<<<<<<< HEAD
import csv
import json
from itertools import product
from pathlib import Path

import pandas as pd

from src.common.manifest import RAW, baca, sha256_raw

SERI_BPS = ("v2011", "v2016", "v1254")


def _deteksi_encoding_dan_sep(path_berkas: Path) -> tuple[str, str]:
    """Mendeteksi pengodean karakter dan pemisah kolom CSV tanpa mengubah nilai."""
    for enc in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            sampel = path_berkas.read_text(encoding=enc)[:4096]
            dialect = csv.Sniffer().sniff(sampel, delimiters=",;\t")
            return enc, dialect.delimiter
        except UnicodeDecodeError:
            continue
        except csv.Error:
            return enc, ";" if ";" in sampel else ","
    return "latin-1", ","


def baca_csv_bps(berkas_rel: str, raw_dir: Path = RAW) -> pd.DataFrame:
    """Membaca berkas CSV BPS menjadi tabel panjang mentah + kolom lineage."""
    path_berkas = raw_dir / berkas_rel
    enc, sep = _deteksi_encoding_dan_sep(path_berkas)

    # dtype=str dan keep_default_na=False menjaga pemisah desimal & nilai mentah apa adanya
    df = pd.read_csv(path_berkas, encoding=enc, sep=sep, dtype=str, keep_default_na=False)

    # Antisipasi jika ada berkas CSV berformat lebar (kolom tahun berjejer ke samping)
    kolom_tahun = [c for c in df.columns if str(c).strip().isdigit()]
    kolom_id = [c for c in df.columns if not str(c).strip().isdigit()]
    if kolom_tahun and kolom_id and "nilai" not in df.columns:
        df = df.melt(
            id_vars=kolom_id,
            value_vars=kolom_tahun,
            var_name="tahun",
            value_name="nilai",
        )

    df["_berkas_raw"] = berkas_rel
    df["_sha256_raw"] = sha256_raw(berkas_rel, raw=raw_dir)
    return df


def baca_json_bps(berkas_rel: str, raw_dir: Path = RAW) -> pd.DataFrame:
    """Membongkar JSON bersarang WebAPI BPS (vervar, turvar, tahun, datacontent) menjadi tabel panjang."""
    path_berkas = raw_dir / berkas_rel
    with open(path_berkas, "r", encoding="utf-8") as f:
        isi = json.load(f)

    # Akar JSON BPS berupa list berisi dict (atau dict langsung)
    blok_list = isi if isinstance(isi, list) else [isi]

    baris = []
    for blok in blok_list:
        if not isinstance(blok, dict) or "datacontent" not in blok:
            continue

        datacontent = blok.get("datacontent", {})
        daftar_var = blok.get("var", [])
        daftar_vervar = blok.get("vervar", [])
        daftar_turvar = blok.get("turvar", [{"val": "0", "label": "Tidak ada"}])
        daftar_tahun = blok.get("tahun", [])
        daftar_turtahun = blok.get("turtahun", [{"val": "0", "label": "Tahun"}])

        for var_item, ver_item, tur_item, thn_item, tthn_item in product(
            daftar_var, daftar_vervar, daftar_turvar, daftar_tahun, daftar_turtahun
        ):
            v_id = str(var_item.get("val", ""))
            ver_id = str(ver_item.get("val", ""))
            tur_id = str(tur_item.get("val", ""))
            thn_id = str(thn_item.get("val", ""))
            tthn_id = str(tthn_item.get("val", ""))

            # Kunci standar datacontent BPS: {vervar}{var}{turvar}{tahun}{turtahun}
            kunci_lengkap = f"{ver_id}{v_id}{tur_id}{thn_id}{tthn_id}"
            kunci_tanpa_tthn = f"{ver_id}{v_id}{tur_id}{thn_id}"

            if kunci_lengkap in datacontent:
                nilai_mentah = datacontent[kunci_lengkap]
            elif kunci_tanpa_tthn in datacontent:
                nilai_mentah = datacontent[kunci_tanpa_tthn]
            else:
                continue

            baris.append(
                {
                    "var_id": v_id,
                    "var": str(var_item.get("label", "")),
                    "wilayah_id": ver_id,
                    "wilayah": str(ver_item.get("label", "")),
                    "turvar_id": tur_id,
                    "turvar": str(tur_item.get("label", "")),
                    "tahun_id": thn_id,
                    "tahun": str(thn_item.get("label", "")),
                    "periode_id": tthn_id,
                    "periode": str(tthn_item.get("label", "")),
                    "nilai": str(nilai_mentah),
                    "satuan": str(var_item.get("unit", "")),
                }
            )

    df = pd.DataFrame(baris)
    df["_berkas_raw"] = berkas_rel
    df["_sha256_raw"] = sha256_raw(berkas_rel, raw=raw_dir)
    return df


def jalankan_bps(raw_dir: Path = RAW) -> pd.DataFrame:
    """Membaca ke-6 berkas BPS (3 CSV, 3 JSON) di MANIFEST.csv dan menggabungkannya."""
    manifest = baca(raw_dir)
    berkas_bps = sorted(
        b for b in manifest
        if b.startswith("bps/") and any(s in b for s in SERI_BPS)
    )

    daftar_df = []
    print("=== Ringkasan Pembacaan Berkas BPS ===")
    for berkas_rel in berkas_bps:
        if berkas_rel.endswith(".csv"):
            df_berkas = baca_csv_bps(berkas_rel, raw_dir=raw_dir)
        elif berkas_rel.endswith(".json"):
            df_berkas = baca_json_bps(berkas_rel, raw_dir=raw_dir)
        else:
            continue

        print(f"- {berkas_rel}: {len(df_berkas)} baris")
        daftar_df.append(df_berkas)

    if not daftar_df:
        return pd.DataFrame()

    hasil = pd.concat(daftar_df, ignore_index=True)
    print(f"Total keseluruhan baris BPS: {len(hasil)}")
    return hasil


if __name__ == "__main__":
    df_bps = jalankan_bps()
    print("\nKolom hasil:", list(df_bps.columns))
    print("\nContoh 5 baris pertama:")
    print(df_bps.head())
=======
"""Pembaca BPS WebAPI (JSON dinamis) dan uji silang CSV datar."""
import csv
import json
import re

import pandas as pd

from src.common.manifest import RAW, sha256_raw

SUMBER = "bps"
SNAPSHOT = "2026-10-20"

SERI = {
    "sdg10_10_2_1_v2011": {"seri_kode": "var2011", "var_id": "2011", "satuan": "persen"},
    "sdg1_1_4_1_v2016": {"seri_kode": "var2016", "var_id": "2016", "satuan": "persen"},
    "sdg17_17_1_1_v1254": {"seri_kode": "var1254", "var_id": "1254", "satuan": "persen"},
}

RINCIAN = {
    "0": "total",
    "Tidak ada": "total",
    "Akses pada layanan air minum": "air_minum",
    "Akses pada layanan sanitasi dasar": "sanitasi",
    "Akses pada mobilitas dasar": "mobilitas",
    "Akses pada fasilitas kesehatan dasar": "fasilitas_kesehatan",
}

BULAN = {
    "januari": "01", "februari": "02", "maret": "03", "april": "04",
    "mei": "05", "juni": "06", "juli": "07", "agustus": "08",
    "september": "09", "oktober": "10", "november": "11", "desember": "12",
}


def _kode(nilai):
    return str(nilai)


def _bersihkan_catatan(teks):
    if not teks:
        return ""
    teks = re.sub(r"<[^>]+>", " ", teks)
    return re.sub(r"\s+", " ", teks).strip()


def _periode(tahun, turtahun):
    t = turtahun.strip().lower()
    if t == "tahun":
        return tahun, "tahun"
    m = re.search(r"semester\s*([12]|i{1,2})", t)
    if m:
        n = {"i": "1", "ii": "2"}.get(m.group(1), m.group(1))
        return f"{tahun}-S{n}", "semester"
    m = re.search(r"triwulan\s*([1-4]|i{1,3}|iv)", t)
    if m:
        n = {"i": "1", "ii": "2", "iii": "3", "iv": "4"}.get(m.group(1), m.group(1))
        return f"{tahun}-Q{n}", "triwulan"
    m = re.search(r"bulan\s*([a-z]+|\d{1,2})", t)
    if m:
        b = m.group(1)
        n = BULAN.get(b, b.zfill(2) if b.isdigit() else None)
        if n:
            return f"{tahun}-{n}", "bulan"
    raise ValueError(f"turtahun belum didukung: {turtahun!r}")


def _baca_satu(stem, konfig):
    rel = f"{SUMBER}/{SNAPSHOT}/json/{stem}.json"
    halaman = json.loads((RAW / rel).read_text(encoding="utf-8"))
    baris = []
    tidak_cocok = []
    catatan = ""
    for page in halaman:
        vcodes = {_kode(x["val"]): x for x in page["vervar"]}
        varcodes = {_kode(x["val"]): x for x in page["var"]}
        tucodes = {_kode(x["val"]): x for x in page["turvar"]}
        thcodes = {_kode(x["val"]): x for x in page["tahun"]}
        ttcodes = {_kode(x["val"]): x for x in page["turtahun"]}
        for x in page["var"]:
            catatan = _bersihkan_catatan(x.get("note", ""))
        peta = {}
        for v in vcodes:
            for va in varcodes:
                for tu in tucodes:
                    for th in thcodes:
                        for tt in ttcodes:
                            peta[v + va + tu + th + tt] = (v, va, tu, th, tt)
        for kunci, nilai in page["datacontent"].items():
            kunci = str(kunci)
            if kunci not in peta:
                tidak_cocok.append(kunci)
                continue
            v, va, tu, th, tt = peta[kunci]
            turvar_label = tucodes[tu]["label"]
            rincian = RINCIAN.get(tu) or RINCIAN.get(turvar_label) or turvar_label.lower().replace(" ", "_")
            tahun_label = str(thcodes[th]["label"])
            turtahun_label = str(ttcodes[tt]["label"])
            periode, jenis = _periode(tahun_label, turtahun_label)
            unit = (varcodes[va].get("unit") or "").strip().lower()
            satuan = "persen" if (unit == "persen" or konfig["satuan"] == "persen") else unit
            baris.append({
                "sumber": SUMBER,
                "seri_kode": konfig["seri_kode"],
                "wilayah_kode": int(vcodes[v]["val"]),
                "nama_wilayah": str(vcodes[v]["label"]),
                "periode": periode,
                "jenis_periode": jenis,
                "rincian": rincian,
                "nilai": float(nilai),
                "satuan": satuan,
                "_berkas_raw": rel,
                "_sha256_raw": sha256_raw(rel),
                "obs_status": "",
                "note_indicator": catatan,
                "_vervar": v,
                "_var": va,
                "_turvar": tu,
                "_tahun": th,
                "_turtahun": tt,
            })
    return pd.DataFrame(baris), tidak_cocok


def baca_bps():
    frames = []
    seri_meta = {}
    for stem, konfig in SERI.items():
        df, tidak_cocok = _baca_satu(stem, konfig)
        frames.append(df)
        seri_meta[stem] = {
            "seri_kode": konfig["seri_kode"],
            "baris_mentah": int(len(df)),
            "kunci_tidak_cocok": len(tidak_cocok),
            "contoh_tidak_cocok": tidak_cocok[:5],
        }
    gabungan = pd.concat(frames, ignore_index=True)
    meta = {
        "baris_mentah": int(len(gabungan)),
        "seri": seri_meta,
    }
    return gabungan, meta


def domain_bps():
    """Domain lengkap (wilayah, tahun, rincian) dari metadata JSON, termasuk kode tanpa observasi."""
    hasil = {}
    for stem, konfig in SERI.items():
        rel = f"{SUMBER}/{SNAPSHOT}/json/{stem}.json"
        halaman = json.loads((RAW / rel).read_text(encoding="utf-8"))
        wilayah = set()
        tahun = set()
        rincian = set()
        for page in halaman:
            for x in page["vervar"]:
                wilayah.add(int(x["val"]))
            for x in page["tahun"]:
                tahun.add(str(x["label"]))
            for x in page["turvar"]:
                label = str(x["label"])
                rincian.add(
                    RINCIAN.get(_kode(x["val"])) or RINCIAN.get(label) or label.lower().replace(" ", "_")
                )
        hasil[konfig["seri_kode"]] = {
            "wilayah": sorted(wilayah),
            "tahun": sorted(tahun),
            "rincian": sorted(rincian),
        }
    return hasil


def cek_csv(df_json):
    hasil = {}
    for stem, konfig in SERI.items():
        rel = f"{SUMBER}/{SNAPSHOT}/{stem}.csv"
        with open(RAW / rel, encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        j = df_json[df_json["seri_kode"] == konfig["seri_kode"]]
        jmap = {
            (str(r["_vervar"]), str(r["_turvar"]), str(r["_tahun"])): float(r["nilai"])
            for _, r in j.iterrows()
        }
        cmap = {
            (str(r["wilayah_id"]), str(r["turvar_id"]), str(r["tahun_id"])): float(r["nilai"])
            for r in rows
        }
        sama = set(jmap) & set(cmap)
        beda = [k for k in sama if abs(jmap[k] - cmap[k]) > 1e-9]
        hasil[stem] = {
            "baris_csv": len(rows),
            "baris_json": len(jmap),
            "kunci_sama": len(sama),
            "hanya_json": len(set(jmap) - set(cmap)),
            "hanya_csv": len(set(cmap) - set(jmap)),
            "beda_nilai": len(beda),
            "contoh_beda": beda[:5],
        }
    return hasil
>>>>>>> origin/main
