"""Pengujian pencocokan docs/data-dictionary.md dengan kolom Silver aktual dan contoh penelusuran lineage."""
import hashlib
from pathlib import Path
import unittest

import pandas as pd
from src.common.manifest import baca
from src.validasi.dokumentasi import DESKRIPSI_KOLOM


class TestDataDictionarySilver(unittest.TestCase):
    def test_semua_kolom_silver_terdokumentasi(self):
        silver = pd.read_parquet("data/silver/silver.parquet")
        teks_kamus = Path("docs/data-dictionary.md").read_text(encoding="utf-8")

        self.assertEqual(set(silver.columns), set(DESKRIPSI_KOLOM.keys()))
        for kol in silver.columns:
            self.assertIn(f"| `{kol}` |", teks_kamus)
        self.assertIn("17 dari 17 kolom (100% cocok)", teks_kamus)

    def test_contoh_penelusuran_lineage_valid(self):
        silver = pd.read_parquet("data/silver/silver.parquet")
        teks_kamus = Path("docs/data-dictionary.md").read_text(encoding="utf-8")
        manifest = baca()

        row = silver[
            (silver["sumber"] == "bps")
            & (silver["seri_kode"] == "var1254")
            & (silver["wilayah_kode"] == 1100)
            & (silver["periode"] == "2015")
        ].iloc[0]

        berkas = row["_berkas_raw"]
        sha = row["_sha256_raw"]
        self.assertIn(berkas, teks_kamus)
        self.assertIn(sha, teks_kamus)
        self.assertEqual(manifest[berkas], sha)

        sha_file = hashlib.sha256(Path(f"data/raw/{berkas}").read_bytes()).hexdigest()
        self.assertEqual(sha_file, sha)


if __name__ == "__main__":
    unittest.main(verbosity=2)