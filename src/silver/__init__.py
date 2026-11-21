"""Tahap 2–4 — Profil, pembersihan, dan penyeragaman ke Silver (pertemuan II–VII). Milik tim.

Keluaran: data/silver/silver.parquet dengan skema minimal di src/common/skema.py.
Satu baris = satu seri x wilayah x periode x rincian x berkas sumber. Nilai dari sumber berbeda
TIDAK digabung di sini. Setiap keputusan pembersihan dicatat di log-keputusan.csv.
"""
import json
from pathlib import Path

from . import pembersihan, profil, transformasi

AKAR = Path(__file__).resolve().parents[2]
INTERIM = AKAR / "data" / "interim"
REPORTS = AKAR / "reports"


def jalankan(mentah):
    """Terima keluaran tahap 1, tulis dan kembalikan DataFrame Silver."""
    df = transformasi.ke_silver(mentah)
    df = profil.tandai_outlier(df)
    df = pembersihan.tandai_patahan(df)

    grid, ringkas = pembersihan.grid_bps(df)
    duplikat = pembersihan.cek_duplikat(df)

    profil.tulis_laporan(df, REPORTS)
    pembersihan.tulis_laporan(df, grid, ringkas, duplikat, REPORTS)
    transformasi.tulis_silver(df)

    metrik = {
        "baris_silver": int(len(df)),
        "sel_kosong_grid": int(sum(v["sel_kosong"] for v in ringkas.values())),
        "sel_kosong_grid_per_seri": {k: v["sel_kosong"] for k, v in ringkas.items()},
        "sel_grid_per_seri": {k: v["sel_grid"] for k, v in ringkas.items()},
        "duplikat_kunci": duplikat["jumlah_baris_kembar"],
        "outlier_z": int(df["outlier_z"].sum()),
        "outlier_iqr": int(df["outlier_iqr"].sum()),
        "outlier_ditandai": int((df["outlier_z"] | df["outlier_iqr"]).sum()),
        "patahan_definisi": int(df["patahan_definisi"].sum()),
        "patahan_kandidat": int(df["patahan_kandidat"].sum()),
        "nilai_min": float(df["nilai"].min()),
        "nilai_max": float(df["nilai"].max()),
        "seri": sorted(df["seri_kode"].unique().tolist()),
        "satuan": {k: sorted(v.tolist()) for k, v in df.groupby("seri_kode")["satuan"].unique().items()},
        "rincian": {k: sorted(v.tolist()) for k, v in df.groupby("seri_kode")["rincian"].unique().items()},
    }
    INTERIM.mkdir(parents=True, exist_ok=True)
    (INTERIM / "silver_metrik.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    print(
        f"silver: {len(df)} baris, {df['seri_kode'].nunique()} seri, "
        f"{df['wilayah_kode'].nunique()} wilayah, grid kosong {metrik['sel_kosong_grid']}"
    )
    return df
