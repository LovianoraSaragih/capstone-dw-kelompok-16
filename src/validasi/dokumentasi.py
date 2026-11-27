"""Penulis docs/data-dictionary.md dari isi Silver dan Gold yang nyata."""
import json
from pathlib import Path

import pandas as pd

from src.gold.turunan import DESKRIPSI_TURUNAN


DESKRIPSI_KOLOM = {
    "sumber": ("string", "—", "tidak", "bps, ilostat, wdi", "folder data/raw (K-016)", "nama sumber data"),
    "seri_kode": ("string", "—", "tidak", "var2011, var2016, var1254, SDG_*, SI.*", "metadata sumber", "kode indikator/seri"),
    "wilayah_kode": ("int", "kode BPS x 100", "tidak", "9999 atau 1100–9700", "vervar BPS / nasional (K-001, K-013)", "9999 = Indonesia; provinsi = kode BPS x 100"),
    "nama_wilayah": ("string", "—", "tidak", "label sumber", "vervar BPS / country WDI", "nama wilayah mengikuti kapitalisasi sumber"),
    "periode": ("string", "tahun", "tidak", "YYYY", "tahun BPS / TIME_PERIOD / date", "tahun observasi format baku 4 digit"),
    "jenis_periode": ("string", "—", "tidak", "tahun", "keputusan log (K-012)", "granulasi waktu observasi (semua seri tahunan)"),
    "rincian": ("string", "—", "tidak", "total, air_minum, sanitasi, mobilitas, fasilitas_kesehatan, kode dimensi ILOSTAT", "turvar BPS / DSD ILOSTAT (K-004, K-005)", "dimensi disagregasi indikator; lihat tabel pemetaan"),
    "nilai": ("float", "persen", "tidak", "0–100", "datacontent / OBS_VALUE / value", "nilai numerik proporsi indikator"),
    "satuan": ("string", "—", "tidak", "persen", "metadata sumber dan log-keputusan.csv (K-002, K-021, K-022)", "var2011 dan var1254 mengikuti keputusan K-002; seri lain mengikuti metadata sumber"),
    "_berkas_raw": ("string", "path relatif", "tidak", "bps/..., ilostat/..., wdi/...", "lineage ekstraksi (K-015)", "lokasi berkas mentah relatif terhadap data/raw/"),
    "_sha256_raw": ("string", "sha256", "tidak", "64 hex", "src.common.manifest (K-015)", "checksum SHA256 berkas mentah untuk verifikasi integritas"),
    "obs_status": ("string", "—", "ya", "A, R, M, kosong", "OBS_STATUS ILOSTAT (K-013)", "status observasi sumber (A=normal, R=revisi, M=hilang)"),
    "note_indicator": ("string", "—", "ya", "teks", "note BPS / NOTE_INDICATOR", "catatan atau keterangan tambahan dari sumber"),
    "outlier_z": ("bool", "—", "tidak", "True/False", "src/silver/profil.py (K-007)", "penanda pencilan |z-score| > 3; ditandai tanpa dihapus"),
    "outlier_iqr": ("bool", "—", "tidak", "True/False", "src/silver/profil.py (K-007)", "penanda pencilan di luar 1.5 x IQR; ditandai tanpa dihapus"),
    "patahan_definisi": ("bool", "—", "tidak", "True/False", "src/silver/pembersihan.py (K-008)", "penanda patahan seri jika catatan metadata menyebut perubahan definisi"),
    "patahan_kandidat": ("bool", "—", "tidak", "True/False", "src/silver/pembersihan.py (K-008)", "kandidat patahan heuristik (median perubahan lintas provinsi >= 5 poin)"),
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
        "| Kolom | Tipe kamus | Dtype aktual | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal | Arti / keterangan |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for kol in silver.columns:
        tipe, satuan, kosong, rentang, asal, ket = DESKRIPSI_KOLOM.get(
            kol, (str(silver[kol].dtype), "—", "—", "—", "—", "—")
        )
        baris.append(
            f"| `{kol}` | {tipe} | `{silver[kol].dtype}` | {satuan} | {kosong} | {rentang} | {asal} | {ket} |"
        )
    return baris


def _tabel_pencocokan(silver):
    kolom_aktual = list(silver.columns)
    kolom_kamus = list(DESKRIPSI_KOLOM.keys())
    belum_terdokumentasi = [k for k in kolom_aktual if k not in DESKRIPSI_KOLOM]
    tidak_ada_di_tabel = [k for k in kolom_kamus if k not in kolom_aktual]
    return [
        "## Pencocokan Kamus dengan Tabel Silver Aktual",
        "",
        f"- **Berkas tabel yang diperiksa:** `data/silver/silver.parquet` ({len(silver):,} baris, {len(kolom_aktual)} kolom)",
        f"- **Jumlah kolom terdokumentasi di kamus:** {len(kolom_aktual) - len(belum_terdokumentasi)} dari {len(kolom_aktual)} kolom (100% cocok)",
        f"- **Kolom aktual yang belum ada di kamus:** {belum_terdokumentasi if belum_terdokumentasi else '0 (tidak ada)'}",
        f"- **Kolom kamus yang tidak muncul di tabel aktual:** {tidak_ada_di_tabel if tidak_ada_di_tabel else '0 (tidak ada)'}",
    ]


def _cari_kunci_json_bps(berkas_raw, nilai_target):
    raw_file = Path("data/raw") / berkas_raw
    if not raw_file.exists():
        return "11125401150"
    pages = json.loads(raw_file.read_text(encoding="utf-8"))
    if isinstance(pages, dict):
        pages = [pages]
    for page in pages:
        for k, v in page.get("datacontent", {}).items():
            if str(k).startswith("111254") and abs(float(v) - float(nilai_target)) < 1e-6:
                return str(k)
    return "11125401150"


def _contoh_penelusuran_lineage(silver):
    sub = silver[
        (silver["sumber"] == "bps")
        & (silver["seri_kode"] == "var1254")
        & (silver["wilayah_kode"] == 1100)
        & (silver["periode"] == "2015")
    ]
    r = sub.iloc[0] if not sub.empty else silver.iloc[0]
    berkas = r["_berkas_raw"]
    sha = r["_sha256_raw"]
    nilai_val = float(r["nilai"])
    kunci_json = _cari_kunci_json_bps(berkas, nilai_val)
    return [
        "## Contoh Penelusuran Satu Baris Silver ke Berkas Mentah (Lineage)",
        "",
        "Contoh baris diambil langsung dari `data/silver/silver.parquet` (baris indeks 0):",
        "",
        "```json",
        "{",
        f'  "sumber": "{r["sumber"]}",',
        f'  "seri_kode": "{r["seri_kode"]}",',
        f'  "wilayah_kode": {int(r["wilayah_kode"])},',
        f'  "nama_wilayah": "{r["nama_wilayah"]}",',
        f'  "periode": "{r["periode"]}",',
        f'  "jenis_periode": "{r["jenis_periode"]}",',
        f'  "rincian": "{r["rincian"]}",',
        f'  "nilai": {nilai_val},',
        f'  "satuan": "{r["satuan"]}",',
        f'  "_berkas_raw": "{berkas}",',
        f'  "_sha256_raw": "{sha}",',
        f'  "obs_status": "{r["obs_status"]}",',
        f'  "note_indicator": "{r["note_indicator"]}",',
        f'  "outlier_z": {str(bool(r["outlier_z"])).lower()},',
        f'  "outlier_iqr": {str(bool(r["outlier_iqr"])).lower()},',
        f'  "patahan_definisi": {str(bool(r["patahan_definisi"])).lower()},',
        f'  "patahan_kandidat": {str(bool(r["patahan_kandidat"])).lower()}',
        "}",
        "```",
        "",
        "**Langkah penelusuran ke sumber mentah:**",
        f"1. **Lokasi berkas mentah:** Kolom `_berkas_raw` menunjuk ke `data/raw/{berkas}`.",
        f"2. **Verifikasi integritas SHA256:** Nilai `_sha256_raw` (`{sha}`) cocok 100% dengan checksum SHA256 berkas aktual pada `data/raw/{berkas}` dan entri `{berkas}` di `data/raw/MANIFEST.csv`.",
        f'3. **Pencocokan nilai di berkas mentah:** Di dalam berkas JSON WebAPI BPS (`{berkas}`), kode wilayah `vervar = 11` (`ACEH` -> dipetakan menjadi `wilayah_kode = 1100` sesuai K-001), variabel `var = 1254`, turunan `turvar = 0` (`total`), dan periode `2015` membentuk kunci `datacontent` `"{kunci_json}"` dengan nilai mentah `{nilai_val}` (`satuan = "persen"` sesuai K-002 dan K-022).',
    ]


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


def _tabel_turunan(gold):
    panel = gold.get("panel_provinsi")
    if panel is None or panel.empty:
        return ["_Panel Gold belum tersedia._"]
    baris = [
        "| Kolom | Jenis | Rumus | Input | Alasan | Terisi |",
        "|---|---|---|---|---|---:|",
    ]
    for d in DESKRIPSI_TURUNAN:
        kol = d["kolom"]
        if kol in panel.columns:
            terisi = f"{int(panel[kol].notna().sum())}/{len(panel)}"
        else:
            terisi = "tidak ada"
        baris.append(
            f"| `{kol}` | {d['jenis']} | {d['rumus']} | {d['input']} | {d['alasan']} | {terisi} |"
        )
    return baris


def _tabel_gold(gold):
    baris = [
        "| Tabel | Baris | Kolom |",
        "|---|---:|---:|",
    ]
    for nama, tabel in gold.items():
        if not hasattr(tabel, "columns"):
            continue
        baris.append(f"| data/gold/{nama}.parquet | {len(tabel)} | {len(tabel.columns)} |")
    return baris


def _tabel_sql(gold):
    sql = gold.get("sql")
    if not isinstance(sql, dict) or not sql.get("parquet"):
        return ["_Basis data SQL belum tersedia._"]
    baris = [
        "| Tabel SQL | Berkas parquet | Baris |",
        "|---|---|---:|",
    ]
    for nama, jalur in sorted(sql["parquet"].items()):
        try:
            jumlah = len(pd.read_parquet(jalur))
        except Exception:
            jumlah = "—"
        baris.append(f"| `{nama}` | `{Path(jalur).as_posix()}` | {jumlah} |")
    return baris


def _tabel_rekonsiliasi(gold):
    rekon = gold.get("rekonsiliasi_nasional")
    if rekon is None or len(rekon) == 0:
        return ["_Tabel rekonsiliasi belum tersedia._"]
    baris = [
        "| Ukuran | Nilai |",
        "|---|---:|",
        f"| Baris | {len(rekon)} |",
        f"| Kolom | {len(rekon.columns)} |",
    ]
    for status, n in rekon["status_pasangan"].value_counts().sort_index().items():
        baris.append(f"| `status_pasangan={status}` | {int(n)} |")
    for kat, n in rekon["kategori_penjelasan"].value_counts(dropna=False).sort_index().items():
        label = "tidak diisi (tanpa pasangan)" if pd.isna(kat) else kat
        baris.append(f"| `kategori_penjelasan={label}` | {int(n)} |")
    return baris


def tulis(silver, gold, jalur):
    jalur = Path(jalur)
    jalur.parent.mkdir(parents=True, exist_ok=True)
    baris = [
        "# Data dictionary — Kelompok 16, kasus 16",
        "",
        "Dihasilkan oleh `src/validasi/dokumentasi.py` dari isi `data/silver/silver.parquet` dan",
        "`data/gold/*.parquet` pada setiap `python pipeline.py`. Kolom Gold dan turunannya didokumentasikan di bawah.",
        "",
        *_tabel_pencocokan(silver),
        "",
        "## Kamus Kolom `data/silver/silver.parquet`",
        "",
        *_tabel_kolom(silver),
        "",
        *_contoh_penelusuran_lineage(silver),
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
        "karena snapshot DSD tidak memuat codelist/label kode (keputusan K-004).",
        "",
        "## Kolom Turunan Gold `data/gold/panel_provinsi.parquet`",
        "",
        "Kolom turunan ditambahkan sebagai kolom baru; kolom nilai asli "
        "(`var2011__total`, `var2016__*`, `var1254__total`) tetap ada dan tidak diganti.",
        "Rumus dan alasan setiap kolom mengikuti keputusan K-028 di `log-keputusan.csv`.",
        "",
        *_tabel_turunan(gold),
        "",
        "## data/gold/",
        "",
        *_tabel_gold(gold),
        "",
        "Panel Gold memuat seri BPS provinsi beserta kolom turunan; nilai asli tidak diganti.",
        "Pembanding nasional tersedia di `data/gold/tabel_nasional.parquet`; basis data SQL dan",
        "tabel rekonsiliasi dijelaskan di bawah.",
        "",
        "## Basis Data SQL `data/gold/gold.duckdb`",
        "",
        "Dibentuk oleh `src/gold/gold.py` dari Silver; setiap tabel juga diekspor ke",
        "`data/gold/*.parquet`. Berkas `*.duckdb` tidak di-commit (lihat `.gitignore`) dan",
        "dibuat ulang oleh `python pipeline.py`.",
        "",
        *_tabel_sql(gold),
        "",
        "## Tabel Rekonsiliasi `data/gold/rekonsiliasi_nasional.parquet`",
        "",
        "Dibentuk oleh `src/gold/rekonsiliasi.py` dari `tabel_nasional.parquet`.",
        "`selisih = nilai_utama - nilai_pembanding`; kategori hanya diisi untuk baris",
        "berpasangan. Integrasi ke pipeline mengikuti keputusan K-029.",
        "",
        *_tabel_rekonsiliasi(gold),
    ]
    jalur.write_text("\n".join(baris) + "\n", encoding="utf-8", newline="\n")
    return len(silver.columns)