
"""Tahap Gold: pembentukan panel provinsi x periode x indikator."""

from pathlib import Path

import pandas as pd

from src.silver.panel import PROVINSI_38, KODE_TANPA_PADANAN

AKAR = Path(__file__).resolve().parents[2]
GOLD = AKAR / "data" / "gold"

KUNCI_ALAMI = ["seri_kode", "wilayah_kode", "periode", "rincian"]

KOLOM_PENANDA = [
    "outlier_z",
    "outlier_iqr",
    "patahan_definisi",
    "patahan_kandidat",
]


def pilih_observasi(silver):
    """Pilih observasi BPS provinsi tanpa agregasi atau imputasi."""
    bps = silver[silver["sumber"] == "bps"].copy()

    terpilih = bps[
        bps["wilayah_kode"].isin(PROVINSI_38)
        & ~bps["wilayah_kode"].isin(KODE_TANPA_PADANAN)
    ].copy()

    duplikat = terpilih.duplicated(KUNCI_ALAMI, keep=False)
    if duplikat.any():
        raise ValueError(
            "Gold gagal: ditemukan duplikat indikator-wilayah-periode-rincian. "
            "Periksa pemilihan snapshot di tahap Silver."
        )

    for kolom in KOLOM_PENANDA:
        if kolom not in terpilih.columns:
            raise ValueError(f"Kolom penanda {kolom} tidak ditemukan di Silver.")

    return terpilih


def bentuk_panel(terpilih):
    """Bentuk panel lebar 38 provinsi x seluruh tahun yang tersedia."""
    wilayah = sorted(PROVINSI_38)
    periode = sorted(terpilih["periode"].unique())

    indeks = pd.MultiIndex.from_product(
        [wilayah, periode],
        names=["wilayah_kode", "periode"],
    )

    panel = indeks.to_frame(index=False)
    panel["nama_wilayah"] = panel["wilayah_kode"].map(PROVINSI_38)

    kolom_indikator = ["nilai"] + KOLOM_PENANDA

    for kolom in kolom_indikator:
        bagian = terpilih.pivot(
            index=["wilayah_kode", "periode"],
            columns=["seri_kode", "rincian"],
            values=kolom,
        )

        if kolom == "nilai":
            bagian.columns = [
                f"{seri}_{rincian}"
                for seri, rincian in bagian.columns
            ]
        else:
            bagian.columns = [
                f"{seri}_{rincian}_{kolom}"
                for seri, rincian in bagian.columns
            ]

        panel = panel.merge(
            bagian.reset_index(),
            on=["wilayah_kode", "periode"],
            how="left",
        )

    kolom_flag = [
        kolom for kolom in panel.columns
        if any(kolom.endswith(f"_{flag}") for flag in KOLOM_PENANDA)
    ]

    panel[kolom_flag] = panel[kolom_flag].fillna(False).astype(bool)

    return panel.sort_values(
        ["wilayah_kode", "periode"]
    ).reset_index(drop=True)


def jalankan_sprint1(silver):
    """Menjalankan implementasi Gold Sprint 1."""
    terpilih = pilih_observasi(silver)

    panel = bentuk_panel(terpilih)

    kolom_panjang = [
        "sumber",
        "seri_kode",
        "wilayah_kode",
        "nama_wilayah",
        "periode",
        "jenis_periode",
        "rincian",
        "nilai",
        "satuan",
        "_berkas_raw",
        "_sha256_raw",
    ] + KOLOM_PENANDA

    panjang = terpilih[kolom_panjang].copy()
    panjang = panjang.sort_values(
        ["seri_kode", "wilayah_kode", "periode", "rincian"]
    ).reset_index(drop=True)

    GOLD.mkdir(parents=True, exist_ok=True)

    panel.to_parquet(
        GOLD / "panel_provinsi.parquet",
        index=False,
        engine="pyarrow",
    )
    panjang.to_parquet(
        GOLD / "panel_provinsi_long.parquet",
        index=False,
        engine="pyarrow",
    )

    print(
        f"gold: panel {len(panel)} baris, "
        f"panel panjang {len(panjang)} baris"
    )

    return {
        "panel_provinsi": panel,
        "panel_provinsi_long": panjang,
    }


# Implementasi Gold Sprint 2
from . import nasional, panel


def jalankan(silver):
    """Menjalankan pengolahan Gold dan tabel nasional."""
    hasil = panel.jalankan(silver)
    hasil["tabel_nasional"] = nasional.jalankan(silver)
    return hasil