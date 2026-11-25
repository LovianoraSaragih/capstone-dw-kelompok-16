
# Katalog Seri Data — Kelompok 16, Kasus 16

Katalog ini mencatat identitas indikator, keterkaitan dengan Sustainable Development Goals (SDGs), satuan, sumber metadata, dan keputusan pengolahan untuk delapan seri yang digunakan dalam proyek.

Snapshot data yang digunakan: 20 Oktober 2026.

## 1. Katalog seri BPS

| Kode seri | Nama indikator | Kode SDG | Satuan | Sumber metadata | Keterangan |
|---|---|---|---|---|---|
| var2011 | Proporsi penduduk yang hidup di bawah 50 persen dari median pendapatan, menurut provinsi | 10.2.1 | Persen | `data/raw/bps/2026-10-20/json/sdg10_10_2_1_v2011.json` dan `manifest_asal.json` | Satuan pada metadata kosong. Penetapan persen mengikuti keputusan K-002. |
| var2016 | Proporsi rumah tangga dengan akses terhadap pelayanan dasar menurut provinsi | 1.4.1 | Persen | `data/raw/bps/2026-10-20/json/sdg1_1_4_1_v2016.json` dan `manifest_asal.json` | Metadata BPS mencantumkan satuan Persen. Rincian meliputi air minum, sanitasi, mobilitas, dan fasilitas kesehatan. |
| var1254 | Total pendapatan pemerintah sebagai proporsi terhadap PDB menurut sumbernya | 17.1.1 | Persen | `data/raw/bps/2026-10-20/json/sdg17_17_1_1_v1254.json` dan `manifest_asal.json` | Satuan pada metadata kosong. Penetapan persen mengikuti keputusan K-002. |

## 2. Katalog seri ILOSTAT

| Kode seri | Nama indikator | Kode SDG | Satuan | Sumber metadata | Keterangan |
|---|---|---|---|---|---|
| SDG_0111_SEX_AGE_RT | SDG indicator 1.1.1: Working poverty rate by sex and age | 1.1.1 | Persen | `data/raw/ilostat/2026-10-20/dsd/SDG_0111_SEX_AGE_RT.json` dan `metadata/dataflow.json` | Tingkat kemiskinan penduduk yang bekerja. Menggunakan garis kemiskinan internasional US$3 per hari berdasarkan PPP. |
| SDG_0131_SEX_SOC_RT | SDG indicator 1.3.1: Proportion of population covered by social protection floors/systems by sex and function | 1.3.1 | Proporsi/cakupan penduduk | `data/raw/ilostat/2026-10-20/dsd/SDG_0131_SEX_SOC_RT.json` dan `metadata/dataflow.json` | Mengukur cakupan perlindungan sosial menurut jenis fungsi. Nilai atribut satuan belum diverifikasi dari snapshot. |
| SDG_1041_NOC_RT | SDG indicator 10.4.1: Labour income share as a percent of GDP | 10.4.1 | Persen | `data/raw/ilostat/2026-10-20/dsd/SDG_1041_NOC_RT.json` dan `metadata/dataflow.json` | Rasio pendapatan tenaga kerja terhadap produk domestik bruto. |

## 3. Katalog seri World Development Indicators (WDI)

| Kode seri | Nama indikator | Kode SDG | Satuan | Sumber metadata | Keterangan |
|---|---|---|---|---|---|
| SI.DST.50MD | Proportion of people living below 50 percent of median income (%) | 10.2.1 | Persen | `data/raw/wdi/2026-10-20/metadata/sumber46_indikator.json` | Kolom unit kosong; tanda persen tercantum pada nama indikator. |
| SI.POV.DDAY | Poverty headcount ratio at $3.00 a day (2021 PPP) (% of population) | 1.1.1 | Persen | `data/raw/wdi/2026-10-20/metadata/sumber46_indikator.json` | Kolom unit kosong; tanda persen tercantum pada nama indikator. Menggunakan garis kemiskinan US$3 per hari berdasarkan PPP 2021. |

## 4. Catatan satuan dan keputusan pengolahan

1. Seri BPS `var2011` dan `var1254` memiliki kolom satuan kosong pada metadata mentah. Keduanya ditetapkan menggunakan satuan persen berdasarkan karakter indikator dan rentang nilai, sesuai keputusan K-002 pada `log-keputusan.csv`.
2. Seri BPS `var2016` memiliki satuan Persen pada metadata sumber.
3. Metadata WDI untuk `SI.DST.50MD` dan `SI.POV.DDAY` memiliki kolom `unit` kosong, tetapi nama indikator secara eksplisit menyebutkan persentase.
4. Untuk ILOSTAT, DSD menyediakan atribut `UNIT_MEASURE`, `UNIT_MEASURE_TYPE`, dan `UNIT_MULT`, tetapi nilai atribut satuan belum diverifikasi dalam katalog ini. Satuan tidak boleh dianggap telah dikonfirmasi hanya dari keberadaan atribut tersebut.
5. Semua seri dalam pipeline menggunakan periode tahunan sesuai keputusan K-012.
6. Kode dimensi ILOSTAT dipertahankan dalam rincian Silver karena snapshot DSD yang digunakan tidak menyediakan codelist atau label kode yang diperlukan untuk menerjemahkannya. Hal ini mengikuti keputusan K-004.
7. Pemetaan kode SDG pada katalog menunjukkan keterkaitan indikator dengan target SDG. Nama indikator dan deskripsi mengikuti metadata sumber masing-masing.

## 5. Referensi keputusan tim

| ID keputusan | Pokok keputusan | Dampak terhadap katalog |
|---|---|---|
| K-002 | Penetapan satuan persen untuk var2011 dan var1254 | Menjelaskan satuan yang tidak tercantum pada metadata BPS. |
| K-004 | Mempertahankan kode dimensi asli ILOSTAT | Menjelaskan penggunaan kode dimensi dalam rincian data. |
| K-012 | Menyeragamkan jenis periode menjadi tahun | Menjelaskan periode seluruh seri dalam Silver. |
| K-013 | Mempertahankan pembanding nasional dan status observasi ILOSTAT | Menjelaskan perlakuan data pembanding nasional. |

## 6. Batasan metadata

Katalog ini menggunakan metadata yang tersimpan pada snapshot 20 Oktober 2026. Informasi yang tidak tersedia atau belum terverifikasi pada snapshot tidak diisi dengan asumsi. Apabila metadata sumber diperbarui, katalog perlu ditinjau kembali agar tetap sesuai dengan versi data yang digunakan.