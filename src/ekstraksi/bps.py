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