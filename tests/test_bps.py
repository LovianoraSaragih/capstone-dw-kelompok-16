"""Pengujian pembaca BPS (3 JSON dan 3 CSV), rincian turvar, dan lineage SHA-256."""
import csv
import importlib.util
from pathlib import Path
import unittest

from src.common.manifest import RAW, sha256_raw

SPEC = importlib.util.spec_from_file_location("bps", Path("src/ekstraksi/bps.py"))
bps = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(bps)


class TestPembacaBPS(unittest.TestCase):
    def test_enam_berkas_terbaca_dan_lineage_valid(self):
        df_json, meta_json = bps.baca_bps()
        df_csv, meta_csv = bps.baca_bps_csv()
        uji_silang = bps.cek_csv(df_json)
        domain = bps.domain_bps()

        expected_json = {
            "bps/2026-10-20/json/sdg10_10_2_1_v2011.json",
            "bps/2026-10-20/json/sdg1_1_4_1_v2016.json",
            "bps/2026-10-20/json/sdg17_17_1_1_v1254.json",
        }
        expected_csv = {
            "bps/2026-10-20/sdg10_10_2_1_v2011.csv",
            "bps/2026-10-20/sdg1_1_4_1_v2016.csv",
            "bps/2026-10-20/sdg17_17_1_1_v1254.csv",
        }

        self.assertEqual(set(df_json["_berkas_raw"].unique()), expected_json)
        self.assertEqual(set(df_csv["_berkas_raw"].unique()), expected_csv)
        self.assertEqual(len(df_json), len(df_csv))

        target_seri = {"var2011", "var2016", "var1254"}
        self.assertEqual(set(df_json["seri_kode"].unique()), target_seri)
        self.assertEqual(set(df_csv["seri_kode"].unique()), target_seri)

        # Metadata turvar var2016 memuat 4 rincian akses; observasi memuat 3 rincian aktif (mobilitas kosong di datacontent)
        self.assertEqual(
            set(domain["var2016"]["rincian"]),
            {"air_minum", "sanitasi", "mobilitas", "fasilitas_kesehatan"},
        )
        rincian_obs_v2016 = set(df_json[df_json["seri_kode"] == "var2016"]["rincian"].unique())
        self.assertEqual(rincian_obs_v2016, {"air_minum", "sanitasi", "fasilitas_kesehatan"})

        for stem, info in meta_json["seri"].items():
            self.assertEqual(info["kunci_tidak_cocok"], 0)
        for stem, info in uji_silang.items():
            self.assertEqual(info["baris_json"], info["baris_csv"])
            self.assertEqual(info["hanya_json"], 0)
            self.assertEqual(info["hanya_csv"], 0)
            self.assertEqual(info["beda_nilai"], 0)

        manifest_sha = {}
        manifest_file = RAW.parent / "MANIFEST.csv"
        if manifest_file.exists():
            with open(manifest_file, encoding="utf-8", newline="") as f:
                for row in csv.DictReader(f):
                    path_key = row.get("berkas") or row.get("path") or row.get("file") or ""
                    sha_val = row.get("sha256") or row.get("_sha256_raw") or ""
                    if path_key and sha_val:
                        manifest_sha[path_key.replace("\\", "/")] = sha_val.strip()

        all_expected = expected_json | expected_csv
        for df in (df_json, df_csv):
            self.assertFalse(df["_berkas_raw"].isna().any())
            self.assertFalse(df["_sha256_raw"].isna().any())
            for rel, sha in zip(df["_berkas_raw"], df["_sha256_raw"]):
                self.assertIn(rel, all_expected)
                self.assertEqual(len(sha), 64)
                self.assertEqual(sha, sha256_raw(rel))
                if rel in manifest_sha:
                    self.assertEqual(sha, manifest_sha[rel])


if __name__ == "__main__":
    df_json, meta_json = bps.baca_bps()
    df_csv, meta_csv = bps.baca_bps_csv()
    uji_silang = bps.cek_csv(df_json)
    domain = bps.domain_bps()
    print("=== RINGKASAN JUMLAH BARIS PER BERKAS BPS (3 JSON & 3 CSV) ===")
    for stem, info in meta_json["seri"].items():
        print(f"bps/2026-10-20/json/{stem}.json -> {info}")
    for berkas, info in meta_csv["berkas"].items():
        print(f"{berkas} -> {info}")
    print("Total baris JSON:", len(df_json), "| Total baris CSV:", len(df_csv))
    print("Uji silang JSON vs CSV:", uji_silang)
    print("Domain turvar var2016 (metadata):", domain["var2016"]["rincian"])
    print("Rincian var2016 (observasi):", sorted(df_json[df_json["seri_kode"] == "var2016"]["rincian"].unique()))
    print("Lineage berkas unik (6 berkas):", sorted(set(df_json["_berkas_raw"]).union(set(df_csv["_berkas_raw"]))))
    unittest.main(verbosity=2)