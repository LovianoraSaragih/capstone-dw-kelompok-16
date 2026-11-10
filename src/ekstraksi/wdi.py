"""Pembaca WDI JSON untuk pembanding nasional."""
import json

import pandas as pd

from src.common.manifest import RAW, sha256_raw

SUMBER = "wdi"
SNAPSHOT = "2026-10-20"
REL = f"{SUMBER}/{SNAPSHOT}/data/kelompok-06-hal-01.json"
TARGET = {"SI.DST.50MD", "SI.POV.DDAY"}


def _satuan(nama):
    return "persen" if "%" in nama else "tidak_ada"


def baca_wdi():
    d = json.loads((RAW / REL).read_text(encoding="utf-8"))
    obs = d[1]
    rows = [o for o in obs if o["indicator"]["id"] in TARGET]
    data = []
    for o in rows:
        if o.get("value") is None:
            continue
        data.append({
            "sumber": SUMBER,
            "seri_kode": o["indicator"]["id"],
            "wilayah_kode": 9999,
            "nama_wilayah": o["country"]["value"],
            "periode": str(o["date"]),
            "jenis_periode": "tahun",
            "rincian": "total",
            "nilai": float(o["value"]),
            "satuan": _satuan(o["indicator"]["value"]),
            "_berkas_raw": REL,
            "_sha256_raw": sha256_raw(REL),
            "obs_status": o.get("obs_status") or "",
            "note_indicator": "",
            "_indicator_name": o["indicator"]["value"],
            "_unit_raw": o.get("unit") or "",
            "_scale": o.get("scale") or "",
        })
    df = pd.DataFrame(data)
    meta = {
        "baris_mentah": len(rows),
        "baris_silver": int(len(df)),
        "indikator": sorted(TARGET),
        "null_dibuang": len(rows) - int(len(df)),
    }
    return df, meta
