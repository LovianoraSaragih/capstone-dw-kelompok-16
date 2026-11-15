
"""Pembaca data mentah BPS untuk Kasus 16."""

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, baca, sha256_raw


def jalankan():
    """Membaca CSV BPS dan menyimpan JSON pendamping sebagai metadata."""
    manifest = baca(RAW)
    daftar = sorted(
        berkas for berkas in manifest
        if berkas.startswith("bps/") 
    )

    tabel = []
    metadata = {}

    for berkas in daftar:
        jalur = RAW / berkas
        checksum = sha256_raw(berkas)

        if jalur.suffix.lower() == ".csv":
            df = pd.read_csv(jalur)
            df["_berkas_raw"] = berkas
            df["_sha256_raw"] = checksum
            tabel.append(df)

            print(f"{berkas}: {len(df)} baris")

        elif jalur.suffix.lower() == ".json":
            with open(jalur, encoding="utf-8") as f:
                metadata[berkas] = {
                    "isi": json.load(f),
                    "lineage": {
                        "_berkas_raw": berkas,
                        "_sha256_raw": checksum,
                    },
                }

            print(f"{berkas}: metadata dibaca")

    if not tabel:
        raise ValueError("Tidak ditemukan CSV BPS dalam manifest.")

    hasil = pd.concat(tabel, ignore_index=True, sort=False)
    hasil.attrs["metadata_bps"] = metadata

    print(f"\nTotal data BPS: {len(hasil)} baris")
    print(f"Total metadata BPS: {len(metadata)} berkas")

    return hasil
