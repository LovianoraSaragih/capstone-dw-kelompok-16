
"""Tahap validasi Silver dan Gold."""

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import baca
from src.common.skema import KUNCI, periksa_silver

from . import dokumentasi

AKAR = Path(__file__).resolve().parents[2]
REPORTS = AKAR / "reports"
INTERIM = AKAR / "data" / "interim"


def _baca_kelengkapan():
    """Membaca laporan kelengkapan yang dibuat tahap Silver."""
    jalur = REPORTS / "kelengkapan.csv"

    if not jalur.exists():
        return pd.DataFrame()

    return pd.read_csv(jalur)


def _aturan(silver, gold, manifest, panel):
    aturan = []

    # 1. Skema dan lineage minimal Silver
    salah = periksa_silver(silver, manifest)
    aturan.append((
        "skema_minimal",
        not salah,
        "; ".join(salah) if salah else "Kolom wajib, periode, dan lineage sesuai"
    ))

    # 2. Rentang proporsi
    persen = silver[silver["satuan"].str.lower() == "persen"]
    buruk = persen[
        (persen["nilai"] < 0) | (persen["nilai"] > 100)
    ]
    aturan.append((
        "nilai_persen_0_100",
        buruk.empty,
        f"{len(buruk)} baris di luar rentang 0-100"
    ))

    # 3. Kode wilayah
    kode = silver["wilayah_kode"]
    valid = (
        (kode == 9999)
        | ((kode >= 1100) & (kode <= 9700) & (kode % 100 == 0))
    )
    aturan.append((
        "wilayah_kode_valid",
        bool(valid.all()),
        f"{int((~valid).sum())} kode tidak valid"
    ))

    # 4. Konsistensi satuan
    satuan = silver.groupby(
        ["sumber", "seri_kode"]
    )["satuan"].nunique()

    aturan.append((
        "satuan_seragam_per_seri",
        bool((satuan <= 1).all()),
        f"{int((satuan > 1).sum())} seri memiliki lebih dari satu satuan"
    ))

    # 5. Rincian terisi
    rincian = silver["rincian"].astype(str).str.strip()
    aturan.append((
        "rincian_terisi",
        bool((rincian != "").all()),
        f"{int((rincian == '').sum())} rincian kosong"
    ))

    # 6. Keunikan kunci Silver
    duplikat = int(silver.duplicated(KUNCI).sum())
    aturan.append((
        "silver_kunci_unik",
        duplikat == 0,
        f"{duplikat} baris duplikat pada kunci Silver"
    ))

    # 7. Penanda imputasi
    # Pipeline saat ini tidak melakukan imputasi pada kolom nilai.
    # Jika imputasi diterapkan di masa depan, kolom is_imputed wajib ada.
    if "is_imputed" in silver.columns:
        marker = silver["is_imputed"]
        marker_valid = (
            marker.notna().all()
            and marker.isin([True, False]).all()
        )
        detail_imputasi = (
            "Kolom is_imputed tersedia dan seluruh penandanya valid"
        )
    else:
        marker_valid = True
        detail_imputasi = (
            "Tidak ada imputasi nilai dalam transformasi Silver; "
            "nilai berasal dari observasi sumber. "
            "Imputasi di masa depan wajib memakai is_imputed."
        )

    aturan.append((
        "imputasi_memiliki_penanda",
        bool(marker_valid),
        detail_imputasi
    ))

    # 8. Kelengkapan panel per seri
    kolom_panel = {
        "seri_kode", "sel_grid", "sel_terisi",
        "sel_kosong", "persen_lengkap"
    }

    panel_valid = (
        not panel.empty
        and kolom_panel.issubset(panel.columns)
    )

    if panel_valid:
        panel_valid = (
            (panel["sel_grid"] > 0).all()
            and (
                panel["sel_grid"]
                == panel["sel_terisi"] + panel["sel_kosong"]
            ).all()
            and (
                (
                    100 * panel["sel_terisi"] / panel["sel_grid"]
                ).round(2)
                - panel["persen_lengkap"]
            ).abs().le(0.01).all()
        )

    aturan.append((
        "kelengkapan_panel_per_seri",
        bool(panel_valid),
        (
            f"{len(panel)} seri dilaporkan"
            if panel_valid
            else "Laporan panel tidak tersedia atau perhitungannya tidak sesuai"
        )
    ))

    # 9. Gold terbentuk
    gold_panel = gold.get("panel_provinsi")
    aturan.append((
        "gold_panel_terbentuk",
        gold_panel is not None and len(gold_panel) > 0,
        f"{0 if gold_panel is None else len(gold_panel)} baris"
    ))

    # 10. Keunikan kunci Gold
    panjang = gold.get("panel_provinsi_long")

    if panjang is None:
        aturan.append((
            "gold_kunci_unik",
            False,
            "Tabel panjang tidak ada"
        ))
    else:
        dup = int(panjang.duplicated(KUNCI).sum())
        aturan.append((
            "gold_kunci_unik",
            dup == 0,
            f"{dup} duplikat"
        ))

    return aturan


def jalankan(silver, gold):
    manifest = baca()
    panel = _baca_kelengkapan()

    aturan = _aturan(silver, gold, manifest, panel)
    lolos = sum(1 for _, ok, _ in aturan if ok)

    kolom = dokumentasi.tulis(
        silver,
        gold,
        AKAR / "docs" / "data-dictionary.md"
    )

    REPORTS.mkdir(parents=True, exist_ok=True)

    baris = [
        "# Validasi Silver dan Gold",
        "",
        "| Aturan | Status | Detail |",
        "|---|---|---|",
    ]

    for nama, ok, detail in aturan:
        status = "LOLOS" if ok else "GAGAL"
        baris.append(f"| {nama} | {status} | {detail} |")

    # Tabel kelengkapan panel
    baris += [
        "",
        "## Kelengkapan panel per seri",
        "",
        "Sumber: `reports/kelengkapan.csv`.",
        "",
        "| Seri | Sel grid | Terisi | Kosong | Kelengkapan |",
        "|---|---:|---:|---:|---:|",
    ]

    if panel.empty:
        baris.append("| Belum tersedia | - | - | - | - |")
    else:
        for _, r in panel.iterrows():
            baris.append(
                f"| {r['seri_kode']} | {int(r['sel_grid'])} "
                f"| {int(r['sel_terisi'])} | {int(r['sel_kosong'])} "
                f"| {r['persen_lengkap']:.2f}% |"
            )

    baris += [
        "",
        f"## Ringkasan",
        "",
        f"Total: {lolos}/{len(aturan)} aturan lolos.",
        "",
        "Nilai kosong pada grid menunjukkan tidak adanya observasi "
        "sumber dan tidak diimputasi.",
        "",
    ]

    (REPORTS / "validasi.md").write_text(
        "\n".join(baris),
        encoding="utf-8",
        newline="\n"
    )

    metrik = {
        "aturan_validasi": len(aturan),
        "aturan_lolos": lolos,
        "kolom_terdokumentasi": kolom,
        "aturan": [
            {
                "nama": n,
                "lolos": bool(ok),
                "detail": d
            }
            for n, ok, d in aturan
        ]
    }

    INTERIM.mkdir(parents=True, exist_ok=True)

    (INTERIM / "validasi_metrik.json").write_text(
        json.dumps(metrik, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n"
    )

    print(f"validasi: {lolos}/{len(aturan)} aturan lolos")

    gagal = [n for n, ok, _ in aturan if not ok]

    if gagal:
        raise RuntimeError(f"validasi gagal: {gagal}")

    return {"metrik": metrik}
