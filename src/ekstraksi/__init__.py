
"""Tahap 1 — Ekstraksi seluruh sumber data mentah."""

import pandas as pd

from src.common.manifest import RAW, baca
from .bps import jalankan as ekstrak_bps
from .wdi import jalankan as ekstrak_wdi
from .ilostat import jalankan as ekstrak_ilostat


def jalankan():
    """Gabungkan seluruh keluaran pembaca menjadi satu DataFrame mentah."""

    # Membaca masing-masing sumber
    bps = ekstrak_bps()
    wdi = ekstrak_wdi()
    ilostat = ekstrak_ilostat()

    # Mengumpulkan seluruh DataFrame
    daftar_df = [bps, wdi, *ilostat.values()]

    # Menyimpan metadata dan lineage metadata sebelum penggabungan
    metadata = {
        "bps": bps.attrs.get("metadata_bps", {}),
        "wdi": wdi.attrs.get("metadata_wdi", {}),
        "ilostat": {
            nama: {
                "dsd": df.attrs.get("ilostat_dsd"),
                "dataflow": df.attrs.get("ilostat_dataflow"),
            }
            for nama, df in ilostat.items()
        },
    }

    # Menghindari konflik atribut ketika concat
    for df in daftar_df:
        df.attrs = {}

    # Menggabungkan tanpa menyeragamkan kolom sumber
    hasil = pd.concat(
        daftar_df,
        ignore_index=True,
        sort=False,
    )

    hasil.attrs["metadata_ekstraksi"] = metadata
    hasil.attrs["berkas_dibaca"] = len(baca(RAW))
    hasil.attrs["format"] = 2

    print("\n=== RINGKASAN EKSTRAKSI GABUNGAN ===")
    print(f"Jumlah berkas manifest: {hasil.attrs['berkas_dibaca']}")
    print(f"Jumlah baris mentah: {len(hasil)}")
    print(f"Jumlah kolom: {len(hasil.columns)}")
    print(f"Jumlah sumber: 3")

    return hasil
