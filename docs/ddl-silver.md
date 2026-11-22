Dokumen ini menjelaskan alasan di balik tipe data, kunci, constraint, dan indeks pada `sql/silver_ddl.sql`. Skema mengikuti `KOLOM` dan `WAJIB` di `transformasi.py`, sedangkan kunci unik mengikuti `KUNCI` di `pembersihan.py`.

## 1. Ringkasan

| Tabel | Fungsi | Kunci utama | Jenis kunci |
|---|---|---|---|
| `silver_observasi` | Salinan Silver: satu baris per observasi per berkas mentah | `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)` | Komposit, alami |
| `silver_muat_log` | Catatan setiap pemuatan parquet ke database | `id` | Surrogate, auto-increment |

Ada dua keputusan dasar:

1. **Tipe data mengikuti Silver parquet.** Silver adalah sumber kebenaran, jadi database tidak boleh mengubah tipe atau makna nilai.
2. **Kunci `silver_observasi` adalah kunci alami yang sudah dipakai pipeline.** Dengan begitu, pemeriksaan duplikat di Python dan constraint di database menguji hal yang sama.

## 2. Catatan tentang tipe data SQLite

SQLite memakai *type affinity*, bukan tipe yang kaku. Kolom `INTEGER` pada prinsipnya masih bisa menerima teks. Karena itu desain ini bertumpu pada tiga lapis:

- tipe deklaratif (`TEXT`, `INTEGER`, `REAL`) yang menentukan affinity,
- `NOT NULL` dan `CHECK` untuk menolak nilai yang tidak sah,
- validasi dan casting di `pemuat.py` (`wilayah_kode` menjadi `int64`, `nilai` menjadi `float64`) sebelum data masuk, meniru `ke_silver()`.

Hanya ada tiga tipe dasar yang dipakai agar skema mudah dibaca dan mudah dipindahkan ke DBMS lain.

## 3. Tabel `silver_observasi`

### 3.1 Tipe data per kolom

| Kolom | Tipe | Null | Alasan |
|---|---|---|---|
| `sumber` | `TEXT` | NOT NULL | Penanda asal data. `CHECK (sumber IN ('bps','ilostat','wdi'))` menyamai tiga sumber yang digabung di `ke_silver()`, sehingga sumber salah ketik tertolak sejak insert. Jika sumber baru ditambahkan, constraint ini harus diperbarui. |
| `seri_kode` | `TEXT` | NOT NULL | Kodenya campuran: `var2011` (BPS), `SI.POV.DDAY` (WDI), `SDG_0111_SEX_AGE_RT` (ILOSTAT). Mengandung titik, garis bawah, dan huruf, jadi bukan angka. |
| `wilayah_kode` | `INTEGER` | NOT NULL | Kode numerik 4 digit (1100 sampai 9700) dan 9999 untuk nasional, sesuai `panel.py`. Parquet menyimpannya sebagai `int64`. Sebagai integer, perbandingan seperti `IN (9100, 9400)` dan penyaringan 9999 tidak bergantung pada format teks. |
| `nama_wilayah` | `TEXT` | NOT NULL | Label deskriptif. Tidak dijadikan bagian kunci karena penulisannya bisa berbeda antarsumber, dan `wilayah_kode` sudah mengidentifikasi wilayah secara unik. |
| `periode` | `TEXT` | NOT NULL | Di Silver kolom ini diubah dengan `astype(str)`. Dipertahankan sebagai teks supaya periode non-tahunan (jika ada) tidak rusak. Urutan leksikografis tetap benar untuk tahun 4 digit. Kode yang membutuhkan angka, seperti `profil_pembanding.py`, melakukan `astype(int)` sendiri. |
| `jenis_periode` | `TEXT` | NOT NULL | Label kategori (misalnya tahunan). Tidak diberi `CHECK` karena nilai sahnya belum didokumentasikan dan constraint yang salah akan menolak data valid. |
| `rincian` | `TEXT` | NOT NULL | Kode dimensi, misalnya `total`, dan pada ILOSTAT berupa kode asli karena label belum tersedia (lihat batasan di `profil_pembanding.py`). Pembeda observasi dalam satu seri. |
| `nilai` | `REAL` | NOT NULL | Sesuai `float64` di parquet (IEEE 754, 8 byte), jadi tidak ada konversi presisi. `NOT NULL` karena `nilai` termasuk `WAJIB` dan `ke_silver()` menolak nilai kosong. Sel kosong direpresentasikan lewat ketiadaan baris (lihat grid di `pembersihan.py`), bukan `NULL`, sesuai prinsip tanpa imputasi. |
| `satuan` | `TEXT` | NOT NULL | Label satuan. Disimpan apa adanya karena `profil.py` dan `profil_pembanding.py` menggabungkan satuan unik per seri. |
| `_berkas_raw` | `TEXT` | NOT NULL | Jejak asal data (nama berkas mentah). Termasuk bagian kunci, lihat bagian 3.2. |
| `_sha256_raw` | `TEXT` | NOT NULL | Checksum berkas mentah untuk keterlacakan. `CHECK (length = 64)` memastikan bentuknya heksadesimal SHA-256 yang utuh. Tidak dijadikan kunci karena sudah ditentukan oleh `_berkas_raw`. |
| `obs_status` | `TEXT` | NOT NULL, default `''` | Di `ke_silver()`, nilai kosong diisi `""` lewat `fillna("")`. Default `''` menjaga kesetaraan dengan parquet dan menghindari tiga keadaan (`NULL`, kosong, berisi) pada kolom teks. |
| `note_indicator` | `TEXT` | NOT NULL, default `''` | Sama dengan `obs_status`. Kolom ini dibaca `tandai_patahan()` lewat `fillna("").str.lower()`, jadi string kosong aman dipakai. |

Constraint tambahan pada tabel:

- `CHECK (typeof(nilai) IN ('real','integer'))` menutup celah dynamic typing SQLite: teks tidak bisa menyusup ke kolom `nilai` meskipun affinity-nya `REAL`.
- `CHECK (length(_sha256_raw) = 64)` seperti dijelaskan di atas.

### 3.2 Pemilihan kunci utama

**Kunci:** `(sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw)`

Alasan:

1. **Identik dengan `KUNCI` di `pembersihan.py`.** Fungsi `cek_duplikat()` sudah menganggap enam kolom ini sebagai identitas satu baris. Constraint database menegakkan aturan yang sama, dan `pemuat.py` melakukan pra-pemeriksaan dengan kunci yang sama sehingga galatnya jelas.
2. **`_berkas_raw` ada di dalam kunci** agar dua snapshot atau dua format (misalnya JSON dan CSV BPS) yang memuat observasi sama bisa tersimpan berdampingan. Tanpa kolom ini, pemuatan dua snapshot akan gagal atau salah satunya hilang secara diam-diam. `deduplikasi_dua_snapshot()` di `klasifikasi_anomali.py` memang bekerja dengan kunci tanpa `_berkas_raw` (`KUNCI_OBSERVASI`), tetapi itu adalah tahap keputusan *setelah* data lengkap tersedia, bukan tahap penyimpanan.
3. **`nilai` tidak masuk kunci.** Dua baris dengan kunci sama tetapi nilai berbeda adalah revisi, bukan observasi berbeda. Itu persis kasus yang ditangani aturan deduplikasi dua snapshot.

Alternatif kunci yang ditolak:

| Alternatif | Alasan ditolak |
|---|---|
| Surrogate key (`id` auto-increment) saja | Tidak mencegah baris ganda secara semantik. Kunci alami tetap harus dipasang sebagai `UNIQUE`, sehingga surrogate hanya menambah kolom dan indeks. |
| Kunci tanpa `_berkas_raw` (5 kolom) | Menolak penyimpanan dua snapshot sekaligus dan membuat log revisi tidak bisa dibentuk dari database. |
| Kunci dengan `_sha256_raw` sebagai ganti `_berkas_raw` | Lebih panjang dan tidak terbaca manusia. Dua berkas berbeda dengan isi sama akan dianggap satu berkas. |

### 3.3 `WITHOUT ROWID`

Tabel dibuat `WITHOUT ROWID` karena kunci utamanya komposit dan berupa teks. Pada tabel biasa, SQLite menyimpan data di B-tree berdasarkan rowid dan membuat indeks terpisah untuk PK, sehingga enam kolom kunci tersimpan dua kali. Dengan `WITHOUT ROWID`, tabel itu sendiri adalah B-tree berurutan menurut PK. Dampaknya:

- Pencarian dengan prefiks PK (`sumber`, lalu `sumber + seri_kode`, dan seterusnya) langsung memakai urutan tabel.
- Penyimpanan lebih hemat.
- Konsekuensinya, setiap indeks sekunder membawa seluruh kolom PK di dalamnya, sehingga indeks tambahan relatif mahal. Itu sebabnya indeks sekunder dibatasi dua saja.

### 3.4 Indeks sekunder

| Indeks | Kolom | Pola akses yang dilayani |
|---|---|---|
| `ix_silver_seri_wilayah_periode` | `seri_kode, wilayah_kode, periode` | Query per seri tanpa menyebut `sumber`, misalnya filter `seri_kode IN (...)` di `profil_pembanding.py` dan pembentukan panel di `panel.py`. Prefiks PK diawali `sumber`, jadi PK tidak melayani pola ini dengan baik. |
| `ix_silver_wilayah` | `wilayah_kode` | Penyaringan lintas seri per wilayah, misalnya nasional (9999) atau provinsi Papua lama (9100 dan 9400). |

Jika ukuran data tetap kecil, kedua indeks ini bisa dihapus tanpa mengubah hasil query, hanya kecepatannya.

## 4. Tabel `silver_muat_log`

### 4.1 Tipe data per kolom

| Kolom | Tipe | Alasan |
|---|---|---|
| `id` | `INTEGER PRIMARY KEY AUTOINCREMENT` | Surrogate key, lihat 4.2. |
| `waktu_utc` | `TEXT` | SQLite tidak punya tipe tanggal-waktu bawaan. Format ISO-8601 dengan zona UTC (`isoformat`) terurut benar secara leksikografis dan dapat diproses fungsi tanggal SQLite. |
| `berkas_parquet` | `TEXT` | Nama berkas parquet yang dimuat. |
| `sha256_parquet` | `TEXT` | Checksum parquet, dihitung dari isi berkas. Menjawab pertanyaan "database ini dibangun dari parquet versi yang mana?". |
| `jumlah_baris` | `INTEGER` | Hitungan, harus bilangan bulat. Dibandingkan dengan jumlah baris parquet saat verifikasi. |
| `jumlah_seri` | `INTEGER` | Hitungan `COUNT(DISTINCT seri_kode)`. |
| `jumlah_nilai` | `REAL` | `SUM(nilai)` sebagai pemeriksaan silang. Bertipe `REAL` karena jumlah dari `float64`. Pemuat membandingkannya dengan toleransi relatif, bukan kesamaan persis, karena penjumlahan titik mengambang bergantung pada urutan. |

Semua kolom `NOT NULL`: log yang tidak lengkap tidak berguna sebagai jejak audit.

### 4.2 Pemilihan kunci utama

**Kunci:** `id` (surrogate, `AUTOINCREMENT`).

Alasan:

- Tidak ada kunci alami yang andal. `waktu_utc` bisa bertabrakan, dan `sha256_parquet` sama jika parquet yang sama dimuat dua kali, padahal itu dua peristiwa pemuatan yang sah dan layak dicatat.
- Tabel ini adalah log: yang penting adalah urutan kejadian, dan `AUTOINCREMENT` menjamin id tidak dipakai ulang setelah baris dihapus.

Catatan jujur: pada pemuat saat ini, database dibangun ulang dari awal setiap kali dijalankan, sehingga `silver_muat_log` hanya berisi satu baris per berkas database. Pada praktiknya, log ini baru menumpuk riwayat jika Anda mengubah pemuat menjadi mode tambah (*append*) atau menyalin log lama ke database baru. `AUTOINCREMENT` sudah disiapkan untuk kebutuhan itu. Jika tidak ada rencana tersebut, `INTEGER PRIMARY KEY` tanpa `AUTOINCREMENT` sudah cukup dan sedikit lebih ringan.

### 4.3 Tidak ada foreign key

Kedua tabel tidak saling mereferensikan. Log mencatat peristiwa pemuatan secara keseluruhan, bukan per baris observasi. Menautkan setiap observasi ke satu pemuatan baru bermakna jika pemuatan bersifat tambahan, dan hal itu belum dibutuhkan.

## 5. Constraint yang sengaja tidak dipasang

| Constraint | Alasan |
|---|---|
| `CHECK (nilai BETWEEN 0 AND 100)` | Tidak semua seri berupa persentase. `klasifikasi_anomali.py` memang mengasumsikan rentang itu, tetapi seri WDI dan ILOSTAT bisa memiliki satuan lain. Aturan ini lebih tepat berada di lapisan validasi per seri. |
| `CHECK` pada `jenis_periode` dan `satuan` | Daftar nilai sah belum didokumentasikan. Constraint yang salah akan menolak data valid. |
| `FOREIGN KEY` ke tabel dimensi wilayah atau seri | Silver sengaja datar. Dimensi wilayah (`PROVINSI_38` di `panel.py`) bukan padanan satu lawan satu dengan Silver, karena ada kode 9999 dan kode Papua lama yang tidak masuk 38 provinsi. |
| `periode` sebagai `INTEGER` | Merusak periode non-tahunan dan menyimpang dari Silver parquet. |

## 6. Pemetaan ke PostgreSQL (jika dipindahkan)

| SQLite | PostgreSQL | Catatan |
|---|---|---|
| `TEXT` | `TEXT` | Sama. `sumber` bisa menjadi `VARCHAR` atau `ENUM`. |
| `INTEGER` (`wilayah_kode`) | `INTEGER` atau `SMALLINT` | Kode maksimum 9999 muat di `SMALLINT`. |
| `INTEGER` (hitungan log) | `BIGINT` | Mengikuti `int64` di parquet. |
| `REAL` | `DOUBLE PRECISION` | Hati-hati: `REAL` di PostgreSQL hanya 4 byte, jadi jangan dipakai langsung. |
| `waktu_utc TEXT` | `TIMESTAMPTZ` | Tipe waktu asli tersedia. |
| `INTEGER PRIMARY KEY AUTOINCREMENT` | `BIGINT GENERATED ALWAYS AS IDENTITY` | |
| `WITHOUT ROWID` | dihapus | Tidak ada padanan. Gunakan `CLUSTER` jika urutan fisik penting. |
| `CHECK (typeof(nilai) ...)` | dihapus | Tipe kolom sudah ketat. |

## 7. Keterbatasan

- Dynamic typing SQLite berarti jaminan tipe bergantung pada `CHECK` dan validasi pemuat. Menulis ke database dengan alat lain tanpa melewati `pemuat.py` bisa menyisipkan nilai bertipe salah di kolom selain `nilai`.
- Constraint `sumber IN (...)` perlu diperbarui jika sumber data baru ditambahkan.
- Kunci mencakup `_berkas_raw`, jadi unik di database belum berarti unik secara semantik. Penyatuan snapshot tetap harus dilakukan lewat `deduplikasi_dua_snapshot()` atau query yang setara.
- Desain ini diuji pada data sintetis dengan skema yang sama. Ukuran data nyata dan pola query sebenarnya belum diukur, sehingga keputusan indeks sebaiknya ditinjau ulang setelah dijalankan pada `silver.parquet` asli.
