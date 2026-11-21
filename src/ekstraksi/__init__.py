"""Tahap 1 — Ekstraksi data mentah BPS."""

from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, sha256_raw


BERKAS = {
    "var2011": "bps/2026-10-20/sdg10_10_2_1_v2011.csv",
    "var1254": "bps/2026-10-20/sdg17_17_1_1_v1254.csv",
    "var2016": "bps/2026-10-20/sdg1_1_4_1_v2016.csv",
}


def jalankan():
    """Baca tiga CSV BPS dan kembalikan data mentah beserta lineage."""
    hasil = {}

    for seri, berkas in BERKAS.items():
        path = RAW / berkas

        df = pd.read_csv(path)
        df["_berkas_raw"] = berkas
        df["_sha256_raw"] = sha256_raw(berkas)

        hasil[seri] = df

    return hasil
