
"""Pembaca data mentah ILOSTAT SDMX untuk Kasus 16.

Membaca CSV, DSD, dan metadata JSON. Tidak melakukan pembersihan data.
"""

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, sha256_raw


SERI = [
    "SDG_0111_SEX_AGE_RT",
    "SDG_0131_SEX_SOC_RT",
    "SDG_1041_NOC_RT",
]


def baca_json(jalur):
    """Membaca berkas JSON mentah."""
    with open(jalur, encoding="utf-8") as f:
        return json.load(f)


def cari_berkas(nama, folder):
    """Mencari satu berkas berdasarkan nama di dalam folder."""
    hasil = list((RAW / folder).rglob(nama))

    if len(hasil) != 1:
        raise FileNotFoundError(
            f"Diharapkan 1 berkas {nama}, ditemukan {len(hasil)}."
        )

    return hasil[0]


def informasi_dsd(jalur):
    """Membaca dimensi dan referensi codelist dari DSD."""
    data = baca_json(jalur)
    struktur = data["data"]["dataStructures"][0]
    komponen = struktur["dataStructureComponents"]

    daftar_dimensi = komponen.get("dimensionList", {})
    dimensi = [
        item["id"]
        for item in daftar_dimensi.get("dimensions", [])
    ]

    waktu = daftar_dimensi.get("timeDimension")
    if isinstance(waktu, dict):
        dimensi.append(waktu["id"])

    atribut = komponen.get("attributeList", {}).get("attributes", [])

    obs_status = next(
        (item for item in atribut if item.get("id") == "OBS_STATUS"),
        None,
    )

    return {
        "nama": struktur.get("name"),
        "dimensi": dimensi,
        "obs_status": obs_status,
    }


def baca_seri(kode):
    """Membaca satu seri CSV beserta DSD dan lineage."""
    nama_csv = f"DF_{kode}.csv"

    jalur_csv = cari_berkas(
        nama_csv, Path("ilostat")
    )

    jalur_dsd = cari_berkas(
        f"{kode}.json", Path("ilostat")
    )

    # Baca metadata DSD dan pastikan dimensi dipahami
    dsd = informasi_dsd(jalur_dsd)

    # Baca CSV tanpa melakukan pembersihan
    df = pd.read_csv(
        jalur_csv,
        dtype={"TIME_PERIOD": "string", "OBS_STATUS": "string"},
    )

    # Pastikan dimensi yang didefinisikan DSD tersedia di CSV
    kurang = [
        kolom for kolom in dsd["dimensi"]
        if kolom not in df.columns
    ]

    if kurang:
        raise ValueError(
            f"{kode}: dimensi DSD tidak ditemukan di CSV: {kurang}"
        )

    # Tambahkan lineage dari MANIFEST.csv
    berkas_raw = jalur_csv.relative_to(RAW).as_posix()

    df["_berkas_raw"] = berkas_raw
    df["_sha256_raw"] = sha256_raw(berkas_raw)

    print(
        f"{berkas_raw}: {len(df):,} baris | "
        f"dimensi: {', '.join(dsd['dimensi'])}"
    )

    return df, dsd


def jalankan():
    """Membaca seluruh seri ILOSTAT sebagai DataFrame terpisah."""
    hasil = {}

    for kode in SERI:
        df, dsd = baca_seri(kode)

        nama_sumber = f"ilostat_{kode}"
        df.attrs["ilostat_dsd"] = dsd

        hasil[nama_sumber] = df

    print("\nRingkasan ekstraksi ILOSTAT:")

    for nama, df in hasil.items():
        print(f"{nama}: {len(df)} baris")

    print(f"Total: {sum(len(df) for df in hasil.values())} baris")

    return hasil