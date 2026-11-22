"""Pengujian tautan kategori calon anomali profil, aturan deduplikasi dua snapshot, dan log-keputusan.csv."""
import csv
import importlib.util
from pathlib import Path
import unittest

import pandas as pd

SPEC = importlib.util.spec_from_file_location("klasifikasi_anomali", Path("src/silver/klasifikasi_anomali.py"))
ka = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ka)


class TestKlasifikasiAnomaliDanLog(unittest.TestCase):
    def test_semua_calon_anomali_terklasifikasi_dan_tercatat(self):
        df_profil = pd.read_csv("reports/profil_anomali.csv")
        df_klas = ka.buat_tabel_klasifikasi()

        # Setiap calon anomali dari profil (25 baris) tertaut 1-ke-1 dengan kategorinya
        self.assertEqual(len(df_profil), len(df_klas))
        self.assertEqual(len(df_klas), 25)
        self.assertTrue(set(df_klas["kategori_anomali"]).issubset({"outlier_asli", "patahan_seri", "galat_input"}))

        # Outlier asli dan patahan seri tidak boleh diubah nilainya
        non_galat = df_klas[df_klas["kategori_anomali"].isin(["outlier_asli", "patahan_seri"])]
        self.assertTrue((non_galat["nilai_sebelum"] == non_galat["nilai_sesudah"]).all())
        self.assertTrue((non_galat["tindakan"] == "ditandai_dan_dijelaskan").all())

    def test_aturan_deduplikasi_dua_snapshot(self):
        snap1 = pd.DataFrame([
            {"sumber": "bps", "seri_kode": "var2011", "wilayah_kode": 1100, "periode": "2022", "rincian": "total", "nilai": 10.5},
            {"sumber": "bps", "seri_kode": "var2011", "wilayah_kode": 1200, "periode": "2022", "rincian": "total", "nilai": 12.0},
        ])
        snap2 = pd.DataFrame([
            # Angka sama -> bukan duplikat salah
            {"sumber": "bps", "seri_kode": "var2011", "wilayah_kode": 1100, "periode": "2022", "rincian": "total", "nilai": 10.5},
            # Angka berbeda -> revisi
            {"sumber": "bps", "seri_kode": "var2011", "wilayah_kode": 1200, "periode": "2022", "rincian": "total", "nilai": 12.4},
        ])
        hasil, revisi = ka.deduplikasi_dua_snapshot(snap1, snap2)
        self.assertEqual(len(hasil), 2)
        self.assertEqual(len(revisi), 1)
        self.assertEqual(int(revisi.iloc[0]["wilayah_kode"]), 1200)
        self.assertAlmostEqual(float(revisi.iloc[0]["nilai_lama"]), 12.0)
        self.assertAlmostEqual(float(revisi.iloc[0]["nilai_revisi"]), 12.4)

    def test_log_keputusan_lengkap(self):
        with open("log-keputusan.csv", encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        by_id = {r["id"]: r for r in rows}
        for kode in ("K-024", "K-025", "K-026"):
            self.assertIn(kode, by_id)
        self.assertIn("25 calon anomali", by_id["K-024"]["keputusan"])
        self.assertIn("0 galat input", by_id["K-025"]["keputusan"])
        self.assertIn("deduplikasi dua snapshot", by_id["K-026"]["keputusan"].lower())


if __name__ == "__main__":
    unittest.main(verbosity=2)