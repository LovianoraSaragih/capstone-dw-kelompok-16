# Hasil Pengujian Ekstraksi ILOSTAT

## 1. Hasil pembacaan berkas CSV

| Berkas | Baris mentah | Baris hasil |
|---|---:|---:|
| SDG_0111_SEX_AGE_RT | 218 | 218 |
| SDG_0131_SEX_SOC_RT | 30 | 30 |
| SDG_1041_NOC_RT | 23 | 23 |
| **Total** | **271** | **271** |

Seluruh baris berhasil dibaca tanpa kehilangan baris.

## 2. Hasil pembacaan metadata JSON

| Berkas | Hasil |
|---|---|
| SDG_0111_SEX_AGE_RT.json (DSD) | Berhasil dibaca |
| SDG_0131_SEX_SOC_RT.json (DSD) | Berhasil dibaca |
| SDG_1041_NOC_RT.json (DSD) | Berhasil dibaca |
| dataflow.json | Berhasil dibaca (1.215 dataflow) |

Ketiga DSD berhasil dibaca untuk memperoleh informasi dimensi dan atribut.

## 3. Pengujian lineage

- Seluruh 271 baris hasil ekstraksi memiliki `_berkas_raw` dan `_sha256_raw`.
- Hash SHA-256 ketiga CSV sesuai dengan MANIFEST.csv.
- Pemeriksaan seluruh 7 berkas ILOSTAT (3 CSV dan 4 JSON) menunjukkan 7 berkas cocok dan 0 gagal.

## 4. Kesimpulan

Pembaca ILOSTAT berhasil membaca 3 berkas CSV dan 4 berkas JSON. Sebanyak 271 baris observasi berhasil diekstraksi. Seluruh baris observasi memiliki atribut lineage, dan hash ketujuh berkas sumber sesuai dengan MANIFEST.csv.
