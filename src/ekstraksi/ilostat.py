"""Pembaca data mentah ILOSTAT SDMX untuk Kasus 16.

Membaca 3 CSV, 3 DSD JSON, dan 1 dataflow JSON.
Tidak melakukan pembersihan data.
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


def lineage_json(jalur):
    """Mencatat asal dan checksum berkas JSON."""
    berkas_raw = jalur.relative_to(RAW).as_posix()

    return {
        "_berkas_raw": berkas_raw,
        "_sha256_raw": sha256_raw(berkas_raw),
    }


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
        "lineage": lineage_json(jalur),
    }


def baca_dataflow():
    """Membaca metadata dataflow untuk ketiga seri ILOSTAT."""
    jalur = cari_berkas(
        "dataflow.json", Path("ilostat")
    )

    data = baca_json(jalur)
    daftar = data["data"]["dataflows"]
    asal = lineage_json(jalur)

    hasil = {}

    for kode in SERI:
        id_dataflow = f"DF_{kode}"

        cocok = [
            item for item in daftar
            if item.get("id") == id_dataflow
        ]

        if len(cocok) != 1:
            raise ValueError(
                f"Diharapkan 1 dataflow {id_dataflow}, "
                f"ditemukan {len(cocok)}."
            )

        hasil[kode] = {
            "metadata": cocok[0],
            "lineage": asal,
        }

    print(
        f"{asal['_berkas_raw']}: "
        f"{len(daftar)} dataflow | "
        f"{len(hasil)} metadata seri ditemukan"
    )

    return hasil


def baca_seri(kode, dataflow):
    """Membaca satu seri CSV beserta DSD dan lineage."""
    nama_csv = f"DF_{kode}.csv"

    jalur_csv = cari_berkas(
        nama_csv, Path("ilostat")
    )

    jalur_dsd = cari_berkas(
        f"{kode}.json", Path("ilostat")
    )

    dsd = informasi_dsd(jalur_dsd)

    df = pd.read_csv(
        jalur_csv,
        dtype={"TIME_PERIOD": "string", "OBS_STATUS": "string"},
    )

    kurang = [
        kolom for kolom in dsd["dimensi"]
        if kolom not in df.columns
    ]

    if kurang:
        raise ValueError(
            f"{kode}: dimensi DSD tidak ditemukan di CSV: {kurang}"
        )

    berkas_raw = jalur_csv.relative_to(RAW).as_posix()

    df["_berkas_raw"] = berkas_raw
    df["_sha256_raw"] = sha256_raw(berkas_raw)

    df.attrs["ilostat_dsd"] = dsd
    df.attrs["ilostat_dataflow"] = dataflow[kode]

    print(
        f"{berkas_raw}: {len(df):,} baris | "
        f"dimensi: {', '.join(dsd['dimensi'])}"
    )

    return df


def jalankan():
    """Membaca seluruh seri ILOSTAT sebagai DataFrame terpisah."""
    dataflow = baca_dataflow()
    hasil = {}

    for kode in SERI:
        df = baca_seri(kode, dataflow)
        nama_sumber = f"ilostat_{kode}"
        hasil[nama_sumber] = df

    print("\nRingkasan ekstraksi ILOSTAT:")

    for nama, df in hasil.items():
        print(f"{nama}: {len(df)} baris")

    print(f"Total: {sum(len(df) for df in hasil.values())} baris")

    return hasil
