"""Kolom turunan panel Gold untuk analisis ketimpangan, layanan dasar, dan keuangan daerah."""

import pandas as pd

KOMPONEN_LAYANAN = [
    "var2016__air_minum",
    "var2016__sanitasi",
    "var2016__fasilitas_kesehatan",
    "var2016__mobilitas",
]

KOLOM_ASLI = [
    "var1254__total",
    "var2011__total",
    "var2016__air_minum",
    "var2016__fasilitas_kesehatan",
    "var2016__mobilitas",
    "var2016__sanitasi",
]

DESKRIPSI_TURUNAN = [
    {
        "kolom": "layanan_dasar_indeks",
        "jenis": "analisis",
        "rumus": "rata-rata komponen var2016 yang tidak kosong: air_minum, sanitasi, fasilitas_kesehatan, mobilitas",
        "input": "var2016__air_minum, var2016__sanitasi, var2016__fasilitas_kesehatan, var2016__mobilitas",
        "alasan": "Ringkasan akses layanan dasar dalam satu angka 0-100; mobilitas tidak diimputasi sehingga hanya komponen tersedia yang dihitung.",
    },
    {
        "kolom": "layanan_dasar_n_komponen",
        "jenis": "analisis",
        "rumus": "jumlah komponen var2016 yang tidak kosong pada baris tersebut",
        "input": "var2016__air_minum, var2016__sanitasi, var2016__fasilitas_kesehatan, var2016__mobilitas",
        "alasan": "Menunjukkan berapa komponen yang benar-benar menyusun indeks; nilai 3 berarti mobilitas kosong.",
    },
    {
        "kolom": "layanan_dasar_terendah",
        "jenis": "analisis",
        "rumus": "nilai minimum komponen var2016 yang tidak kosong",
        "input": "var2016__air_minum, var2016__sanitasi, var2016__fasilitas_kesehatan, var2016__mobilitas",
        "alasan": "Mengidentifikasi jenis layanan dasar yang paling lemah di suatu provinsi pada tahun tertentu.",
    },
    {
        "kolom": "layanan_dasar_rentang",
        "jenis": "analisis",
        "rumus": "maksimum komponen dikurangi minimum komponen; kosong bila komponen tersedia kurang dari dua",
        "input": "var2016__air_minum, var2016__sanitasi, var2016__fasilitas_kesehatan, var2016__mobilitas",
        "alasan": "Mengukur ketimpangan antarjenis layanan dasar di dalam satu provinsi.",
    },
    {
        "kolom": "var2011_nasional",
        "jenis": "pendukung",
        "rumus": "nilai var2011 total pada wilayah_kode 9999 untuk periode yang sama",
        "input": "Silver bps var2011 rincian total wilayah 9999",
        "alasan": "Pembanding nasional resmi untuk menghitung selisih provinsi tanpa membuat rata-rata provinsi baru.",
    },
    {
        "kolom": "var1254_nasional",
        "jenis": "pendukung",
        "rumus": "nilai var1254 total pada wilayah_kode 9999 untuk periode yang sama",
        "input": "Silver bps var1254 rincian total wilayah 9999",
        "alasan": "Pembanding nasional resmi untuk rasio pendapatan pemerintah terhadap PDB.",
    },
    {
        "kolom": "layanan_dasar_nasional",
        "jenis": "pendukung",
        "rumus": "rata-rata komponen var2016 yang tidak kosong pada wilayah_kode 9999 untuk periode yang sama",
        "input": "Silver bps var2016 wilayah 9999",
        "alasan": "Pembanding nasional untuk indeks layanan dasar dengan formula yang sama seperti provinsi.",
    },
    {
        "kolom": "layanan_dasar_n_komponen_nasional",
        "jenis": "pendukung",
        "rumus": "jumlah komponen var2016 yang tidak kosong pada wilayah_kode 9999 untuk periode yang sama",
        "input": "Silver bps var2016 wilayah 9999",
        "alasan": "Menunjukkan jumlah komponen penyusun indeks nasional.",
    },
    {
        "kolom": "var2011_gap_nasional",
        "jenis": "analisis",
        "rumus": "var2011__total provinsi dikurangi var2011_nasional pada periode yang sama",
        "input": "var2011__total, var2011_nasional",
        "alasan": "Selisih proporsi penduduk di bawah 50 persen median terhadap nasional; nilai positif berarti ketimpangan lebih tinggi dari nasional.",
    },
    {
        "kolom": "layanan_dasar_gap_nasional",
        "jenis": "analisis",
        "rumus": "layanan_dasar_indeks provinsi dikurangi layanan_dasar_nasional pada periode yang sama",
        "input": "layanan_dasar_indeks, layanan_dasar_nasional",
        "alasan": "Selisih akses layanan dasar terhadap nasional; nilai negatif berarti tertinggal dari nasional.",
    },
    {
        "kolom": "var1254_gap_nasional",
        "jenis": "analisis",
        "rumus": "var1254__total provinsi dikurangi var1254_nasional pada periode yang sama",
        "input": "var1254__total, var1254_nasional",
        "alasan": "Selisih rasio pendapatan pemerintah terhadap PDB dari nasional; menggambarkan kapasitas fiskal relatif.",
    },
    {
        "kolom": "perubahan_layanan_dasar",
        "jenis": "analisis",
        "rumus": "layanan_dasar_indeks tahun t dikurangi tahun t-1; kosong bila t-1 tidak tersedia",
        "input": "layanan_dasar_indeks, periode",
        "alasan": "Mengukur arah dan besar perubahan akses layanan dasar antartahun berurutan tanpa mencampur loncatan tahun.",
    },
    {
        "kolom": "perubahan_var2011",
        "jenis": "analisis",
        "rumus": "var2011__total tahun t dikurangi tahun t-1; kosong bila t-1 tidak tersedia",
        "input": "var2011__total, periode",
        "alasan": "Mengukur perubahan relatif kemiskinan terhadap median antartahun berurutan.",
    },
    {
        "kolom": "perubahan_var1254",
        "jenis": "analisis",
        "rumus": "var1254__total tahun t dikurangi tahun t-1; kosong bila t-1 tidak tersedia",
        "input": "var1254__total, periode",
        "alasan": "Mengukur perubahan rasio pendapatan pemerintah terhadap PDB antartahun berurutan.",
    },
    {
        "kolom": "peringkat_var2011",
        "jenis": "analisis",
        "rumus": "peringkat var2011__total lintas provinsi per periode; 1 = paling rendah",
        "input": "var2011__total, periode",
        "alasan": "Memudahkan analisis ketimpangan lintas provinsi pada tahun yang sama.",
    },
    {
        "kolom": "peringkat_layanan_dasar",
        "jenis": "analisis",
        "rumus": "peringkat layanan_dasar_indeks lintas provinsi per periode; 1 = paling tinggi",
        "input": "layanan_dasar_indeks, periode",
        "alasan": "Memudahkan analisis ketimpangan akses layanan dasar lintas provinsi pada tahun yang sama.",
    },
]

KOLOM_TURUNAN = [d["kolom"] for d in DESKRIPSI_TURUNAN]


def _benchmark_nasional(silver):
    bps = silver[
        (silver["sumber"] == "bps")
        & (silver["wilayah_kode"] == 9999)
    ].copy()

    v2011 = bps[
        (bps["seri_kode"] == "var2011")
        & (bps["rincian"] == "total")
    ][["periode", "nilai"]].rename(columns={"nilai": "var2011_nasional"})

    v1254 = bps[
        (bps["seri_kode"] == "var1254")
        & (bps["rincian"] == "total")
    ][["periode", "nilai"]].rename(columns={"nilai": "var1254_nasional"})

    v2016 = bps[
        (bps["seri_kode"] == "var2016")
        & (bps["rincian"].isin(["air_minum", "sanitasi", "fasilitas_kesehatan", "mobilitas"]))
    ]

    layanan = (
        v2016.groupby("periode")["nilai"]
        .agg(
            layanan_dasar_nasional="mean",
            layanan_dasar_n_komponen_nasional="count",
        )
        .reset_index()
    )

    return (
        v2011.merge(v1254, on="periode", how="outer")
        .merge(layanan, on="periode", how="outer")
    )


def tambah_kolom_turunan(panel, silver):
    """Menambahkan kolom turunan tanpa mengganti kolom nilai asli."""
    p = panel.copy()

    for kol in KOMPONEN_LAYANAN:
        if kol not in p.columns:
            p[kol] = float("nan")

    komponen = p[KOMPONEN_LAYANAN]
    p["layanan_dasar_n_komponen"] = komponen.notna().sum(axis=1).astype("int64")
    p["layanan_dasar_indeks"] = komponen.mean(axis=1, skipna=True)
    p["layanan_dasar_terendah"] = komponen.min(axis=1, skipna=True)

    maksimum = komponen.max(axis=1, skipna=True)
    p["layanan_dasar_rentang"] = (
        maksimum - p["layanan_dasar_terendah"]
    ).where(p["layanan_dasar_n_komponen"] >= 2)

    benchmark = _benchmark_nasional(silver)
    p = p.merge(benchmark, on="periode", how="left")

    p["var2011_gap_nasional"] = p["var2011__total"] - p["var2011_nasional"]
    p["layanan_dasar_gap_nasional"] = p["layanan_dasar_indeks"] - p["layanan_dasar_nasional"]
    p["var1254_gap_nasional"] = p["var1254__total"] - p["var1254_nasional"]

    p = p.sort_values(["wilayah_kode", "periode"]).reset_index(drop=True)
    p["_tahun"] = pd.to_numeric(p["periode"].astype(str).str[:4], errors="coerce")

    for kol, nama in [
        ("layanan_dasar_indeks", "perubahan_layanan_dasar"),
        ("var2011__total", "perubahan_var2011"),
        ("var1254__total", "perubahan_var1254"),
    ]:
        sebelumnya = p.groupby("wilayah_kode")[kol].shift(1)
        tahun_sebelumnya = p.groupby("wilayah_kode")["_tahun"].shift(1)
        p[nama] = (p[kol] - sebelumnya).where((p["_tahun"] - tahun_sebelumnya) == 1)

    p["peringkat_var2011"] = (
        p.groupby("periode")["var2011__total"]
        .rank(method="min", ascending=True)
        .astype("Int64")
    )
    p["peringkat_layanan_dasar"] = (
        p.groupby("periode")["layanan_dasar_indeks"]
        .rank(method="min", ascending=False)
        .astype("Int64")
    )

    p = p.drop(columns=["_tahun"])
    urutan = [c for c in p.columns if c not in KOLOM_TURUNAN]
    urutan += [c for c in KOLOM_TURUNAN if c in p.columns]
    return p[urutan]
