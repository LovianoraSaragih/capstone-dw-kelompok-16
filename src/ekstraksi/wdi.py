
"""Pembaca data mentah WDI untuk Kasus 16."""

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, baca, sha256_raw


def jalankan():
    """Membaca data observasi WDI dan metadata pendamping."""
    manifest = baca(RAW)

    daftar = sorted(
        berkas for berkas in manifest
        if berkas.startswith("wdi/")
    )

    tabel = []
    metadata = {}

    for berkas in daftar:
        jalur = RAW / berkas
        checksum = sha256_raw(berkas)

        with open(jalur, encoding="utf-8") as f:
            isi = json.load(f)

        if "/data/" in berkas:
            if not isinstance(isi, list) or len(isi) < 2:
                raise ValueError(f"Struktur JSON WDI tidak sesuai: {berkas}")

            observasi = isi[1]

            if not isinstance(observasi, list):
                raise ValueError(f"Data observasi WDI bukan list: {berkas}")

            df = pd.json_normalize(observasi)
            df["_berkas_raw"] = berkas
            df["_sha256_raw"] = checksum
            tabel.append(df)

            print(f"{berkas}: {len(df)} baris")

        else:
            metadata[berkas] = {
                "isi": isi,
                "lineage": {
                    "_berkas_raw": berkas,
                    "_sha256_raw": checksum,
                },
            }

            print(f"{berkas}: metadata dibaca")

    if not tabel:
        raise ValueError("Tidak ditemukan data observasi WDI dalam manifest.")

    hasil = pd.concat(tabel, ignore_index=True, sort=False)
    hasil.attrs["metadata_wdi"] = metadata

    print(f"\nTotal data WDI: {len(hasil)} baris")
    print(f"Total metadata WDI: {len(metadata)} berkas")

    return hasil
