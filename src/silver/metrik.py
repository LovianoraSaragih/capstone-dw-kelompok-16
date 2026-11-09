"""Hitung results/<nim>/metrics.json dari artefak pipeline yang sudah dihasilkan."""
import json
import sys
from pathlib import Path

import pandas as pd

from src.common.hasil import tulis_hasil

AKAR = Path(__file__).resolve().parents[2]
SILVER = AKAR / "data" / "silver" / "silver.parquet"
INTERIM = AKAR / "data" / "interim"


def _baca(nama):
    jalur = INTERIM / nama
    if not jalur.exists():
        return {}
    return json.loads(jalur.read_text(encoding="utf-8"))


def hitung():
    df = pd.read_parquet(SILVER)
    ekstraksi = _baca("ekstraksi_metrik.json")
    silver = _baca("silver_metrik.json")
    validasi = _baca("validasi_metrik.json")
    kosong = silver.get("sel_kosong_grid_per_seri", {})
    metrik = {
        "berkas_dibaca": int(df["_berkas_raw"].nunique()),
        "baris_mentah": int(ekstraksi.get("baris_mentah", 0)),
        "format": int(ekstraksi.get("format", 0)),
        "baris_silver": int(len(df)),
        "sel_kosong_grid": int(silver.get("sel_kosong_grid", 0)),
        "outlier_ditandai": int(silver.get("outlier_ditandai", 0)),
        "patahan_ditandai": int(silver.get("patahan_definisi", 0)),
        "aturan_validasi": int(validasi.get("aturan_validasi", 0)),
        "aturan_lolos": int(validasi.get("aturan_lolos", 0)),
        "kolom_terdokumentasi": int(validasi.get("kolom_terdokumentasi", 0)),
        "outlier_z": int(silver.get("outlier_z", 0)),
        "outlier_iqr": int(silver.get("outlier_iqr", 0)),
        "patahan_kandidat": int(silver.get("patahan_kandidat", 0)),
        "duplikat_kunci": int(silver.get("duplikat_kunci", 0)),
        "sel_kosong_grid_var2011": int(kosong.get("var2011", 0)),
        "sel_kosong_grid_var2016": int(kosong.get("var2016", 0)),
        "sel_kosong_grid_var1254": int(kosong.get("var1254", 0)),
    }
    return metrik


def main():
    nim = sys.argv[1] if len(sys.argv) > 1 else "124450115"
    metrik = hitung()
    tujuan = tulis_hasil(nim, metrik, seed=0)
    teks = tujuan.read_text(encoding="utf-8")
    tujuan.write_text(teks, encoding="utf-8", newline="\n")
    print(tujuan)
    print(json.dumps(metrik, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
