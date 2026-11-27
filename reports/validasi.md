# Validasi Silver dan Gold

| Aturan | Status | Detail |
|---|---|---|
| skema_minimal | LOLOS | Kolom wajib, periode, dan lineage sesuai |
| nilai_persen_0_100 | LOLOS | 0 baris di luar rentang 0-100 |
| wilayah_kode_valid | LOLOS | 0 kode tidak valid |
| satuan_seragam_per_seri | LOLOS | 0 seri memiliki lebih dari satu satuan |
| rincian_terisi | LOLOS | 0 rincian kosong |
| silver_kunci_unik | LOLOS | 0 baris duplikat pada kunci Silver |
| imputasi_memiliki_penanda | LOLOS | Tidak ada imputasi nilai dalam transformasi Silver; nilai berasal dari observasi sumber. Imputasi di masa depan wajib memakai is_imputed. |
| kelengkapan_panel_per_seri | LOLOS | 3 seri dilaporkan |
| gold_panel_terbentuk | LOLOS | 304 baris |
| gold_nilai_asli_utuh | LOLOS | Seluruh kolom nilai asli tersedia |
| gold_turunan_lengkap | LOLOS | 16 kolom turunan tersedia |
| gold_kunci_unik | LOLOS | 0 duplikat |

## Kelengkapan panel per seri

Sumber: `reports/kelengkapan.csv`.

| Seri | Sel grid | Terisi | Kosong | Kelengkapan |
|---|---:|---:|---:|---:|
| var2011 | 234 | 205 | 29 | 87.61% |
| var2016 | 780 | 525 | 255 | 67.31% |
| var1254 | 78 | 70 | 8 | 89.74% |

## Ringkasan

Total: 12/12 aturan lolos.

Nilai kosong pada grid menunjukkan tidak adanya observasi sumber dan tidak diimputasi.
