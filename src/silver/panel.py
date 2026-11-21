"""Pembentukan grid panel 38 provinsi dan laporan kelengkapan."""

import pandas as pd

PROVINSI_38 = {
    1100: "ACEH",
    1200: "SUMATERA UTARA",
    1300: "SUMATERA BARAT",
    1400: "RIAU",
    1500: "JAMBI",
    1600: "SUMATERA SELATAN",
    1700: "BENGKULU",
    1800: "LAMPUNG",
    1900: "KEP. BANGKA BELITUNG",
    2100: "KEP. RIAU",
    3100: "DKI JAKARTA",
    3200: "JAWA BARAT",
    3300: "JAWA TENGAH",
    3400: "DI YOGYAKARTA",
    3500: "JAWA TIMUR",
    3600: "BANTEN",
    5100: "BALI",
    5200: "NUSA TENGGARA BARAT",
    5300: "NUSA TENGGARA TIMUR",
    6100: "KALIMANTAN BARAT",
    6200: "KALIMANTAN TENGAH",
    6300: "KALIMANTAN SELATAN",
    6400: "KALIMANTAN TIMUR",
    6500: "KALIMANTAN UTARA",
    7100: "SULAWESI UTARA",
    7200: "SULAWESI TENGAH",
    7300: "SULAWESI SELATAN",
    7400: "SULAWESI TENGGARA",
    7500: "GORONTALO",
    7600: "SULAWESI BARAT",
    8100: "MALUKU",
    8200: "MALUKU UTARA",
    9100: "PAPUA BARAT",
    9200: "PAPUA BARAT DAYA",
    9400: "PAPUA",
    9500: "PAPUA SELATAN",
    9600: "PAPUA TENGAH",
    9700: "PAPUA PEGUNUNGAN",
}

KODE_PAPUA_LAMA = {9100, 9400}

KODE_TANPA_PADANAN = {9100, 9200, 9400, 9500, 9600, 9700}


def bentuk_grid(silver):
    """Bentuk grid seri x periode x rincian x 38 provinsi."""
    data = silver.copy()

    indonesia = data[data["wilayah_kode"] == 9999].copy()
    papua_lama = data[data["wilayah_kode"].isin(KODE_PAPUA_LAMA)].copy()

    provinsi = data[
        data["wilayah_kode"].isin(PROVINSI_38)
        & ~data["wilayah_kode"].isin(KODE_PAPUA_LAMA)
    ].copy()

    dimensi = data[["seri_kode", "periode", "rincian"]].drop_duplicates()

    wilayah = pd.DataFrame({
        "wilayah_kode": list(PROVINSI_38.keys()),
        "nama_wilayah": list(PROVINSI_38.values()),
    })

    grid = dimensi.merge(wilayah, how="cross")

    kunci = [
        "seri_kode",
        "periode",
        "rincian",
        "wilayah_kode",
        "nama_wilayah",
    ]

    observasi = provinsi[
        kunci + ["nilai", "satuan"]
    ].drop_duplicates(subset=kunci)

    panel = grid.merge(observasi, on=kunci, how="left")

    panel["status_data"] = "data_tidak_tersedia"

    panel.loc[
        panel["wilayah_kode"].isin(KODE_TANPA_PADANAN),
        "status_data"
    ] = "tidak_ada_padanan_historis"

    panel.loc[
        panel["nilai"].notna(),
        "status_data"
    ] = "tersedia"

    panel["tersedia"] = panel["nilai"].notna()

    return panel, indonesia, papua_lama


def laporan_kelengkapan(panel):
    """Laporan kelengkapan dengan pemisahan sel tanpa padanan."""
    laporan = (
        panel.groupby(["seri_kode", "periode"], as_index=False)
        .agg(
            total_sel=("tersedia", "size"),
            sel_terisi=("tersedia", "sum"),
            sel_tidak_ada_padanan=(
                "status_data",
                lambda x: (x == "tidak_ada_padanan_historis").sum(),
            ),
        )
    )

    laporan["total_padanan"] = (
        laporan["total_sel"] - laporan["sel_tidak_ada_padanan"]
    )

    laporan["sel_kosong"] = (
        laporan["total_sel"] - laporan["sel_terisi"]
    )

    laporan["sel_kosong_padanan"] = (
        laporan["total_padanan"] - laporan["sel_terisi"]
    )

    laporan["persen_terisi"] = (
        laporan["sel_terisi"] / laporan["total_padanan"] * 100
    ).round(2)

    return laporan