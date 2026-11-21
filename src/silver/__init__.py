"""Tahap Silver: penyeragaman data mentah BPS."""

from pathlib import Path

import pandas as pd

from src.common.skema import KOLOM, periksa_silver
from src.common.manifest import baca


SATUAN = {
    "var2011": "Persen",
    "var1254": "Persen",
    "var2016": "Persen",
}


def jalankan(mentah):
    """Transformasi tiga seri BPS menjadi tabel Silver."""
    hasil = []

    for seri, df in mentah.items():
        data = pd.DataFrame({
            "sumber": "BPS",
            "seri_kode": seri,
            "wilayah_kode": pd.to_numeric(
                df["wilayah_id"], errors="raise"
            ).astype("int64"),
            "nama_wilayah": df["wilayah"].astype("string"),
            "periode": pd.to_numeric(
                df["tahun"], errors="raise"
            ).astype("int64").astype("string"),
            "jenis_periode": "tahun",
            "rincian": df["turvar"].astype("string"),
            "nilai": pd.to_numeric(df["nilai"], errors="raise"),
            "satuan": SATUAN[seri],
            "_berkas_raw": df["_berkas_raw"],
            "_sha256_raw": df["_sha256_raw"],
        })

        hasil.append(data[KOLOM])

    silver = pd.concat(hasil, ignore_index=True)

    salah = periksa_silver(silver, baca())
    if salah:
        raise ValueError(
            "Silver gagal diperiksa:\n- " + "\n- ".join(salah)
        )

    folder = Path("data/silver")
    folder.mkdir(parents=True, exist_ok=True)

    silver.to_parquet(folder / "silver.parquet", index=False)

    print(f"Silver selesai: {len(silver):,} baris")
    print(f"Jumlah seri: {silver['seri_kode'].nunique()}")
    print(f"Jumlah wilayah: {silver['wilayah_kode'].nunique()}")
    print(f"File: {folder / 'silver.parquet'}")

    return silver
