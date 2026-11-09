"""Tahap 4–6 — Reshape, integrasi, dan penyimpanan ke Gold (pertemuan VII, IX, XI, XII). Milik tim.

Keluaran Sprint 1: panel provinsi x tahun x indikator dari seri BPS. Integrasi pembanding
nasional dan basis data SQL dikerjakan pada Sprint 2.
"""
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parents[2]
GOLD = AKAR / "data" / "gold"


def _rata(kolom):
    if isinstance(kolom, tuple):
        return "_".join(str(x) for x in kolom if str(x) != "")
    return str(kolom)


def jalankan(silver):
    """Terima Silver, tulis tabel Gold, kembalikan {nama_tabel: DataFrame}."""
    bps = silver[silver["sumber"] == "bps"].copy()

    panel = (
        bps.pivot_table(
            index=["wilayah_kode", "nama_wilayah", "periode"],
            columns=["seri_kode", "rincian"],
            values="nilai",
            aggfunc="mean",
        )
        .reset_index()
    )
    panel.columns = [_rata(c) for c in panel.columns]
    panel = panel.sort_values(["wilayah_kode", "periode"]).reset_index(drop=True)

    panjang = bps[[
        "sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode",
        "jenis_periode", "rincian", "nilai", "satuan", "_berkas_raw", "_sha256_raw",
    ]].sort_values(["seri_kode", "wilayah_kode", "periode", "rincian"]).reset_index(drop=True)

    GOLD.mkdir(parents=True, exist_ok=True)
    panel.to_parquet(GOLD / "panel_provinsi.parquet", index=False, engine="pyarrow")
    panjang.to_parquet(GOLD / "panel_provinsi_long.parquet", index=False, engine="pyarrow")

    print(f"gold: panel {len(panel)} baris, panel panjang {len(panjang)} baris")
    return {"panel_provinsi": panel, "panel_provinsi_long": panjang}
