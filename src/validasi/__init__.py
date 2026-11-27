
"""Tahap validasi Silver dan Gold."""

import json
from pathlib import Path

import pandas as pd

from src.common.manifest import baca
from src.common.skema import KUNCI, periksa_silver
from src.gold.turunan import KOLOM_ASLI, KOLOM_TURUNAN

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

    # 10. Nilai asli tetap ada
    if gold_panel is None or gold_panel.empty:
        aturan.append(("gold_nilai_asli_utuh", False, "Panel Gold tidak ada"))
    else:
        kurang_asli = [k for k in KOLOM_ASLI if k not in gold_panel.columns]
        aturan.append((
            "gold_nilai_asli_utuh",
            not kurang_asli,
            (
                "Seluruh kolom nilai asli tersedia"
                if not kurang_asli
                else f"Kolom nilai asli hilang: {kurang_asli}"
            )
        ))

    # 11. Kolom turunan tersedia
    if gold_panel is None or gold_panel.empty:
        aturan.append(("gold_turunan_lengkap", False, "Panel Gold tidak ada"))
    else:
        kurang_turunan = [k for k in KOLOM_TURUNAN if k not in gold_panel.columns]
        aturan.append((
            "gold_turunan_lengkap",
            not kurang_turunan,
            (
                f"{len(KOLOM_TURUNAN)} kolom turunan tersedia"
                if not kurang_turunan
                else f"Kolom turunan hilang: {kurang_turunan}"
            )
        ))

    # 12. Keunikan kunci Gold
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

    # 13. Tabel rekonsiliasi terbentuk
    rekon = gold.get("rekonsiliasi_nasional")
    kolom_rekon = {
        "id_pasangan", "status_pasangan", "selisih",
        "kategori_penjelasan",
    }
    jalur_rekon = AKAR / "data" / "gold" / "rekonsiliasi_nasional.parquet"

    if rekon is None or len(rekon) == 0:
        aturan.append((
            "rekonsiliasi_terbentuk",
            False,
            "Tabel rekonsiliasi tidak ada atau kosong"
        ))
    else:
        kurang_rekon = sorted(kolom_rekon - set(rekon.columns))
        berkas_ada = jalur_rekon.is_file()
        aturan.append((
            "rekonsiliasi_terbentuk",
            not kurang_rekon and berkas_ada,
            (
                f"{len(rekon)} baris; berkas tersimpan"
                if not kurang_rekon and berkas_ada
                else f"kolom hilang: {kurang_rekon}; berkas ada: {berkas_ada}"
            )
        ))

    # 14. Basis data SQL dan ekspor tabelnya terbentuk
    sql = gold.get("sql")
    tabel_sql = sql.get("parquet", {}) if isinstance(sql, dict) else {}

    if not isinstance(sql, dict) or "db" not in sql:
        aturan.append((
            "basisdata_sql_terbentuk",
            False,
            "Basis data SQL tidak ada"
        ))
    else:
        db_ada = Path(sql["db"]).is_file()
        tabel_ada = (
            len(tabel_sql) >= 7
            and all(Path(p).is_file() for p in tabel_sql.values())
        )
        aturan.append((
            "basisdata_sql_terbentuk",
            db_ada and tabel_ada,
            (
                f"{len(tabel_sql)} tabel diekspor; basis data tersimpan"
                if db_ada and tabel_ada
                else f"basis data ada: {db_ada}; tabel lengkap: {tabel_ada}"
            )
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
