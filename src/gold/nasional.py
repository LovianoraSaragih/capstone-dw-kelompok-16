
"""Pembentukan tabel Gold nasional untuk seri utama dan pembanding."""

from pathlib import Path

import pandas as pd


AKAR = Path(__file__).resolve().parents[2]
GOLD = AKAR / "data" / "gold"
OUTPUT = GOLD / "tabel_nasional.parquet"

SERI_NASIONAL = {
    "var2011": "bps",
    "var2016": "bps",
    "var1254": "bps",
    "SDG_0111_SEX_AGE_RT": "ilostat",
    "SDG_0131_SEX_SOC_RT": "ilostat",
    "SDG_1041_NOC_RT": "ilostat",
    "SI.DST.50MD": "wdi",
    "SI.POV.DDAY": "wdi",
}

KUNCI_NASIONAL = [
    "sumber",
    "seri_kode",
    "periode",
    "rincian",
]


def jalankan(silver):
    """Membentuk dan menyimpan tabel observasi nasional."""

    kolom_wajib = {
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
    }

    kurang = kolom_wajib - set(silver.columns)
    if kurang:
        raise ValueError(
            f"Kolom Silver tidak tersedia: {sorted(kurang)}"
        )

    # Mengambil observasi Indonesia untuk delapan seri.
    data = silver.loc[
        silver["seri_kode"].isin(SERI_NASIONAL)
        & (silver["wilayah_kode"] == 9999)
    ].copy()

    # Memastikan semua seri memiliki observasi nasional.
    seri_hilang = set(SERI_NASIONAL) - set(data["seri_kode"].unique())
    if seri_hilang:
        raise ValueError(
            f"Seri nasional tidak ditemukan: {sorted(seri_hilang)}"
        )

    # Memastikan sumber setiap seri sesuai.
    sumber_seharusnya = data["seri_kode"].map(SERI_NASIONAL)
    sumber_salah = data["sumber"] != sumber_seharusnya

    if sumber_salah.any():
        raise ValueError(
            "Terdapat seri dengan sumber yang tidak sesuai."
        )

    # Memastikan tidak ada duplikat kunci observasi.
    duplikat = data.duplicated(KUNCI_NASIONAL)
    if duplikat.any():
        raise ValueError(
            f"Ditemukan {int(duplikat.sum())} duplikat observasi nasional."
        )

    # Memastikan informasi lineage tersedia.
    kolom_lineage = ["_berkas_raw", "_sha256_raw"]
    if data[kolom_lineage].isna().any().any():
        raise ValueError(
            "Terdapat observasi nasional tanpa informasi lineage."
        )

    # Menandai asal setiap angka nasional.
    data["asal_nilai"] = "baris_indonesia"

    # Mempertahankan seluruh rincian observasi.
    data = data.sort_values(
        ["seri_kode", "periode", "rincian"]
    ).reset_index(drop=True)

    GOLD.mkdir(parents=True, exist_ok=True)
    data.to_parquet(OUTPUT, index=False)

    print(f"Gold nasional: {len(data)} observasi")
    print(f"Disimpan: {OUTPUT}")

    return data
