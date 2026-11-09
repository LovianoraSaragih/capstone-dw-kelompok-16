"""Tahap 1 — Ekstraksi (pertemuan X). Milik tim.

Baca setiap berkas di data/raw/ (CSV, JSON WebAPI BPS, XLSX BNPB, SDMX ILO, JSON WDI) menjadi
DataFrame mentah yang setia pada sumbernya: jangan membersihkan di sini, cukup ratakan struktur
dan catat asal tiap baris (`_berkas_raw` relatif data/raw/, `_sha256_raw` dari src.common.manifest).
"""
import json
from pathlib import Path

from .bps import baca_bps, cek_csv
from .ilostat import baca_ilostat
from .wdi import baca_wdi

AKAR = Path(__file__).resolve().parents[2]
INTERIM = AKAR / "data" / "interim"


def jalankan():
    """Kembalikan {nama_sumber: DataFrame mentah}."""
    bps, meta_bps = baca_bps()
    ilostat, meta_ilostat = baca_ilostat()
    wdi, meta_wdi = baca_wdi()
    cek = cek_csv(bps)

    berkas = set(bps["_berkas_raw"]) | set(ilostat["_berkas_raw"]) | set(wdi["_berkas_raw"])
    metrik = {
        "baris_mentah": meta_bps["baris_mentah"] + meta_ilostat["baris_mentah"] + meta_wdi["baris_mentah"],
        "format": 4,
        "berkas_dibaca": len(berkas),
        "bps": meta_bps,
        "ilostat": meta_ilostat,
        "wdi": meta_wdi,
        "cek_csv": cek,
    }
    INTERIM.mkdir(parents=True, exist_ok=True)
    (INTERIM / "ekstraksi_metrik.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )
    beda = sum(v["beda_nilai"] for v in cek.values())
    print(
        f"ekstraksi: BPS {len(bps)} baris, ILOSTAT {len(ilostat)}, WDI {len(wdi)}; "
        f"uji silang CSV {beda} beda nilai dari {sum(v['baris_csv'] for v in cek.values())} baris"
    )
    return {"bps": bps, "ilostat": ilostat, "wdi": wdi}
