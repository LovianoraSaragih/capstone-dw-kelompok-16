# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Proyek Sprint 1 mengolah tiga sumber data, yaitu Badan Pusat Statistik (BPS), International Labour Organization (ILOSTAT), dan World Development Indicators (WDI). Data mencakup tiga seri BPS, tiga seri ILOSTAT, dan dua seri WDI.

Hasil integrasi menghasilkan 1.137 baris data Silver dengan 17 kolom. Pemeriksaan panel tiga seri BPS menemukan 292 sel kosong dari 1.092 sel grid, sehingga kelengkapan keseluruhan mencapai 73,26%. Nilai kosong tersebut dipertahankan tanpa imputasi. Hasil validasi menunjukkan 10 dari 10 aturan lolos. Pada Sprint 1, Gold difokuskan pada panel provinsi BPS, sedangkan rekonsiliasi pembanding nasional ditunda ke Sprint 2.

## Data dan lineage
Data mentah berasal dari tiga sumber, yaitu BPS, ILOSTAT, dan WDI. Snapshot yang digunakan adalah 20 Oktober 2026. Berdasarkan pemeriksaan MANIFEST.csv, terdapat 18 berkas yang cocok dengan manifest.

Ekstraksi menghasilkan 800 baris data BPS, 271 baris data ILOSTAT, dan 66 baris data WDI. Pada data BPS, hasil ekstraksi JSON WebAPI diperiksa silang dengan CSV dan tidak ditemukan perbedaan nilai pada 800 baris yang diperiksa (K-003). Ekstraksi ILOSTAT menggunakan tiga CSV observasi dan empat JSON metadata, termasuk DSD dan dataflow (K-014).

Informasi asal data dipertahankan melalui kolom `_berkas_raw` dan `_sha256_raw`. Kolom tersebut membantu menelusuri berkas sumber dan identitas snapshot yang digunakan. Keputusan penggunaan snapshot dan pembentukan kunci data dicatat dalam `log-keputusan.csv`, khususnya K-009 dan K-015.

Pemeriksaan ini merupakan validasi terhadap berkas snapshot yang tersedia. Perbandingan menyeluruh antara snapshot 20 Oktober 2026 dan hasil penarikan API terbaru belum dilaporkan pada Sprint 1.

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


## Integrasi dan rekonsiliasi
Pada Sprint 1, integrasi Gold difokuskan pada pembentukan panel provinsi berdasarkan data BPS. Hasilnya adalah 280 baris pada Gold panel dan 800 baris pada Gold panel panjang.

Data ILOSTAT dan WDI dipertahankan sebagai pembanding nasional. Seri pembanding tersebut memiliki cakupan wilayah dan tingkat rincian yang berbeda dari data BPS yang disusun berdasarkan provinsi. Oleh karena itu, perbandingan langsung belum dilakukan sebagai rekonsiliasi final.

Sesuai keputusan K-010, rekonsiliasi pembanding nasional ditunda ke Sprint 2. Keputusan K-013 mempertahankan kode wilayah nasional 9999, nama sumber, dan status observasi ILOSTAT agar informasi sumber tetap dapat ditelusuri.

Analisis kuantitatif mengenai selisih seri utama dengan pembanding nasional, pengaruh perbedaan definisi dan metode, serta perubahan vintage WDI belum diselesaikan pada Sprint 1. Hal tersebut menjadi pekerjaan lanjutan dan tidak dinyatakan sebagai hasil yang sudah teruji.

## Validasi dan reproduksibilitas
Validasi dijalankan melalui `python pipeline.py`. Pemeriksaan mencakup rentang nilai persentase, validitas kode wilayah, konsistensi satuan, kelengkapan rincian, keunikan kunci Silver, pemeriksaan penanda imputasi, kelengkapan panel per seri, keberadaan panel Gold, dan duplikasi pada Gold.

Hasil pemeriksaan yang tercatat pada `reports/validasi.md` adalah 10 dari 10 aturan lolos. Tidak ditemukan nilai persentase di luar rentang yang ditetapkan, kode wilayah tidak valid, satuan yang tidak konsisten, rincian kosong, maupun duplikasi kunci Silver. Pemeriksaan juga menghasilkan laporan kelengkapan panel untuk tiga seri BPS.

Hasil kelengkapan panel adalah:
- var2011: 205 dari 234 sel terisi atau 87,61%.
- var2016: 525 dari 780 sel terisi atau 67,31%.
- var1254: 70 dari 78 sel terisi atau 89,74%.

Hasil metrik validasi untuk NIM 124450083 dicatat melalui perintah:

`python -m src.common.hasil 124450083 aturan_validasi=10 aturan_lolos=10`

Hasilnya disimpan pada `results/124450083/metrics.json`.

Pipeline dapat dijalankan kembali dari repository menggunakan perintah `python pipeline.py`, dengan syarat dependensi dan berkas data mentah yang tercatat dalam manifest tersedia. Bukti hasil validasi dapat diperiksa pada `reports/validasi.md`, sedangkan keputusan pengolahan dapat ditelusuri melalui `log-keputusan.csv`.

Pengukuran waktu eksekusi dari kondisi awal yang bersih belum dicatat. Perbandingan performa pandas dengan DuckDB atau Dask juga belum dilakukan, sehingga belum ada kesimpulan mengenai perbedaan waktu maupun penggunaan sumber daya di antara teknologi tersebut.

Keterbatasan lainnya adalah pemeriksaan penanda imputasi belum menjadi verifikasi independen apabila kolom `is_imputed` tidak tersedia. Dalam kondisi tersebut, pemeriksaan mengikuti asumsi bahwa transformasi Silver saat ini tidak melakukan imputasi nilai numerik. Keterbatasan ini perlu diperhatikan ketika pipeline dikembangkan lebih lanjut.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
