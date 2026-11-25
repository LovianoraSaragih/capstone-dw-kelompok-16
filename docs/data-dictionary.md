# Data dictionary — Kelompok 16, kasus 16

Dihasilkan oleh `src/validasi/dokumentasi.py` dari isi `data/silver/silver.parquet` dan
`data/gold/*.parquet` pada setiap `python pipeline.py`.

## data/silver/silver.parquet

| Kolom | Tipe | Satuan/format | Boleh kosong | Rentang atau nilai sah | Asal | Keterangan |
|---|---|---|---|---|---|---|
| sumber | string | — | tidak | bps, ilostat, wdi | folder data/raw | nama sumber |
| seri_kode | string | — | tidak | var2011, var2016, var1254, SDG_*, SI.* | metadata sumber | kode seri |
| wilayah_kode | int | kode BPS x 100 | tidak | 9999 atau 1100–9700 | vervar BPS / nasional | 9999 = Indonesia |
| nama_wilayah | string | — | tidak | label sumber | vervar BPS / country WDI | mengikuti kapitalisasi sumber |
| periode | string | tahun | tidak | YYYY | tahun BPS / TIME_PERIOD / date | format baku |
| jenis_periode | string | — | tidak | tahun | metadata sumber | semua seri tahunan |
| rincian | string | — | tidak | total, air_minum, sanitasi, mobilitas, fasilitas_kesehatan, kode dimensi ILOSTAT | turvar BPS / DSD ILOSTAT | lihat tabel pemetaan |
| nilai | float | persen | tidak | 0–100 | datacontent / OBS_VALUE / value | proporsi |
| satuan | string | — | tidak | persen | metadata + keputusan log | lihat K-004 |
| _berkas_raw | string | path relatif | tidak | data/raw/... | sumber baris | lineage |
| _sha256_raw | string | sha256 | tidak | 64 hex | src.common.manifest | lineage |
| obs_status | string | — | ya | A, R, M, kosong | OBS_STATUS ILOSTAT | catatan status observasi |
| note_indicator | string | — | ya | teks | note BPS / NOTE_INDICATOR | catatan sumber |
| outlier_z | bool | — | tidak | True/False | src/silver/profil.py | z-score > 3; tidak dihapus |
| outlier_iqr | bool | — | tidak | True/False | src/silver/profil.py | di luar 1.5 IQR; tidak dihapus |
| patahan_definisi | bool | — | tidak | True/False | src/silver/pembersihan.py | hanya jika catatan metadata menyebut patahan |
| patahan_kandidat | bool | — | tidak | True/False | src/silver/pembersihan.py | heuristik median perubahan >= 5 poin |

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
karena snapshot DSD tidak memuat codelist/label kode.

## data/gold/

| Tabel | Baris | Kolom |
|---|---:|---:|
| data/gold/panel_provinsi.parquet | 304 | 28 |
| data/gold/panel_provinsi_long.parquet | 731 | 15 |

Panel Gold Sprint 1 hanya berisi seri BPS provinsi; integrasi pembanding nasional menyusul di Sprint 2.
