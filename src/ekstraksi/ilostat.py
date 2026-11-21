"""Pembaca ILOSTAT SDMX-CSV dengan resolusi dimensi dari DSD."""
import csv
import json

import pandas as pd

from src.common.manifest import RAW, sha256_raw

SUMBER = "ilostat"
SNAPSHOT = "2026-10-20"
FILES = ["SDG_0111_SEX_AGE_RT", "SDG_0131_SEX_SOC_RT", "SDG_1041_NOC_RT"]
STANDAR = {"REF_AREA", "FREQ", "MEASURE"}
FREQ_JENIS = {"A": "tahun", "S": "semester", "Q": "triwulan", "M": "bulan"}


def _dimensi(stem):
    rel = f"{SUMBER}/{SNAPSHOT}/dsd/{stem}.json"
    d = json.loads((RAW / rel).read_text(encoding="utf-8"))
    ds = d["data"]["dataStructures"][0]
    dl = ds["dataStructureComponents"]["dimensionList"]
    dims = [x["id"] for x in dl.get("dimensions", [])]
    waktu = [x["id"] for x in dl.get("timeDimensions", [])]
    breakdown = [x for x in dims if x not in STANDAR and x not in waktu]
    return dims, breakdown


def _satuan(kode):
    return {"PT": "persen"}.get(kode.strip(), kode.strip().lower())


def baca_ilostat():
    frames = []
    seri_meta = {}
    for stem in FILES:
        rel = f"{SUMBER}/{SNAPSHOT}/data/DF_{stem}.csv"
        with open(RAW / rel, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        dims, breakdown = _dimensi(stem)
        data = []
        for r in rows:
            nilai = (r.get("OBS_VALUE") or "").strip()
            if nilai == "":
                continue
            if r.get("REF_AREA") != "IDN":
                raise ValueError(f"REF_AREA di luar Indonesia pada {stem}: {r.get('REF_AREA')!r}")
            mult = (r.get("UNIT_MULT") or "").strip()
            faktor = 10 ** int(mult) if mult != "" else 1
            bagian = [f"{d}={r[d]}" for d in breakdown if (r.get(d) or "").strip()]
            rincian = ";".join(bagian) if bagian else "total"
            freq = (r.get("FREQ") or "").strip()
            data.append({
                "sumber": SUMBER,
                "seri_kode": stem,
                "wilayah_kode": 9999,
                "nama_wilayah": "Indonesia",
                "periode": (r.get("TIME_PERIOD") or "").strip(),
                "jenis_periode": FREQ_JENIS.get(freq, freq),
                "rincian": rincian,
                "nilai": float(nilai) * faktor,
                "satuan": _satuan(r.get("UNIT_MEASURE") or ""),
                "_berkas_raw": rel,
                "_sha256_raw": sha256_raw(rel),
                "obs_status": r.get("OBS_STATUS") or "",
                "note_indicator": r.get("NOTE_INDICATOR") or "",
                "_ref_area": r.get("REF_AREA") or "",
                "_freq": freq,
                "_measure": r.get("MEASURE") or "",
                "_unit_mult": mult,
            })
        frames.append(pd.DataFrame(data))
        seri_meta[stem] = {
            "baris_mentah": len(rows),
            "baris_silver": len(data),
            "dimensi": dims,
            "breakdown": breakdown,
        }
    gabungan = pd.concat(frames, ignore_index=True)
    meta = {"baris_mentah": int(sum(v["baris_mentah"] for v in seri_meta.values())), "seri": seri_meta}
    return gabungan, meta
