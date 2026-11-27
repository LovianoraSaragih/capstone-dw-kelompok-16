# AI_LOG — Kelompok 16

Satu baris per pemakaian AI yang bermakna (ChatGPT, Claude, Copilot, Bravais, dan sejenisnya).
Ringkas dan jujur; transkrip penuh tidak diminta. Yang dinilai bukan "pakai AI atau tidak",
melainkan "mengerti atau tidak" — isi kolom terakhir dengan apa yang Anda ubah dari keluarannya.

| Tanggal | Siapa (NIM) | Alat | Untuk apa | Apa yang diubah dari keluarannya |
|---|---|---|---|---|
| 2026-11-09 | 124450115 | opencode | membaca struktur JSON BPS/ILOSTAT/WDI dan menyusun pembaca | mengganti tebakan posisi baris dengan pencocokan kode metadata, menambah uji silang CSV, dan memeriksa ulang kunci paginasi |
| 2026-11-09 | 124450115 | opencode | menyusun transformasi Silver, profil, dan pembersihan | menetapkan satuan persen dari definisi indikator, tidak mengimputasi var1254, dan menurunkan ambang kandidat patahan menjadi 5 poin |
| 2026-11-09 | 124450115 | opencode | menyusun panel Gold, validasi, dan data dictionary | menunda rekonsiliasi nasional ke Sprint 2 dan memastikan semua angka laporan dihasilkan kode |
| 2026-11-27 | 124450115 | opencode | menyusun kolom turunan panel Gold | menetapkan indeks rata-rata komponen tersedia, memakai baris 9999 sebagai pembanding, dan hanya menghitung perubahan tahun berurutan |
| 2026-11-27 | 124450115 | opencode | mengintegrasikan basis data SQL dan rekonsiliasi nasional ke pipeline Gold | memanggil modul yang sudah ada dari src/gold/__init__.py, menambah dua aturan validasi, dan mendokumentasikan keluaran SQL/rekonsiliasi |
