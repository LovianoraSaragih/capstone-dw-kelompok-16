"""Tahap 8 — Validasi dan dokumentasi (pertemuan XIV–XV). Milik tim.

Tulis skema validasi Silver dan Gold (pandera atau Great Expectations): rentang nilai per satuan,
kelengkapan wilayah, keunikan kunci, konsistensi provinsi vs nasional bila relevan. Laporan
validasi ditulis ke reports/validasi.md. Data dictionary di docs/data-dictionary.md.
"""
import json
from pathlib import Path

from src.common.manifest import baca
from src.common.skema import KUNCI, periksa_silver

from . import dokumentasi

AKAR = Path(__file__).resolve().parents[2]
REPORTS = AKAR / "reports"
INTERIM = AKAR / "data" / "interim"


def _aturan(silver, gold, manifest):
    aturan = []
    salah = periksa_silver(silver, manifest)
    aturan.append((
        "skema_minimal",
        not salah,
        "; ".join(salah) if salah else "11 kolom, kunci unik, periode, lineage cocok",
    ))

    persen = silver[silver["satuan"] == "persen"]
    buruk = persen[(persen["nilai"] < 0) | (persen["nilai"] > 100)]
    aturan.append(("nilai_persen_0_100", buruk.empty, f"{len(buruk)} baris di luar 0-100"))

    kode = silver["wilayah_kode"]
    valid = (kode == 9999) | ((kode >= 1100) & (kode <= 9700) & (kode % 100 == 0))
    aturan.append(("wilayah_kode_valid", bool(valid.all()), f"{int((~valid).sum())} kode tidak valid"))

    satuan = silver.groupby(["sumber", "seri_kode"])["satuan"].nunique()
    aturan.append((
        "satuan_seragam_per_seri",
        bool((satuan <= 1).all()),
        f"{int((satuan > 1).sum())} seri punya lebih dari satu satuan",
    ))

    rincian = silver["rincian"].astype(str).str.strip()
    aturan.append(("rincian_terisi", bool((rincian != "").all()), f"{int((rincian == '').sum())} rincian kosong"))

    panel = gold.get("panel_provinsi")
    aturan.append((
        "gold_panel_terbentuk",
        panel is not None and len(panel) > 0,
        f"{0 if panel is None else len(panel)} baris",
    ))

    panjang = gold.get("panel_provinsi_long")
    if panjang is None:
        aturan.append(("gold_kunci_unik", False, "tabel panjang tidak ada"))
    else:
        dup = int(panjang.duplicated(KUNCI).sum())
        aturan.append(("gold_kunci_unik", dup == 0, f"{dup} duplikat"))
    return aturan


def jalankan(silver, gold):
    manifest = baca()
    aturan = _aturan(silver, gold, manifest)
    lolos = sum(1 for _, ok, _ in aturan if ok)

    kolom = dokumentasi.tulis(silver, gold, AKAR / "docs" / "data-dictionary.md")

    REPORTS.mkdir(parents=True, exist_ok=True)
    baris = [
        "# Validasi Silver dan Gold",
        "",
        "| Aturan | Status | Detail |",
        "|---|---|---|",
    ]
    for nama, ok, detail in aturan:
        baris.append(f"| {nama} | {'LOLOS' if ok else 'GAGAL'} | {detail} |")
    baris += ["", f"Total: {lolos}/{len(aturan)} aturan lolos."]
    (REPORTS / "validasi.md").write_text("\n".join(baris) + "\n", encoding="utf-8", newline="\n")

    metrik = {
        "aturan_validasi": len(aturan),
        "aturan_lolos": lolos,
        "kolom_terdokumentasi": kolom,
        "aturan": [{"nama": n, "lolos": bool(ok), "detail": d} for n, ok, d in aturan],
    }
    INTERIM.mkdir(parents=True, exist_ok=True)
    (INTERIM / "validasi_metrik.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n"
    )

    print(f"validasi: {lolos}/{len(aturan)} aturan lolos")
    gagal = [n for n, ok, _ in aturan if not ok]
    if gagal:
        raise RuntimeError(f"validasi gagal: {gagal}")
    return {"metrik": metrik}
