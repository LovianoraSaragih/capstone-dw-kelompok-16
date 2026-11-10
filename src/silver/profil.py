"""Profil deskriptif, deteksi anomali, dan grafik per seri."""
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


def statistik(df):
    baris = []
    for (sumber, seri, rincian), sub in df.groupby(["sumber", "seri_kode", "rincian"], sort=True):
        baris.append({
            "sumber": sumber,
            "seri_kode": seri,
            "rincian": rincian,
            "n": int(len(sub)),
            "n_wilayah": int(sub["wilayah_kode"].nunique()),
            "n_periode": int(sub["periode"].nunique()),
            "periode_min": sub["periode"].min(),
            "periode_max": sub["periode"].max(),
            "nilai_min": float(sub["nilai"].min()),
            "nilai_max": float(sub["nilai"].max()),
            "nilai_mean": round(float(sub["nilai"].mean()), 4),
            "nilai_median": float(sub["nilai"].median()),
            "nilai_std": round(float(sub["nilai"].std(ddof=0)), 4),
            "satuan": ",".join(sorted(sub["satuan"].unique())),
        })
    return pd.DataFrame(baris)


def matriks_ketersediaan(df):
    return (
        df.groupby(["sumber", "seri_kode", "rincian", "periode"], sort=True)
        .agg(n_wilayah=("wilayah_kode", "nunique"), n_observasi=("nilai", "size"))
        .reset_index()
    )


def tandai_outlier(df):
    df = df.copy()
    df["outlier_z"] = False
    df["outlier_iqr"] = False
    for _, sub in df.groupby(["sumber", "seri_kode", "rincian"], sort=True):
        nilai = sub["nilai"]
        if len(nilai) < 4:
            continue
        std = float(nilai.std(ddof=0))
        if std > 0:
            z = (nilai - nilai.mean()).abs() / std
            df.loc[sub.index, "outlier_z"] = z > 3
        q1 = float(nilai.quantile(0.25))
        q3 = float(nilai.quantile(0.75))
        iqr = q3 - q1
        if iqr > 0:
            df.loc[sub.index, "outlier_iqr"] = (nilai < q1 - 1.5 * iqr) | (nilai > q3 + 1.5 * iqr)
    return df


def grafik(df, direktori):
    direktori = Path(direktori)
    direktori.mkdir(parents=True, exist_ok=True)
    for (sumber, seri), sub in df.groupby(["sumber", "seri_kode"], sort=True):
        fig, ax = plt.subplots(figsize=(10, 5))
        for rincian, bagian in sub.groupby("rincian", sort=True):
            agg = bagian.groupby("periode")["nilai"].mean().sort_index()
            ax.plot(agg.index, agg.values, marker="o", label=rincian)
        ax.set_title(f"{sumber} - {seri}")
        ax.set_xlabel("periode")
        ax.set_ylabel("nilai")
        ax.legend(fontsize=7)
        fig.tight_layout()
        fig.savefig(direktori / f"deret_{sumber}_{seri}.png", dpi=100)
        plt.close(fig)

        fig, ax = plt.subplots(figsize=(10, 5))
        labels = []
        data = []
        for rincian, bagian in sub.groupby("rincian", sort=True):
            labels.append(rincian)
            data.append(bagian["nilai"].to_numpy())
        ax.boxplot(data, tick_labels=labels)
        ax.set_title(f"Boxplot {sumber} - {seri}")
        ax.tick_params(axis="x", labelrotation=45)
        fig.tight_layout()
        fig.savefig(direktori / f"boxplot_{sumber}_{seri}.png", dpi=100)
        plt.close(fig)


def tulis_laporan(df, direktori):
    direktori = Path(direktori)
    direktori.mkdir(parents=True, exist_ok=True)
    statistik(df).to_csv(direktori / "profil_deskriptif.csv", index=False, lineterminator="\n")
    matriks_ketersediaan(df).to_csv(direktori / "matriks_ketersediaan.csv", index=False, lineterminator="\n")
    anomali = df.loc[df["outlier_z"] | df["outlier_iqr"], [
        "sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode",
        "rincian", "nilai", "outlier_z", "outlier_iqr",
    ]]
    anomali.to_csv(direktori / "profil_anomali.csv", index=False, lineterminator="\n")
    grafik(df, direktori / "gambar")
