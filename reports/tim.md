# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Lapisan silver mengambil tiga sumber mentah yang berbeda bentuk (JSON BPS WebAPI, SDMX-CSV ILOSTAT, JSON WDI) dan mengubahnya menjadi **satu tabel observasi yang panjang dan bertipe**, `data/silver/silver.parquet`, dengan kontrak 13 kolom yang tetap. Lapisan ini tidak mengimputasi, mengagregasi, atau mengubah bentuk nilai. Setelah itu tabel diprofilkan (statistik deskriptif, outlier, ketersediaan), diperiksa kelengkapan dan duplikasinya, ditandai kemungkinan patahan seri, lalu diringkas menjadi `metrics.json`.

Lapisan ini terdiri dari empat tahap:

1. **Harmonisasi** (`transformasi.py`): gabungkan keluaran tiga pembaca, seragamkan tipe dan string, tegakkan kolom wajib, urutkan, tulis Parquet.
2. **Profiling** (`profil.py`): statistik per seri, matriks ketersediaan, penanda outlier z-score dan IQR, grafik garis dan boxplot.
3. **Pembersihan dan pemeriksaan** (`pembersihan.py`): grid kelengkapan BPS, pemeriksaan duplikat pada kunci alami, penanda patahan yang terdokumentasi dan kandidat patahan heuristik.
4. **Pengukuran** (`metrik.py`): membaca Parquet dan JSON metrik sementara, lalu menulis `results/<nim>/metrics.json`.

## Data dan lineage

Alur data yang dilakukan:

| Langkah | Masukan | Keluaran |
| --- | --- | --- |
| Ekstraksi (`baca_bps`, `baca_ilostat`, `baca_wdi`) | `data/raw/<sumber>/<snapshot>/...` | tiga DataFrame dengan kolom umum plus kolom `_` khusus sumber |
| `ke_silver` | tiga DataFrame tersebut | satu DataFrame, 13 kolom, terurut |
| `tulis_silver` | DataFrame | `data/silver/silver.parquet` |
| `profil.tulis_laporan` | DataFrame silver dengan penanda outlier | `profil_deskriptif.csv`, `matriks_ketersediaan.csv`, `profil_anomali.csv`, `gambar/deret_*.png`, `gambar/boxplot_*.png` |
| `pembersihan.tulis_laporan` | DataFrame silver, grid, hasil cek duplikat | `grid_bps.csv`, `kelengkapan.csv`, `pembersihan.md` |
| `metrik.main` | `silver.parquet`, `data/interim/*_metrik.json` | `results/<nim>/metrics.json` (nim bawaan 124450115) |

Kolom penanda `outlier_z`, `outlier_iqr`, `patahan_definisi` dan `patahan_kandidat` dihitung pada salinan DataFrame. Pada kode yang ditampilkan, kolom-kolom itu **tidak** ikut tersimpan di `silver.parquet`, yang hanya memuat 13 kolom kontrak. Hasilnya tetap ada di `profil_anomali.csv` dan sebagai angka di JSON sementara.

## Masalah data dan penanganannya

Pemeriksaan Sprint 1 menghasilkan 1.137 baris dan 17 kolom pada data Silver. Masalah yang ditemukan meliputi celah panel, nilai ekstrem, perbedaan format dan satuan, serta penyesuaian katalog wilayah dan metadata sumber.

| Masalah | Temuan dan jumlah | Penanganan | Bukti |
|---|---|---|---|
| Missing dan celah panel | Terdapat 292 sel kosong dari 1.092 sel grid tiga seri BPS, dengan kelengkapan keseluruhan 73,26%. var2011 memiliki 29 sel kosong (87,61% lengkap), var2016 memiliki 255 (67,31%), dan var1254 memiliki 8 (89,74%). | Sel kosong dipertahankan tanpa imputasi karena tidak ada sumber nilai pengganti yang dapat dipastikan. Rincian yang tidak memiliki observasi tetap dipertahankan agar kekosongan terlihat. | reports/kelengkapan.csv; K-005; K-006 |
| Outlier | Terdapat 25 baris terdeteksi metode IQR dan 13 baris terdeteksi Z-score. Sebanyak 13 baris terdeteksi oleh kedua metode, sedangkan 12 hanya terdeteksi IQR. | Outlier diberi penanda dan tidak dihapus maupun di-winsorize karena dapat menggambarkan kondisi wilayah yang sebenarnya. | reports/profil_anomali.csv; K-007 |
| Patahan seri | Tidak ada patahan terdefinisi dan tidak ada kandidat patahan pada seluruh seri yang diperiksa. | Patahan hanya ditandai apabila didukung catatan metadata atau memenuhi kriteria heuristik yang ditetapkan. | Silver: patahan_definisi dan patahan_kandidat; K-008 |
| Duplikasi | Tidak ditemukan duplikasi berdasarkan kunci sumber, seri, wilayah, periode, jenis periode, dan rincian. | Kunci unik dipertahankan dan hanya snapshot yang ditetapkan yang digunakan. | Silver; K-009; reports/validasi.md |
| Format dan satuan | Metadata sumber tidak selalu mencantumkan satuan. Periode berasal dari format berbeda antarsumber. | var2011 dan var1254 diseragamkan menjadi persen. Periode seluruh seri diseragamkan menjadi tahun tanpa mengubah nilai. | K-002; K-012 |
| Wilayah dan katalog | Kode 9999 digunakan untuk Indonesia, sedangkan kode wilayah provinsi mengikuti katalog BPS. Empat provinsi baru di Papua belum memiliki observasi pada ketiga seri BPS yang dibahas dalam keputusan katalog. | Pemetaan kode wilayah disesuaikan dengan katalog BPS. Baris provinsi pemekaran tanpa observasi tidak dibuat secara artifisial. | K-001 |
| Revisi ekstraksi BPS | Sebanyak 800 baris hasil ekstraksi JSON WebAPI BPS diperiksa silang terhadap CSV dan tidak ditemukan perbedaan nilai. | Struktur JSON berpaginasi diperbaiki dengan pencocokan kode metadata, bukan posisi baris. | K-003 |
| Metadata ILOSTAT | Penanganan mencakup 271 baris observasi dan pembacaan 3 CSV observasi serta 4 JSON metadata. | Kode dimensi asli dipertahankan agar label kategori tidak ditebak dan metadata tetap dapat ditelusuri. | K-004; K-014 |
| Status observasi dan pembanding nasional | Sebanyak 337 baris terkait pembanding nasional dan seri ILOSTAT ditangani dalam keputusan integrasi. | Kode 9999 dan nama sumber dipertahankan untuk pembanding nasional. Status observasi tidak dihilangkan agar informasi revisi dan provisional tetap tersedia. | K-013 |
| Integrasi dan pembentukan Gold | Data Silver berjumlah 1.137 baris, sedangkan Gold panel provinsi berjumlah 280 baris. | Integrasi dilakukan dengan mempertahankan sumber data terpisah pada tahap ekstraksi. Rekonsiliasi pembanding nasional ditunda ke Sprint 2 karena perbedaan cakupan dan granularitas. | K-010; K-011; K-016 |

Catatan interpretasi:
- Nilai kosong pada baris Silver berjumlah 0, tetapi grid panel tetap memiliki 292 sel kosong. Kedua angka mengukur hal yang berbeda.
- Pemeriksaan var2011 pada 35 wilayah yang tersedia menemukan 5 kombinasi wilayah-tahun yang tidak tersedia pada 2023. Angka ini berasal dari pemeriksaan rentang periode dan tidak menggantikan angka kelengkapan grid.
- Log K-005 secara khusus mencatat 195 sel kosong pada grid rincian mobilitas. Angka ini merupakan catatan dengan cakupan rincian tersendiri dan tidak dijumlahkan lagi ke total 292 sel kosong.
- Penanda outlier tidak otomatis berarti kesalahan data.
- Dampak baris dalam log merupakan jumlah sesuai konteks keputusan masing-masing, bukan selalu jumlah baris yang diubah atau dihapus.

Seluruh angka mengacu pada data Silver, laporan profiling, laporan kelengkapan, hasil validasi, dan ID keputusan dalam log Sprint 1.


## Artefak keluaran

| Artefak | Penghasil |
| --- | --- |
| `data/silver/silver.parquet` | `tulis_silver` |
| `reports/.../profil_deskriptif.csv`, `matriks_ketersediaan.csv`, `profil_anomali.csv` | `profil.tulis_laporan` |
| `reports/.../gambar/deret_<sumber>_<seri>.png`, `boxplot_<sumber>_<seri>.png` | `profil.grafik` |
| `reports/.../grid_bps.csv`, `kelengkapan.csv`, `pembersihan.md` | `pembersihan.tulis_laporan` |
| `results/<nim>/metrics.json` | `metrik.main` |

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
