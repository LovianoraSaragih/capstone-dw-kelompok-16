# Laporan tim — <Nama tim>, kasus <NN> <judul kasus>

Satu dokumen bersama, enam bagian. Angka harus dapat ditarik ulang dari `data/silver`, `data/gold`,
dan `log-keputusan.csv` yang sudah di-*commit*.

## Ringkasan
Kasus, seri yang ditangani, dan satu kalimat temuan utama tentang kualitas datanya.

## Data dan lineage
Sumber dan format mentah, jumlah berkas, cara `_berkas_raw`/`_sha256_raw` dibentuk, dan hasil tarik
ulang API (bila dilakukan): apa yang berubah sejak snapshot 17–20 Oktober 2026.

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
Seri utama vs pembanding nasional: selisih, penjelasannya (definisi, metode, vintage, granularitas),
dan hasil analisis revisi dari arsip WDI.

## Validasi dan reproduksibilitas
Skema validasi (aturan, hasil lolos/gagal), waktu `python pipeline.py` dari nol, perbandingan pandas
vs DuckDB/Dask, dan keterbatasan yang tersisa.

## Pembagian kerja
| Anggota | NIM | Komponen | Tugas sampingan | Bagian laporan yang ditulis |
|---|---|---|---|---|
