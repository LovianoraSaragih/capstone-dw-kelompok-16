"""Profil ketersediaan dan kesebandingan seri pembanding Stage 2."""
from pathlib import Path

import pandas as pd

AKAR = Path(__file__).resolve().parents[2]
REPORTS = AKAR / "reports"

SERI_UTAMA = ["var2011", "var2016", "var1254"]
SERI_PEMBANDING = [
    "SDG_0111_SEX_AGE_RT",
    "SDG_0131_SEX_SOC_RT",
    "SDG_1041_NOC_RT",
    "WSI.DST.50MD",
    "SI.POV.DDAY",
]

KEPUTUSAN = {
    ("SI.DST.50MD", "var2011"): (
        "Kandidat konsep",
        "Sama-sama mengukur proporsi penduduk di bawah 50% median pendapatan. "
        "Definisi, populasi, metodologi, dan tahun perlu divalidasi."
    ),
    ("SI.POV.DDAY", "var2011"): (
        "Kontekstual",
        "Sama-sama berkaitan dengan kemiskinan, tetapi ambang $3 per hari PPP "
        "berbeda dengan 50% median pendapatan."
    ),
    ("SDG_0111_SEX_AGE_RT", "var2011"): (
        "Kontekstual",
        "Kemiskinan pekerja berdasarkan kelompok umur dan jenis kelamin berbeda "
        "dari indikator proporsi penduduk berpendapatan di bawah 50% median."
    ),
    ("SDG_0131_SEX_SOC_RT", "var2016"): (
        "Kontekstual",
        "Cakupan perlindungan sosial tidak sama dengan akses terhadap layanan dasar."
    ),
    ("SDG_1041_NOC_RT", "var2011"): (
        "Kontekstual",
        "Porsi pendapatan tenaga kerja berkaitan dengan distribusi ekonomi, "
        "tetapi bukan ukuran langsung penduduk di bawah 50% median pendapatan."
    ),
}


def _tahun(sub):
    return sorted(sub.loc[sub["nilai"].notna(), "periode"].astype(int).unique().tolist())


def _profil(df):
    baris = []
    for (sumber, seri, rincian), sub in df.groupby(
        ["sumber", "seri_kode", "rincian"], sort=True
    ):
        tahun = _tahun(sub)
        baris.append({
            "sumber": sumber,
            "seri_kode": seri,
            "rincian": rincian,
            "jumlah_observasi": int(sub["nilai"].notna().sum()),
            "jumlah_wilayah": int(sub["wilayah_kode"].nunique()),
            "tahun_tersedia": ",".join(map(str, tahun)),
            "tahun_awal": min(tahun) if tahun else None,
            "tahun_akhir": max(tahun) if tahun else None,
            "satuan": ",".join(sorted(sub["satuan"].dropna().astype(str).unique())),
        })
    return pd.DataFrame(baris)


def _ketersediaan(df):
    sub = df[df["nilai"].notna()]
    return (
        sub.groupby(
            ["sumber", "seri_kode", "rincian", "periode"], sort=True
        )
        .agg(
            jumlah_wilayah=("wilayah_kode", "nunique"),
            jumlah_observasi=("nilai", "count"),
            satuan=("satuan", lambda x: ",".join(sorted(x.dropna().astype(str).unique()))),
        )
        .reset_index()
        .sort_values(["seri_kode", "rincian", "periode"])
    )


def _kesebandingan(df):
    nasional = df[(df["wilayah_kode"] == 9999) & df["nilai"].notna()]
    baris = []

    for pembanding in SERI_PEMBANDING:
        comp = nasional[nasional["seri_kode"] == pembanding]
        tahun_comp = set(comp["periode"].astype(int).unique())

        for utama in SERI_UTAMA:
            main = nasional[nasional["seri_kode"] == utama]
            tahun_main = set(main["periode"].astype(int).unique())
            overlap = sorted(tahun_comp & tahun_main)

            status, alasan = KEPUTUSAN.get(
                (pembanding, utama),
                (
                    "Belum ditetapkan sebagai pembanding",
                    "Pasangan ini belum dinilai secara khusus berdasarkan "
                    "kesamaan konsep, definisi, populasi, dan metode. "
                    "Overlap tahun hanya menunjukkan kesamaan periode."
                ),
            )

            baris.append({
                "seri_pembanding": pembanding,
                "seri_utama_bps": utama,
                "tahun_pembanding": ",".join(map(str, sorted(tahun_comp))),
                "tahun_utama": ",".join(map(str, sorted(tahun_main))),
                "tahun_overlap": ",".join(map(str, overlap)),
                "jumlah_tahun_overlap": len(overlap),
                "status": status,
                "dasar_pemilihan": alasan,
                "cakupan": "Nasional (wilayah_kode 9999)",
            })

    return pd.DataFrame(baris)


def _markdown(profil, kesebandingan):
    isi = [
        "# Profil dan Kesebandingan Seri Pembanding",
        "",
        "## Metode",
        "",
        "Profil dibuat dari data Silver dengan nilai yang tidak kosong. "
        "Ketersediaan dicatat berdasarkan seri, rincian, dan periode aktual. "
        "Overlap dihitung dari tahun yang benar-benar tersedia pada data nasional "
        "(wilayah_kode 9999), bukan hanya rentang tahun awal dan akhir.",
        "",
        "Overlap tahun tidak otomatis berarti dua indikator sebanding. "
        "Penentuan kandidat mempertimbangkan konsep dan definisi indikator.",
        "",
        "## Profil seri pembanding",
        "",
        "| Seri | Rincian | Observasi | Tahun tersedia | Satuan |",
        "|---|---|---:|---|---|",
    ]
    for _, r in profil.iterrows():
        isi.append(
            f"| {r['seri_kode']} | {r['rincian']} | {r['jumlah_observasi']} | "
            f"{r['tahun_tersedia']} | {r['satuan']} |"
        )

    isi += [
        "",
        "## Penilaian kesebandingan dan overlap",
        "",
        "| Pembanding | Seri utama | Overlap | Jumlah | Status | Dasar |",
        "|---|---|---|---:|---|---|",
    ]
    for _, r in kesebandingan.iterrows():
        isi.append(
            f"| {r['seri_pembanding']} | {r['seri_utama_bps']} | "
            f"{r['tahun_overlap'] or '-'} | {r['jumlah_tahun_overlap']} | "
            f"{r['status']} | {r['dasar_pemilihan']} |"
        )

    isi += [
        "",
        "## Kandidat rincian yang sebanding",
        "",
        "- **SI.DST.50MD (rincian total) terhadap var2011** ditetapkan sebagai "
        "kandidat konsep utama. Keduanya mengukur proporsi penduduk dengan "
        "pendapatan di bawah 50% median pendapatan.",
        "- Pemilihan kandidat didasarkan pada kesamaan konsep indikator, bukan "
        "semata-mata pada overlap tahun. Kesamaan definisi operasional, "
        "populasi, sumber, metodologi, dan cakupan periode masih perlu "
        "divalidasi sebelum keduanya digunakan dalam perbandingan langsung.",
        "- Seri lain dipertahankan sebagai konteks karena berkaitan dengan "
        "kemiskinan, distribusi pendapatan, ketenagakerjaan, atau perlindungan "
        "sosial, tetapi memiliki konsep atau batas pengukuran yang berbeda.",
        "- Berdasarkan penilaian konsep saat ini, belum ditetapkan kandidat "
        "pembanding langsung untuk var2016 dan var1254.",
        "",
        "## Batasan",
        "",
        "- Seri pembanding ILOSTAT dan WDI tersedia pada tingkat nasional; "
        "tidak digunakan untuk membandingkan antarprovinsi.",
        "- Rincian ILOSTAT dipertahankan dalam kode aslinya karena label dimensi "
        "belum seluruhnya tersedia pada data snapshot.",
        "- Overlap pada tabel kesebandingan dihitung pada tingkat seri dari "
        "gabungan tahun yang tersedia pada rincian nasional. Tahun overlap tidak "
        "menjamin setiap rincian tersedia pada tahun yang sama.",
        "- Tabel ketersediaan lengkap per seri, rincian, dan periode dapat dilihat "
        "pada [ketersediaan_pembanding.csv](ketersediaan_pembanding.csv).",
        "-Profil rincian dapat dilihat pada [profil_seri_pembanding.csv](profil_seri_pembanding.csv).",
        "- Overlap menunjukkan kesamaan periode, bukan kesamaan metodologi.",
        "- Data kosong tidak diisi atau diimputasi.",
        "",
    ]
    return "n".join(isi)


def jalankan(df=None):
    """Buat laporan Stage 2 secara terpisah dari pipeline utama."""
    if df is None:
        df = pd.read_parquet(AKAR / "data" / "silver" / "silver.parquet")

    df = df[df["seri_kode"].isin(SERI_PEMBANDING + SERI_UTAMA)].copy()
    profil = _profil(df[df["seri_kode"].isin(SERI_PEMBANDING)])
    tersedia = _ketersediaan(df[df["seri_kode"].isin(SERI_PEMBANDING)])
    kesebandingan = _kesebandingan(df)

    REPORTS.mkdir(parents=True, exist_ok=True)
    profil.to_csv(REPORTS / "profil_seri_pembanding.csv", index=False, lineterminator=chr(10))
    tersedia.to_csv(REPORTS / "ketersediaan_pembanding.csv", index=False, lineterminator=chr(10))
    kesebandingan.to_csv(REPORTS / "kesebandingan_pembanding.csv", index=False, lineterminator=chr(10))
    (REPORTS / "profil_pembanding.md").write_text(
        _markdown(profil, kesebandingan), encoding="utf-8", newline=""
    )

    print(f"Profil pembanding: {len(profil)} rincian")
    print(f"Ketersediaan: {len(tersedia)} baris seri-rincian-periode")
    print(f"Kesebandingan: {len(kesebandingan)} pasangan seri")
    print(f"Laporan tersimpan di {REPORTS}")

    return {
        "profil": profil,
        "ketersediaan": tersedia,
        "kesebandingan": kesebandingan,
    }


if __name__ == "__main__":
    jalankan()
