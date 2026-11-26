# Data dictionary — Kelompok 16, kasus 16

Dihasilkan oleh `src/validasi/dokumentasi.py` dari isi `data/silver/silver.parquet` dan
`data/gold/*.parquet` pada setiap `python pipeline.py`. Kolom Gold akan dilengkapi pada Sprint 2–3.

## Pencocokan Kamus dengan Tabel Silver Aktual

- **Berkas tabel yang diperiksa:** `data/silver/silver.parquet` (1,137 baris, 17 kolom)
- **Jumlah kolom terdokumentasi di kamus:** 17 dari 17 kolom (100% cocok)
- **Kolom aktual yang belum ada di kamus:** 0 (tidak ada)
- **Kolom kamus yang tidak muncul di tabel aktual:** 0 (tidak ada)

## Kamus Kolom `data/silver/silver.parquet`

| Kolom | Tipe kamus | Dtype aktual | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal | Arti / keterangan |
|---|---|---|---|---|---|---|---|
| `sumber` | string | `str` | — | tidak | bps, ilostat, wdi | folder data/raw (K-016) | nama sumber data |
| `seri_kode` | string | `str` | — | tidak | var2011, var2016, var1254, SDG_*, SI.* | metadata sumber | kode indikator/seri |
| `wilayah_kode` | int | `int64` | kode BPS x 100 | tidak | 9999 atau 1100–9700 | vervar BPS / nasional (K-001, K-013) | 9999 = Indonesia; provinsi = kode BPS x 100 |
| `nama_wilayah` | string | `str` | — | tidak | label sumber | vervar BPS / country WDI | nama wilayah mengikuti kapitalisasi sumber |
| `periode` | string | `str` | tahun | tidak | YYYY | tahun BPS / TIME_PERIOD / date | tahun observasi format baku 4 digit |
| `jenis_periode` | string | `str` | — | tidak | tahun | keputusan log (K-012) | granulasi waktu observasi (semua seri tahunan) |
| `rincian` | string | `str` | — | tidak | total, air_minum, sanitasi, mobilitas, fasilitas_kesehatan, kode dimensi ILOSTAT | turvar BPS / DSD ILOSTAT (K-004, K-005) | dimensi disagregasi indikator; lihat tabel pemetaan |
| `nilai` | float | `float64` | persen | tidak | 0–100 | datacontent / OBS_VALUE / value | nilai numerik proporsi indikator |
| `satuan` | string | `str` | — | tidak | persen | metadata sumber dan log-keputusan.csv (K-002, K-021, K-022) | var2011 dan var1254 mengikuti keputusan K-002; seri lain mengikuti metadata sumber |
| `_berkas_raw` | string | `str` | path relatif | tidak | bps/..., ilostat/..., wdi/... | lineage ekstraksi (K-015) | lokasi berkas mentah relatif terhadap data/raw/ |
| `_sha256_raw` | string | `str` | sha256 | tidak | 64 hex | src.common.manifest (K-015) | checksum SHA256 berkas mentah untuk verifikasi integritas |
| `obs_status` | string | `str` | — | ya | A, R, M, kosong | OBS_STATUS ILOSTAT (K-013) | status observasi sumber (A=normal, R=revisi, M=hilang) |
| `note_indicator` | string | `str` | — | ya | teks | note BPS / NOTE_INDICATOR | catatan atau keterangan tambahan dari sumber |
| `outlier_z` | bool | `bool` | — | tidak | True/False | src/silver/profil.py (K-007) | penanda pencilan |z-score| > 3; ditandai tanpa dihapus |
| `outlier_iqr` | bool | `bool` | — | tidak | True/False | src/silver/profil.py (K-007) | penanda pencilan di luar 1.5 x IQR; ditandai tanpa dihapus |
| `patahan_definisi` | bool | `bool` | — | tidak | True/False | src/silver/pembersihan.py (K-008) | penanda patahan seri jika catatan metadata menyebut perubahan definisi |
| `patahan_kandidat` | bool | `bool` | — | tidak | True/False | src/silver/pembersihan.py (K-008) | kandidat patahan heuristik (median perubahan lintas provinsi >= 5 poin) |

## Contoh Penelusuran Satu Baris Silver ke Berkas Mentah (Lineage)

Contoh baris diambil langsung dari `data/silver/silver.parquet` (baris indeks 0):

```json
{
  "sumber": "bps",
  "seri_kode": "var1254",
  "wilayah_kode": 1100,
  "nama_wilayah": "ACEH",
  "periode": "2015",
  "jenis_periode": "tahun",
  "rincian": "total",
  "nilai": 1.54,
  "satuan": "persen",
  "_berkas_raw": "bps/2026-10-20/json/sdg17_17_1_1_v1254.json",
  "_sha256_raw": "0bdc1b62f4a7ec0d96175254a4a4e0df7421b3ee89e0d08fd29a5b878d67c531",
  "obs_status": "",
  "note_indicator": "Sumber : BPS",
  "outlier_z": false,
  "outlier_iqr": false,
  "patahan_definisi": false,
  "patahan_kandidat": false
}
```

**Langkah penelusuran ke sumber mentah:**
1. **Lokasi berkas mentah:** Kolom `_berkas_raw` menunjuk ke `data/raw/bps/2026-10-20/json/sdg17_17_1_1_v1254.json`.
2. **Verifikasi integritas SHA256:** Nilai `_sha256_raw` (`0bdc1b62f4a7ec0d96175254a4a4e0df7421b3ee89e0d08fd29a5b878d67c531`) cocok 100% dengan checksum SHA256 berkas aktual pada `data/raw/bps/2026-10-20/json/sdg17_17_1_1_v1254.json` dan entri `bps/2026-10-20/json/sdg17_17_1_1_v1254.json` di `data/raw/MANIFEST.csv`.
3. **Pencocokan nilai di berkas mentah:** Di dalam berkas JSON WebAPI BPS (`bps/2026-10-20/json/sdg17_17_1_1_v1254.json`), kode wilayah `vervar = 11` (`ACEH` -> dipetakan menjadi `wilayah_kode = 1100` sesuai K-001), variabel `var = 1254`, turunan `turvar = 0` (`total`), dan periode `2015` membentuk kunci `datacontent` `"11125401150"` dengan nilai mentah `1.54` (`satuan = "persen"` sesuai K-002 dan K-022).

## Seri di Silver

| Sumber | Seri | Baris | Wilayah | Periode | Rentang nilai | Satuan | Rincian | Outlier | Patahan |
|---|---|---:|---:|---|---|---|---|---:|---:|
| bps | var1254 | 70 | 35 | 2015–2016 | 0.3–14.4 | persen | total | 4 | 0 |
| bps | var2011 | 205 | 35 | 2018–2023 | 0.01–31.7 | persen | total | 3 | 0 |
| bps | var2016 | 525 | 35 | 2019–2023 | 13.02–97.12 | persen | air_minum, fasilitas_kesehatan, sanitasi | 17 | 0 |
| ilostat | SDG_0111_SEX_AGE_RT | 218 | 1 | 2000–2025 | 5.642–72.24 | persen | SEX=SEX_F;AGE=AGE_YTHADULT_Y15-24, SEX=SEX_F;AGE=AGE_YTHADULT_YGE15, SEX=SEX_F;AGE=AGE_YTHADULT_YGE25, SEX=SEX_M;AGE=AGE_YTHADULT_Y15-24, SEX=SEX_M;AGE=AGE_YTHADULT_YGE15, SEX=SEX_M;AGE=AGE_YTHADULT_YGE25, SEX=SEX_T;AGE=AGE_YTHADULT_Y15-24, SEX=SEX_T;AGE=AGE_YTHADULT_YGE15, SEX=SEX_T;AGE=AGE_YTHADULT_YGE25 | 0 | 0 |
| ilostat | SDG_0131_SEX_SOC_RT | 30 | 1 | 2002–2022 | 0–100 | persen | SEX=SEX_F;SOC=SOC_CONTIG_MAT, SEX=SEX_F;SOC=SOC_CONTIG_UNE, SEX=SEX_M;SOC=SOC_CONTIG_UNE, SEX=SEX_T;SOC=SOC_CONTIG_CHILD, SEX=SEX_T;SOC=SOC_CONTIG_DISAB, SEX=SEX_T;SOC=SOC_CONTIG_INJ, SEX=SEX_T;SOC=SOC_CONTIG_PENSION, SEX=SEX_T;SOC=SOC_CONTIG_POOR, SEX=SEX_T;SOC=SOC_CONTIG_TOTAL, SEX=SEX_T;SOC=SOC_CONTIG_UNE, SEX=SEX_T;SOC=SOC_CONTIG_VULN | 1 | 0 |
| ilostat | SDG_1041_NOC_RT | 23 | 1 | 2004–2026 | 57.66–62.82 | persen | total | 0 | 0 |
| wdi | SI.DST.50MD | 33 | 1 | 1984–2025 | 3.6–10.3 | persen | total | 0 | 0 |
| wdi | SI.POV.DDAY | 33 | 1 | 1984–2025 | 3.7–86.8 | persen | total | 0 | 0 |

## Pemetaan rincian BPS

| Rincian Silver | Label/code asal | Seri |
|---|---|---|
| total | Tidak ada / 0 | var2011, var1254 |
| air_minum | Akses pada layanan air minum (1683) | var2016 |
| sanitasi | Akses pada layanan sanitasi dasar (1684) | var2016 |
| mobilitas | Akses pada mobilitas dasar (1685) | var2016; tidak ada observasi |
| fasilitas_kesehatan | Akses pada fasilitas kesehatan dasar (1686) | var2016 |

Rincian ILOSTAT memakai kode dimensi asli dari DSD, mis. `SEX=SEX_T;AGE=AGE_YTHADULT_YGE15`,
karena snapshot DSD tidak memuat codelist/label kode (keputusan K-004).

## data/gold/

| Tabel | Baris | Kolom |
|---|---:|---:|
| data/gold/panel_provinsi.parquet | 304 | 10 |
| data/gold/panel_provinsi_long.parquet | 731 | 13 |
| data/gold/kelengkapan_panel.parquet | 28 | 10 |
| data/gold/papua_historis.parquet | 46 | 19 |

Panel Gold Sprint 1 hanya berisi seri BPS provinsi; integrasi pembanding nasional dan kamus kolom Gold menyusul di Sprint 2–3.
