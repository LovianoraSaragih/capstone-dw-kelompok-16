"""Pembaca WDI JSON (data observasi dan metadata indikator/sumber) untuk pembanding nasional."""
import json

import pandas as pd

from src.common.manifest import RAW, sha256_raw

SUMBER = "wdi"
SNAPSHOT = "2026-10-20"
REL_DATA = f"{SUMBER}/{SNAPSHOT}/data/kelompok-06-hal-01.json"
REL = REL_DATA
REL_SUMBER = f"{SUMBER}/{SNAPSHOT}/metadata/sumber.json"
REL_INDIKATOR = [
    f"{SUMBER}/{SNAPSHOT}/metadata/sumber2_indikator.json",
    f"{SUMBER}/{SNAPSHOT}/metadata/sumber46_indikator.json",
]
BERKAS_WDI = [REL_DATA, REL_SUMBER, *REL_INDIKATOR]
TARGET = {"SI.DST.50MD", "SI.POV.DDAY"}


def _satuan(nama):
    return "persen" if "%" in nama else "tidak_ada"


def baca_metadata_wdi():
    """Baca 3 berkas metadata WDI (sumber dan indikator target) beserta lineage berkas."""
    baris_meta = []
    ringkasan = {}

    d_sumber = json.loads((RAW / REL_SUMBER).read_text(encoding="utf-8"))
    list_sumber = d_sumber[1]
    sha_sumber = sha256_raw(REL_SUMBER)
    for item in list_sumber:
        baris_meta.append({
            "tipe_metadata": "sumber",
            "id": str(item.get("id") or ""),
            "code": str(item.get("code") or ""),
            "name": str(item.get("name") or ""),
            "lastupdated": str(item.get("lastupdated") or ""),
            "unit": "",
            "source_id": str(item.get("id") or ""),
            "source_value": str(item.get("name") or ""),
            "sourceNote": str(item.get("description") or ""),
            "sourceOrganization": "",
            "topics": "",
            "_berkas_raw": REL_SUMBER,
            "_sha256_raw": sha_sumber,
        })
    ringkasan[REL_SUMBER] = {
        "total_json": len(list_sumber),
        "baris_dibaca": len(list_sumber),
    }

    for rel in REL_INDIKATOR:
        d_ind = json.loads((RAW / rel).read_text(encoding="utf-8"))
        list_ind = d_ind[1]
        rows_ind = [x for x in list_ind if x.get("id") in TARGET]
        sha_ind = sha256_raw(rel)
        for item in rows_ind:
            src = item.get("source") or {}
            topics = "; ".join(
                t.get("value", "") for t in (item.get("topics") or []) if t.get("value")
            )
            baris_meta.append({
                "tipe_metadata": "indikator",
                "id": str(item.get("id") or ""),
                "code": "",
                "name": str(item.get("name") or ""),
                "lastupdated": "",
                "unit": str(item.get("unit") or ""),
                "source_id": str(src.get("id") or ""),
                "source_value": str(src.get("value") or ""),
                "sourceNote": str(item.get("sourceNote") or ""),
                "sourceOrganization": str(item.get("sourceOrganization") or ""),
                "topics": topics,
                "_berkas_raw": rel,
                "_sha256_raw": sha_ind,
            })
        ringkasan[rel] = {
            "total_json": len(list_ind),
            "baris_dibaca": len(rows_ind),
        }

    return pd.DataFrame(baris_meta), ringkasan


def baca_wdi():
    """Baca data observasi WDI dan hubungkan dengan metadata 3 berkas JSON WDI."""
    df_meta, ringkasan_meta = baca_metadata_wdi()

    meta_ind = {}
    sub_ind = df_meta[df_meta["tipe_metadata"] == "indikator"]
    for _, r in sub_ind.iterrows():
        if r["id"] not in meta_ind:
            meta_ind[r["id"]] = r.to_dict()

    d = json.loads((RAW / REL_DATA).read_text(encoding="utf-8"))
    obs = d[1]
    rows = [o for o in obs if o["indicator"]["id"] in TARGET]
    sha_data = sha256_raw(REL_DATA)

    data = []
    for o in rows:
        if o.get("value") is None:
            continue
        ind_id = o["indicator"]["id"]
        info_meta = meta_ind.get(ind_id, {})
        data.append({
            "sumber": SUMBER,
            "seri_kode": ind_id,
            "wilayah_kode": 9999,
            "nama_wilayah": o["country"]["value"],
            "periode": str(o["date"]),
            "jenis_periode": "tahun",
            "rincian": "total",
            "nilai": float(o["value"]),
            "satuan": _satuan(o["indicator"]["value"]),
            "_berkas_raw": REL_DATA,
            "_sha256_raw": sha_data,
            "obs_status": o.get("obs_status") or "",
            "note_indicator": "",
            "_indicator_name": o["indicator"]["value"],
            "_unit_raw": o.get("unit") or "",
            "_scale": o.get("scale") or "",
            "_source_note": info_meta.get("sourceNote", ""),
            "_source_org": info_meta.get("sourceOrganization", ""),
            "_metadata_berkas": info_meta.get("_berkas_raw", ""),
            "_metadata_sha256": info_meta.get("_sha256_raw", ""),
        })

    df = pd.DataFrame(data)
    ringkasan_berkas = {
        REL_DATA: {
            "total_json": len(obs),
            "baris_target": len(rows),
            "baris_non_null": int(len(df)),
            "null_dibuang": len(rows) - int(len(df)),
        },
        **ringkasan_meta,
    }
    meta = {
        "baris_mentah": len(rows),
        "baris_silver": int(len(df)),
        "indikator": sorted(TARGET),
        "null_dibuang": len(rows) - int(len(df)),
        "berkas": ringkasan_berkas,
    }
    return df, meta