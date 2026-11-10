# Validasi Silver dan Gold

| Aturan | Status | Detail |
|---|---|---|
| skema_minimal | LOLOS | 11 kolom, kunci unik, periode, lineage cocok |
| nilai_persen_0_100 | LOLOS | 0 baris di luar 0-100 |
| wilayah_kode_valid | LOLOS | 0 kode tidak valid |
| satuan_seragam_per_seri | LOLOS | 0 seri punya lebih dari satu satuan |
| rincian_terisi | LOLOS | 0 rincian kosong |
| gold_panel_terbentuk | LOLOS | 280 baris |
| gold_kunci_unik | LOLOS | 0 duplikat |

Total: 7/7 aturan lolos.
