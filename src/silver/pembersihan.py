"""Grid kelengkapan, duplikasi, dan penandaan patahan seri."""
import statistics
from pathlib import Path

import pandas as pd

from src.ekstraksi.bps import domain_bps

KUNCI = ["sumber", "seri_kode", "wilayah_kode", "periode", "rincian", "_berkas_raw"]
KATA_PATAHAN = [
    "patahan", "break", "perubahan definisi", "perubahan metodologi",
    "metodologi baru", "revisi definisi",
]
AMBANG_PATAHAN = 5.0


def grid_bps(df):
    domain = domain_bps()
    bps = df[df["sumber"] == "bps"]
    semua = []
    ringkas = {}
    for seri, dom in domain.items():
        sub = bps[bps["seri_kode"] == seri]
        teramati = (
            sub.groupby(["wilayah_kode", "periode", "rincian"], sort=True)
            .size()
            .rename("jumlah_observasi")
            .reset_index()
        )
        idx = pd.MultiIndex.from_product(
            [dom["wilayah"], dom["tahun"], dom["rincian"]],
            names=["wilayah_kode", "periode", "rincian"],
        )
        grid = pd.DataFrame(index=idx).reset_index()
        grid = grid.merge(teramati, on=["wilayah_kode", "periode", "rincian"], how="left")
        grid["jumlah_observasi"] = grid["jumlah_observasi"].fillna(0).astype(int)
        grid.insert(0, "seri_kode", seri)
        semua.append(grid)
        ringkas[seri] = {
            "sel_grid": int(len(grid)),
            "sel_terisi": int((grid["jumlah_observasi"] > 0).sum()),
            "sel_kosong": int((grid["jumlah_observasi"] == 0).sum()),
        }
    return pd.concat(semua, ignore_index=True), ringkas


def kelengkapan(ringkas):
    baris = []
    for seri, r in ringkas.items():
        baris.append({
            "seri_kode": seri,
            "sel_grid": r["sel_grid"],
            "sel_terisi": r["sel_terisi"],
            "sel_kosong": r["sel_kosong"],
            "persen_lengkap": round(100 * r["sel_terisi"] / r["sel_grid"], 2) if r["sel_grid"] else 0.0,
        })
    return pd.DataFrame(baris)


def cek_duplikat(df):
    kembar = df.duplicated(KUNCI, keep=False)
    return {
        "jumlah_baris_kembar": int(kembar.sum()),
        "contoh": df.loc[kembar, KUNCI].head(5).to_dict("records"),
    }


def tandai_patahan(df):
    df = df.copy()
    catatan = df["note_indicator"].fillna("").str.lower()
    df["patahan_definisi"] = False
    for kata in KATA_PATAHAN:
        df["patahan_definisi"] = df["patahan_definisi"] | catatan.str.contains(kata, regex=False)

    df["patahan_kandidat"] = False
    bps = df[df["sumber"] == "bps"]
    for (seri, rincian), sub in bps.groupby(["seri_kode", "rincian"], sort=True):
        pivot = sub.pivot_table(index="wilayah_kode", columns="periode", values="nilai", aggfunc="mean")
        periode = sorted(pivot.columns)
        perubahan = {}
        for i in range(1, len(periode)):
            delta = (pivot[periode[i]] - pivot[periode[i - 1]]).abs().dropna()
            if len(delta) > 0:
                perubahan[periode[i]] = float(delta.median())
        if len(perubahan) < 3:
            continue
        nilai = list(perubahan.values())
        median = statistics.median(nilai)
        mad = statistics.median([abs(v - median) for v in nilai])
        if mad <= 0:
            continue
        for tahun, v in perubahan.items():
            if abs(v - median) > 3 * mad and abs(v) >= AMBANG_PATAHAN:
                mask = (
                    (df["sumber"] == "bps")
                    & (df["seri_kode"] == seri)
                    & (df["rincian"] == rincian)
                    & (df["periode"] == tahun)
                )
                df.loc[mask, "patahan_kandidat"] = True
    return df


def tulis_laporan(df, grid, ringkas, duplikat, direktori):
    direktori = Path(direktori)
    direktori.mkdir(parents=True, exist_ok=True)
    grid.to_csv(direktori / "grid_bps.csv", index=False, lineterminator="\n")
    kelengkapan(ringkas).to_csv(direktori / "kelengkapan.csv", index=False, lineterminator="\n")

    baris = [
        "# Pembersihan dan kelengkapan",
        "",
        f"- Baris Silver: {len(df):,}",
        f"- Duplikat pada kunci Silver: {duplikat['jumlah_baris_kembar']}",
        f"- Outlier ditandai (z atau IQR): {int((df['outlier_z'] | df['outlier_iqr']).sum())}",
        f"- Patahan definisi terdokumentasi: {int(df['patahan_definisi'].sum())}",
        f"- Kandidat patahan (heuristik): {int(df['patahan_kandidat'].sum())}",
        "",
        "## Grid BPS",
        "",
        "| Seri | Sel grid | Terisi | Kosong | % lengkap |",
        "|---|---:|---:|---:|---:|",
    ]
    for seri, r in ringkas.items():
        persen = round(100 * r["sel_terisi"] / r["sel_grid"], 2) if r["sel_grid"] else 0.0
        baris.append(f"| {seri} | {r['sel_grid']} | {r['sel_terisi']} | {r['sel_kosong']} | {persen} |")
    baris += [
        "",
        "Kosong = sel yang tidak punya observasi di data mentah; tidak diimputasi.",
        "var1254 sengaja dibiarkan kosong (tanpa imputasi).",
    ]
    (direktori / "pembersihan.md").write_text("\n".join(baris) + "\n", encoding="utf-8", newline="\n")
