"""Penulis docs/data-dictionary.md dari isi Silver dan Gold yang nyata."""
from pathlib import Path

import pandas as pd

DESKRIPSI_KOLOM = {
    "sumber": ("string", "—", "tidak", "bps, ilostat, wdi", "folder data/raw", "nama sumber"),
    "seri_kode": ("string", "—", "tidak", "var2011, var2016, var1254, SDG_*, SI.*", "metadata sumber", "kode seri"),
    "wilayah_kode": ("int", "kode BPS x 100", "tidak", "9999 atau 1100–9700", "vervar BPS / nasional", "9999 = Indonesia"),
    "nama_wilayah": ("string", "—", "tidak", "label sumber", "vervar BPS / country WDI", "mengikuti kapitalisasi sumber"),
    "periode": ("string", "tahun", "tidak", "YYYY", "tahun BPS / TIME_PERIOD / date", "format baku"),
    "jenis_periode": ("string", "—", "tidak", "tahun", "metadata sumber", "semua seri tahunan"),
    "rincian": ("string", "—", "tidak", "total, air_minum, sanitasi, mobilitas, fasilitas_kesehatan, kode dimensi ILOSTAT", "turvar BPS / DSD ILOSTAT", "lihat tabel pemetaan"),
    "nilai": ("float", "persen", "tidak", "0–100", "datacontent / OBS_VALUE / value", "proporsi"),
    "satuan": ("string", "—", "tidak", "persen", "metadata + keputusan log", "lihat K-004"),
    "_berkas_raw": ("string", "path relatif", "tidak", "data/raw/...", "sumber baris", "lineage"),
    "_sha256_raw": ("string", "sha256", "tidak", "64 hex", "src.common.manifest", "lineage"),
    "obs_status": ("string", "—", "ya", "A, R, M, kosong", "OBS_STATUS ILOSTAT", "catatan status observasi"),
    "note_indicator": ("string", "—", "ya", "teks", "note BPS / NOTE_INDICATOR", "catatan sumber"),
    "outlier_z": ("bool", "—", "tidak", "True/False", "src/silver/profil.py", "z-score > 3; tidak dihapus"),
    "outlier_iqr": ("bool", "—", "tidak", "True/False", "src/silver/profil.py", "di luar 1.5 IQR; tidak dihapus"),
    "patahan_definisi": ("bool", "—", "tidak", "True/False", "src/silver/pembersihan.py", "hanya jika catatan metadata menyebut patahan"),
    "patahan_kandidat": ("bool", "—", "tidak", "True/False", "src/silver/pembersihan.py", "heuristik median perubahan >= 5 poin"),
}

RINCIAN_BPS = [
    ("total", "Tidak ada / 0", "var2011, var1254"),
    ("air_minum", "Akses pada layanan air minum (1683)", "var2016"),
    ("sanitasi", "Akses pada layanan sanitasi dasar (1684)", "var2016"),
    ("mobilitas", "Akses pada mobilitas dasar (1685)", "var2016; tidak ada observasi"),
    ("fasilitas_kesehatan", "Akses pada fasilitas kesehatan dasar (1686)", "var2016"),
]


def _tabel_kolom(silver):
    baris = [
        "| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal | Keterangan |",
        "|---|---|---|---|---|---|---|",
    ]
    for kol in silver.columns:
        tipe, satuan, kosong, rentang, asal, ket = DESKRIPSI_KOLOM.get(
            kol, (str(silver[kol].dtype), "—", "—", "—", "—", "—")
        )
        baris.append(f"| {kol} | {tipe} | {satuan} | {kosong} | {rentang} | {asal} | {ket} |")
    return baris


def _tabel_seri(silver):
    baris = [
        "| Sumber | Seri | Baris | Wilayah | Periode | Rentang nilai | Satuan | Rincian | Outlier | Patahan |",
        "|---|---|---:|---:|---|---|---|---|---:|---:|",
    ]
    for (sumber, seri), sub in silver.groupby(["sumber", "seri_kode"], sort=True):
        rincian = ", ".join(sorted(sub["rincian"].unique()))
        baris.append(
            f"| {sumber} | {seri} | {len(sub)} | {sub['wilayah_kode'].nunique()} | "
            f"{sub['periode'].min()}–{sub['periode'].max()} | "
            f"{float(sub['nilai'].min()):.4g}–{float(sub['nilai'].max()):.4g} | "
            f"{', '.join(sorted(sub['satuan'].unique()))} | {rincian} | "
            f"{int((sub['outlier_z'] | sub['outlier_iqr']).sum())} | "
            f"{int(sub['patahan_definisi'].sum())} |"
        )
    return baris


def _tabel_gold(gold):
    baris = [
        "| Tabel | Baris | Kolom |",
        "|---|---:|---:|",
    ]
    for nama, tabel in gold.items():
        baris.append(f"| data/gold/{nama}.parquet | {len(tabel)} | {len(tabel.columns)} |")
    return baris


def tulis(silver, gold, jalur):
    jalur = Path(jalur)
    jalur.parent.mkdir(parents=True, exist_ok=True)
    baris = [
        "# Data dictionary — Kelompok 16, kasus 16",
        "",
        "Dihasilkan oleh `src/validasi/dokumentasi.py` dari isi `data/silver/silver.parquet` dan",
        "`data/gold/*.parquet` pada setiap `python pipeline.py`.",
        "",
        "## data/silver/silver.parquet",
        "",
        *_tabel_kolom(silver),
        "",
        "## Seri di Silver",
        "",
        *_tabel_seri(silver),
        "",
        "## Pemetaan rincian BPS",
        "",
        "| Rincian Silver | Label/code asal | Seri |",
        "|---|---|---|",
    ]
    for rincian, asal, seri in RINCIAN_BPS:
        baris.append(f"| {rincian} | {asal} | {seri} |")
    baris += [
        "",
        "Rincian ILOSTAT memakai kode dimensi asli dari DSD, mis. `SEX=SEX_T;AGE=AGE_YTHADULT_YGE15`,",
        "karena snapshot DSD tidak memuat codelist/label kode.",
        "",
        "## data/gold/",
        "",
        *_tabel_gold(gold),
        "",
        "Panel Gold Sprint 1 hanya berisi seri BPS provinsi; integrasi pembanding nasional menyusul di Sprint 2.",
    ]
    jalur.write_text("\n".join(baris) + "\n", encoding="utf-8", newline="\n")
    return len(silver.columns)
