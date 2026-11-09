"""Penyeragaman keluaran ekstraksi ke skema minimal Silver."""
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parents[2]
SILVER = AKAR / "data" / "silver" / "silver.parquet"

KOLOM = [
    "sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode", "jenis_periode",
    "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw", "obs_status", "note_indicator",
]
WAJIB = KOLOM[:11]


def ke_silver(mentah):
    frames = [mentah["bps"], mentah["ilostat"], mentah["wdi"]]
    df = pd.concat(frames, ignore_index=True)

    for kol in ["obs_status", "note_indicator"]:
        df[kol] = df[kol].fillna("").astype(str)

    for kol in ["sumber", "seri_kode", "nama_wilayah", "periode", "jenis_periode",
                "rincian", "satuan", "_berkas_raw", "_sha256_raw"]:
        df[kol] = df[kol].astype(str).str.strip()
    df["wilayah_kode"] = df["wilayah_kode"].astype("int64")
    df["nilai"] = df["nilai"].astype("float64")

    df = df[KOLOM].copy()
    kosong = {k: int(df[k].isna().sum()) for k in WAJIB if df[k].isna().any()}
    if kosong:
        raise ValueError(f"kolom wajib masih kosong: {kosong}")

    df = df.sort_values(
        ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]
    ).reset_index(drop=True)
    return df


def tulis_silver(df, jalur=SILVER):
    jalur = Path(jalur)
    jalur.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(jalur, index=False, engine="pyarrow")
    return jalur
