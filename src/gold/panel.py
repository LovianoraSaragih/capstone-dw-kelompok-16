
"""Pembentukan panel Gold provinsi x periode x indikator."""

from pathlib import Path

import pandas as pd

from src.silver.panel import (
    PROVINSI_38,
    KODE_PAPUA_LAMA,
    KODE_TANPA_PADANAN,
)
from src.ekstraksi.bps import domain_bps


AKAR = Path(__file__).resolve().parents[2]
GOLD = AKAR / "data" / "gold"

SERI_UTAMA = ["var2011", "var2016", "var1254"]

# Provinsi yang dapat dibandingkan secara historis.
KODE_PROVINSI_PADANAN = (
    set(PROVINSI_38) - KODE_TANPA_PADANAN
)

KUNCI_PANEL = ["wilayah_kode", "periode", "indikator"]

KOLOM_SUMBER = [
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
]


def _siapkan_identitas(data):
    """Menambahkan nama indikator dan identitas sumber Silver."""

    data = data.copy()

    data["indikator"] = (
        data["seri_kode"].astype(str)
        + "__"
        + data["rincian"].astype(str)
    )

    data["_silver_row_id"] = (
        "silver-"
        + pd.util.hash_pandas_object(
            data[KOLOM_SUMBER],
            index=False,
        ).map(lambda x: f"{x:016x}")
    )

    return data


def _pilih_seri_bps(silver):
    """Memilih sumber BPS untuk tiga seri utama."""

    wajib = set(KOLOM_SUMBER)
    kurang = wajib - set(silver.columns)

    if kurang:
        raise ValueError(
            f"Kolom Silver tidak tersedia: {sorted(kurang)}"
        )

    data = silver[
        (silver["sumber"] == "bps")
        & (silver["seri_kode"].isin(SERI_UTAMA))
    ].copy()

    seri_hilang = set(SERI_UTAMA) - set(data["seri_kode"].unique())

    if seri_hilang:
        raise ValueError(
            f"Seri utama tidak ditemukan: {sorted(seri_hilang)}"
        )

    return data


def siapkan_data(silver):
    """Memilih data provinsi yang memiliki padanan historis."""

    data = _pilih_seri_bps(silver)

    data = data[
        data["wilayah_kode"].isin(KODE_PROVINSI_PADANAN)
    ].copy()

    data = _siapkan_identitas(data)

    # Memastikan satu indikator hanya memiliki satu satuan.
    satuan = data.groupby(
        ["seri_kode", "rincian"]
    )["satuan"].nunique()

    tidak_seragam = satuan[satuan > 1]

    if not tidak_seragam.empty:
        raise ValueError(
            "Ditemukan satuan berbeda dalam indikator:\n"
            f"{tidak_seragam}"
        )

    # Memastikan tidak ada duplikasi kunci panel.
    kembar = data.duplicated(KUNCI_PANEL, keep=False)

    if kembar.any():
        contoh = data.loc[
            kembar,
            KUNCI_PANEL + ["nilai", "satuan", "_berkas_raw"],
        ]

        raise ValueError(
            "Ditemukan duplikasi kunci panel Gold:\n"
            f"{contoh.to_string(index=False)}"
        )

    return data.sort_values(
        KUNCI_PANEL
    ).reset_index(drop=True)


def siapkan_papua_historis(silver):
    """Memisahkan observasi historis Papua Barat dan Papua."""

    data = _pilih_seri_bps(silver)

    data = data[
        data["wilayah_kode"].isin(KODE_PAPUA_LAMA)
    ].copy()

    data = _siapkan_identitas(data)

    return data.sort_values(
        KUNCI_PANEL
    ).reset_index(drop=True)


def bentuk_panel_panjang(data):
    """Panel panjang: satu baris per provinsi x periode x indikator."""

    kolom = KOLOM_SUMBER + [
        "indikator",
        "_silver_row_id",
    ]

    return data[kolom].copy()


def bentuk_panel_lebar(data):
    """Panel lebar dengan 38 provinsi dan kolom setiap indikator."""

    domain = domain_bps()

    semua_indikator = sorted({
        f"{seri}__{rincian}"
        for seri in SERI_UTAMA
        for rincian in domain[seri]["rincian"]
    })

    semua_periode = sorted({
        str(tahun)
        for seri in SERI_UTAMA
        for tahun in domain[seri]["tahun"]
    })

    # Membuat grid lengkap 38 provinsi x seluruh periode.
    wilayah = pd.DataFrame({
        "wilayah_kode": list(PROVINSI_38.keys()),
        "nama_wilayah": list(PROVINSI_38.values()),
    })

    periode = pd.DataFrame({
        "periode": semua_periode,
    })

    grid = wilayah.merge(periode, how="cross")

    # Memberi penanda wilayah yang tidak memiliki padanan historis.
    grid["status_padanan"] = grid["wilayah_kode"].apply(
        lambda kode: (
            "tidak_ada_padanan_historis"
            if kode in KODE_TANPA_PADANAN
            else "dapat_dibandingkan"
        )
    )

    # Membentuk panel lebar dari observasi yang dapat dibandingkan.
    panel = data.pivot(
        index=[
            "wilayah_kode",
            "nama_wilayah",
            "periode",
        ],
        columns="indikator",
        values="nilai",
    ).reset_index()

    panel.columns.name = None

    # Mempertahankan semua kolom indikator dari domain.
    kolom_identitas = [
        "wilayah_kode",
        "nama_wilayah",
        "periode",
    ]

    panel = panel.reindex(
        columns=kolom_identitas + semua_indikator
    )

    # Memastikan seluruh kombinasi provinsi dan periode muncul.
    panel = grid.merge(
        panel,
        on=kolom_identitas,
        how="left",
    )

    return panel.sort_values(
        ["wilayah_kode", "periode"]
    ).reset_index(drop=True)


def laporan_kelengkapan(data):
    """Menghitung kelengkapan berdasarkan provinsi berpadanan."""

    domain = domain_bps()
    baris = []

    for seri in SERI_UTAMA:
        dom = domain[seri]

        wilayah = [
            kode
            for kode in dom["wilayah"]
            if kode in KODE_PROVINSI_PADANAN
        ]

        total_diharapkan = len(wilayah)

        tanpa_padanan = len(
            set(dom["wilayah"]) & KODE_TANPA_PADANAN
        )

        for periode in dom["tahun"]:
            for rincian in dom["rincian"]:

                sub = data[
                    (data["seri_kode"] == seri)
                    & (data["periode"] == periode)
                    & (data["rincian"] == rincian)
                    & (data["wilayah_kode"].isin(wilayah))
                ]

                terisi = int(
                    sub["wilayah_kode"].nunique()
                )

                kosong = total_diharapkan - terisi

                satuan = (
                    sub["satuan"].iloc[0]
                    if not sub.empty
                    else None
                )

                baris.append({
                    "seri_kode": seri,
                    "periode": periode,
                    "rincian": rincian,
                    "satuan": satuan,
                    "provinsi_diharapkan": total_diharapkan,
                    "provinsi_tanpa_padanan_historis": tanpa_padanan,
                    "provinsi_terisi": terisi,
                    "provinsi_kosong": kosong,
                    "baris_gold": len(sub),
                    "persen_lengkap": round(
                        terisi / total_diharapkan * 100,
                        2,
                    ) if total_diharapkan else 0.0,
                })

    return pd.DataFrame(baris)


def jalankan(silver):
    """Membentuk dan menyimpan seluruh keluaran panel Gold."""

    data = siapkan_data(silver)
    papua_historis = siapkan_papua_historis(silver)

    panjang = bentuk_panel_panjang(data)
    lebar = bentuk_panel_lebar(data)
    kelengkapan = laporan_kelengkapan(data)

    # Pemeriksaan keunikan kunci panel.
    if panjang.duplicated(KUNCI_PANEL).any():
        raise ValueError("Kunci panel Gold tidak unik.")

    # Pemeriksaan keterlacakan sumber Silver.
    if panjang["_silver_row_id"].isna().any():
        raise ValueError(
            "Ada baris Gold tanpa identitas sumber Silver."
        )

    if panjang["_silver_row_id"].duplicated().any():
        raise ValueError(
            "Identitas sumber Silver ditemukan lebih dari sekali."
        )

    if papua_historis["_silver_row_id"].duplicated().any():
        raise ValueError(
            "Identitas sumber Papua historis ditemukan lebih dari sekali."
        )

    # Pemeriksaan persentase kelengkapan.
    if (
        (kelengkapan["persen_lengkap"] < 0).any()
        or (kelengkapan["persen_lengkap"] > 100).any()
    ):
        raise ValueError(
            "Persentase kelengkapan berada di luar 0-100."
        )

    GOLD.mkdir(parents=True, exist_ok=True)

    panjang.to_parquet(
        GOLD / "panel_provinsi_long.parquet",
        index=False,
        engine="pyarrow",
    )

    lebar.to_parquet(
        GOLD / "panel_provinsi.parquet",
        index=False,
        engine="pyarrow",
    )

    kelengkapan.to_parquet(
        GOLD / "kelengkapan_panel.parquet",
        index=False,
        engine="pyarrow",
    )

    papua_historis.to_parquet(
        GOLD / "papua_historis.parquet",
        index=False,
        engine="pyarrow",
    )

    print(
        f"gold: {len(panjang)} baris panel panjang, "
        f"{len(lebar)} baris panel lebar, "
        f"{len(kelengkapan)} baris laporan kelengkapan, "
        f"{len(papua_historis)} baris Papua historis"
    )

    return {
        "panel_provinsi": lebar,
        "panel_provinsi_long": panjang,
        "kelengkapan_panel": kelengkapan,
        "papua_historis": papua_historis,
    }