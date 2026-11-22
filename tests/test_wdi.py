"""Pengujian pembaca WDI (4 berkas JSON), filter indicator.id, dan lineage SHA-256."""
import csv
import importlib.util
from pathlib import Path
import unittest

from src.common.manifest import RAW, sha256_raw

SPEC = importlib.util.spec_from_file_location("wdi", Path("src/ekstraksi/wdi.py"))
wdi = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wdi)


class TestPembacaWDI(unittest.TestCase):
    def test_empat_berkas_terbaca_dan_terfilter(self):
        df_obs, meta_obs = wdi.baca_wdi()
        df_meta, _ = wdi.baca_metadata_wdi()

        expected_files = {
            "wdi/2026-10-20/data/kelompok-06-hal-01.json",
            "wdi/2026-10-20/metadata/sumber.json",
            "wdi/2026-10-20/metadata/sumber2_indikator.json",
            "wdi/2026-10-20/metadata/sumber46_indikator.json",
        }
        self.assertEqual(set(meta_obs["berkas"].keys()), expected_files)
        self.assertEqual(len(df_obs), 66)
        self.assertEqual(len(df_meta), 75)

        target = {"SI.DST.50MD", "SI.POV.DDAY"}
        self.assertEqual(set(df_obs["seri_kode"].unique()), target)
        ind_meta = df_meta[df_meta["tipe_metadata"] == "indikator"]
        self.assertEqual(set(ind_meta["id"].unique()), target)

        manifest_sha = {}
        manifest_file = RAW.parent / "MANIFEST.csv"
        if manifest_file.exists():
            with open(manifest_file, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    path_key = row.get("berkas") or row.get("path") or row.get("file") or ""
                    sha_val = row.get("sha256") or row.get("_sha256_raw") or ""
                    if path_key and sha_val:
                        manifest_sha[path_key.replace("\\", "/")] = sha_val.strip()

        for df in (df_obs, df_meta):
            self.assertFalse(df["_berkas_raw"].isna().any())
            self.assertFalse(df["_sha256_raw"].isna().any())
            for rel, sha in zip(df["_berkas_raw"], df["_sha256_raw"]):
                self.assertIn(rel, expected_files)
                self.assertEqual(len(sha), 64)
                self.assertEqual(sha, sha256_raw(rel))
                if rel in manifest_sha:
                    self.assertEqual(sha, manifest_sha[rel])


if __name__ == "__main__":
    df_obs, meta_obs = wdi.baca_wdi()
    df_meta, _ = wdi.baca_metadata_wdi()
    print("=== RINGKASAN JUMLAH BARIS PER BERKAS WDI ===")
    for berkas, info in meta_obs["berkas"].items():
        print(f"{berkas} -> {info}")
    print("Filter seri_kode observasi:", sorted(df_obs["seri_kode"].unique()))
    print("Filter id metadata indikator:", sorted(df_meta[df_meta["tipe_metadata"] == "indikator"]["id"].unique()))
    print("Lineage berkas unik:", sorted(set(df_obs["_berkas_raw"]).union(set(df_meta["_berkas_raw"]))))
    unittest.main(verbosity=2)