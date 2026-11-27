"""Rekonsiliasi Gold nasional: seri utama BPS vs seri pembanding WDI / ILOSTAT.

Masukan : DataFrame keluaran nasional.jalankan (atau data/gold/tabel_nasional.parquet).
Keluaran: data/gold/rekonsiliasi_nasional.parquet, data/interim/rekonsiliasi_metrik.json.

Aturan dasar
- Pasangan didefinisikan di PASANGAN (daftar di bawah); mengubah pasangan = mengubah daftar itu.
- Periode dipasangkan lewat TAHUN (4 digit pertama `periode`), karena seri BPS bisa semesteran
  sedangkan WDI/ILOSTAT tahunan. Label periode asli kedua sisi tetap ditampilkan.
- Periode tanpa pasangan tetap muncul (status_pasangan != 'berpasangan').
- selisih = nilai_utama - nilai_pembanding. Tidak dihapus, tidak dipaksa sama, dan dihitung
  untuk semua baris berpasangan; `selisih_bermakna` menandai apakah selisih layak dibaca
  sebagai selisih (pasangan langsung dan satuan sama).
- kategori_penjelasan hanya terisi untuk baris berpasangan. Nilainya salah satu dari:
  definisi berbeda | metode berbeda | vintage berbeda | cakupan berbeda | belum terjelaskan.
  'belum terjelaskan' dipakai bila uji arah pada registri dilanggar melampaui TOLERANSI_POIN;
  baris itu membawa `dugaan` dan `bukti`.
"""
import json
import re
from pathlib import Path

import duckdb
import pandas as pd

AKAR = Path(__file__).resolve().parents[2]
GOLD = AKAR / "data" / "gold"
INTERIM = AKAR / "data" / "interim"
MASUKAN = GOLD / "tabel_nasional.parquet"
KELUARAN = GOLD / "rekonsiliasi_nasional.parquet"
METRIK = INTERIM / "rekonsiliasi_metrik.json"

NASIONAL = 9999
TOLERANSI_POIN = 1.0      # selisih (poin) yang masih dianggap sejalan dengan uji arah

KATEGORI = ["definisi berbeda", "metode berbeda", "vintage berbeda",
            "cakupan berbeda", "belum terjelaskan"]

KOLOM_MASUKAN = ["sumber", "seri_kode", "periode", "jenis_periode", "rincian",
                 "nilai", "satuan", "_berkas_raw"]

_BUKTI_WDI_50MD = (
    "WDI SI.DST.50MD = proporsi penduduk di bawah 50% median pendapatan/konsumsi per kapita "
    "(PPP 2021, sumber PIP; berbasis survei rumah tangga, pendapatan atau konsumsi menurut "
    "survei). BPS: garis kemiskinan absolut metode kebutuhan dasar (CBN) dari pengeluaran "
    "Susenas, bukan pendapatan; dua kali setahun (Maret, September)."
)
_BUKTI_ILO_WDI = (
    "ILOSTAT SDG 1.1.1 = penduduk BEKERJA di rumah tangga di bawah garis kemiskinan "
    "internasional (metadata: pembilang pekerja miskin, penyebut total pekerja). "
    "WDI SI.POV.DDAY = seluruh penduduk di bawah garis internasional; edisi saat ini US$3,00 "
    "(PPP 2021), sebelumnya US$2,15 (PPP 2017) dengan kode seri yang sama, sehingga angka "
    "lintas edisi tidak sebanding. ILOSTAT memuat edisi US$2,15 dan edisi lebih baru; "
    "estimasi ILO untuk tahun tanpa survei bersifat model."
)
_BUKTI_KONTEKS = (
    "Panduan kelompok bagian 3: var2016 dan var1254 tidak punya padanan langsung. "
    "ILOSTAT SDG 1.3.1 = cakupan perlindungan sosial; SDG 10.4.1 = pangsa pendapatan tenaga "
    "kerja terhadap PDB. Dipakai sebagai konteks."
)


def _konteks(id_, utama, pemb):
    return dict(
        id_pasangan=id_, seri_utama=utama, sumber_utama="bps",
        seri_pembanding=pemb, sumber_pembanding="ilostat", jenis_pasangan="konteks",
        kategori="definisi berbeda", kategori_sekunder="",
        filter_utama=[], filter_pembanding=[],
        arah_harapan=0, dugaan_pelanggaran="",
        penjelasan=("Tidak ada padanan langsung: besaran yang diukur berbeda, jadi selisih "
                    "tidak bermakna dan hanya dicatat sebagai konteks."),
        bukti=_BUKTI_KONTEKS)


PASANGAN = [
    dict(id_pasangan="P1", seri_utama="var2011", sumber_utama="bps",
         seri_pembanding="SI.DST.50MD", sumber_pembanding="wdi",
         jenis_pasangan="langsung",
         kategori="definisi berbeda", kategori_sekunder="metode berbeda",
         # baris rincian 'total' bila ada; bila tidak ada, semua rincian dipakai (dicatat)
         filter_utama=[r"^total$"], filter_pembanding=[],
         arah_harapan=0, dugaan_pelanggaran="",
         penjelasan=("Garis absolut nasional (CBN, pengeluaran) vs garis relatif 50% median. "
                     "Dua konsep kemiskinan yang berbeda; angkanya tidak diharapkan sama."),
         bukti=_BUKTI_WDI_50MD),
    dict(id_pasangan="P2", seri_utama="SDG_0111_SEX_AGE_RT", sumber_utama="ilostat",
         seri_pembanding="SI.POV.DDAY", sumber_pembanding="wdi",
         jenis_pasangan="langsung",
         kategori="cakupan berbeda", kategori_sekunder="vintage berbeda; metode berbeda",
         # jenis kelamin total dan usia 15+ agar mendekati populasi WDI
         filter_utama=[r"SEX[_=]*T(?:;|$)", r"AGE[^;]*YGE15"], filter_pembanding=[],
         arah_harapan=-1,
         dugaan_pelanggaran=("Nilai ILO melebihi WDI melampaui toleransi, berlawanan dengan arah "
                             "yang diharapkan (pekerja miskin <= penduduk miskin pada garis sama). "
                             "Dugaan 1: garis berbeda, ILO dan WDI memakai edisi garis/PPP "
                             "berbeda (US$2,15 PPP 2017 vs US$3,00 PPP 2021). Dugaan 2: estimasi "
                             "model ILO pada tahun tanpa survei WDI. Dugaan 3: subpopulasi ILO "
                             "yang terpilih (rincian_utama) bukan total sex/usia 15+."),
         penjelasan=("ILO menghitung hanya penduduk bekerja usia 15+; WDI seluruh penduduk "
                     "termasuk anak dan non-pekerja. Populasi pembilang dan penyebut berbeda."),
         bukti=_BUKTI_ILO_WDI),
    _konteks("K1", "var2016", "SDG_0131_SEX_SOC_RT"),
    _konteks("K2", "var2016", "SDG_1041_NOC_RT"),
    _konteks("K3", "var1254", "SDG_0131_SEX_SOC_RT"),
    _konteks("K4", "var1254", "SDG_1041_NOC_RT"),
]


# --------------------------------------------------------------------------- persiapan
def _muat(nasional):
    if nasional is None:
        if not MASUKAN.is_file():
            raise FileNotFoundError(f"{MASUKAN} tidak ada; jalankan gold.nasional dahulu.")
        nasional = pd.read_parquet(MASUKAN)
    kurang = set(KOLOM_MASUKAN) - set(nasional.columns)
    if kurang:
        raise ValueError(f"Kolom tabel nasional tidak tersedia: {sorted(kurang)}")
    data = nasional.copy()
    if "wilayah_kode" in data.columns:
        data = data[data["wilayah_kode"] == NASIONAL]
    data["tahun"] = pd.to_numeric(data["periode"].astype(str).str[:4], errors="coerce")
    if data["tahun"].isna().any():
        raise ValueError("Ada periode yang tidak diawali tahun 4 digit.")
    data["tahun"] = data["tahun"].astype("int64")
    return data[KOLOM_MASUKAN + ["tahun"]].reset_index(drop=True)


def _ambil(data, reg, sisi, catatan):
    """Baris satu sisi pasangan. Filter rincian gagal -> pakai semua rincian dan catat."""
    sub = data[(data["seri_kode"] == reg[f"seri_{sisi}"])
               & (data["sumber"] == reg[f"sumber_{sisi}"])]
    pola = reg[f"filter_{sisi}"]
    if pola and not sub.empty:
        ok = pd.Series(True, index=sub.index)
        for p in pola:
            ok &= sub["rincian"].astype(str).str.contains(p, flags=re.I, regex=True)
        if ok.any():
            sub = sub[ok]
        else:
            catatan[(reg["id_pasangan"], sisi)] = (
                f"filter rincian {pola} tidak cocok; semua rincian {reg[f'seri_{sisi}']} dipakai")
    return sub.assign(id_pasangan=reg["id_pasangan"])


# --------------------------------------------------------------------------- inti
def bentuk_rekonsiliasi(nasional=None):
    data = _muat(nasional)
    catatan_filter = {}
    u = pd.concat([_ambil(data, r, "utama", catatan_filter) for r in PASANGAN], ignore_index=True)
    p = pd.concat([_ambil(data, r, "pembanding", catatan_filter) for r in PASANGAN],
                  ignore_index=True)

    reg = pd.DataFrame([{k: (v if not isinstance(v, list) else json.dumps(v))
                         for k, v in r.items()} for r in PASANGAN])
    reg["catatan_u"] = [catatan_filter.get((r["id_pasangan"], "utama"), "") for r in PASANGAN]
    reg["catatan_p"] = [catatan_filter.get((r["id_pasangan"], "pembanding"), "") for r in PASANGAN]

    con = duckdb.connect()
    try:
        con.register("u", u)
        con.register("p", p)
        con.register("reg", reg)
        con.execute(f"""
            CREATE TABLE hasil AS
            WITH j AS (
                SELECT coalesce(u.id_pasangan, p.id_pasangan)  AS id_pasangan,
                       coalesce(u.tahun, p.tahun)              AS tahun,
                       u.periode AS periode_utama,   p.periode AS periode_pembanding,
                       u.rincian AS rincian_utama,   p.rincian AS rincian_pembanding,
                       u.nilai   AS nilai_utama,     p.nilai   AS nilai_pembanding,
                       u.satuan  AS satuan_utama,    p.satuan  AS satuan_pembanding,
                       u.jenis_periode AS jenis_periode_utama,
                       p.jenis_periode AS jenis_periode_pembanding,
                       u._berkas_raw AS berkas_utama, p._berkas_raw AS berkas_pembanding
                FROM u FULL OUTER JOIN p
                  ON u.id_pasangan = p.id_pasangan AND u.tahun = p.tahun
            ),
            k AS (
                SELECT j.*, r.jenis_pasangan, r.seri_utama, r.seri_pembanding,
                       r.kategori AS kategori_reg, r.kategori_sekunder AS sekunder_reg,
                       r.penjelasan AS penjelasan_reg, r.bukti AS bukti_reg,
                       r.dugaan_pelanggaran, r.arah_harapan,
                       r.catatan_u, r.catatan_p,
                       CASE WHEN nilai_utama IS NULL THEN 'tanpa_utama'
                            WHEN nilai_pembanding IS NULL THEN 'tanpa_pembanding'
                            ELSE 'berpasangan' END AS status_pasangan,
                       nilai_utama - nilai_pembanding AS selisih,
                       lower(trim(satuan_utama)) = lower(trim(satuan_pembanding)) AS satuan_sebanding
                FROM j JOIN reg r USING (id_pasangan)
            ),
            m AS (
                SELECT *,
                       (status_pasangan = 'berpasangan' AND jenis_pasangan = 'langsung'
                        AND coalesce(satuan_sebanding, false)) AS selisih_bermakna
                FROM k
            ),
            v AS (
                SELECT *,
                       (selisih_bermakna AND arah_harapan <> 0
                        AND arah_harapan * selisih < -{TOLERANSI_POIN}) AS arah_dilanggar
                FROM m
            )
            SELECT id_pasangan, jenis_pasangan, seri_utama, seri_pembanding,
                   tahun, periode_utama, periode_pembanding,
                   rincian_utama, rincian_pembanding,
                   nilai_utama, nilai_pembanding, selisih, abs(selisih) AS selisih_abs,
                   satuan_utama, satuan_pembanding, satuan_sebanding, selisih_bermakna,
                   status_pasangan,
                   CASE WHEN status_pasangan <> 'berpasangan' THEN NULL
                        WHEN arah_dilanggar THEN 'belum terjelaskan'
                        ELSE kategori_reg END                                   AS kategori_penjelasan,
                   CASE WHEN status_pasangan = 'berpasangan' THEN
                        nullif(sekunder_reg, '') END                            AS kategori_sekunder,
                   CASE WHEN status_pasangan = 'berpasangan' THEN penjelasan_reg END AS penjelasan,
                   CASE WHEN arah_dilanggar THEN dugaan_pelanggaran END         AS dugaan,
                   CASE WHEN status_pasangan = 'berpasangan' THEN bukti_reg END AS bukti,
                   nullif(concat_ws('; ',
                       CASE WHEN status_pasangan = 'berpasangan'
                             AND jenis_periode_utama <> jenis_periode_pembanding
                            THEN 'granularitas periode berbeda (' || periode_utama || ' vs '
                                 || periode_pembanding || ')' END,
                       CASE WHEN status_pasangan = 'berpasangan' AND jenis_pasangan = 'langsung'
                             AND NOT coalesce(satuan_sebanding, false)
                            THEN 'satuan tidak sama' END,
                       nullif(catatan_u, ''), nullif(catatan_p, '')), '') AS catatan,
                   berkas_utama, berkas_pembanding
            FROM v
            ORDER BY id_pasangan, tahun, periode_utama, periode_pembanding
        """)
        hasil = con.execute("SELECT * FROM hasil").fetchdf()
    finally:
        con.close()
    return hasil


def hitung_metrik(rekon):
    brs = rekon[rekon["status_pasangan"] == "berpasangan"]
    bermakna = brs[brs["selisih_bermakna"]]
    med = bermakna["selisih"].median() if len(bermakna) else None
    return {
        "pasangan_rekonsiliasi": int(len(brs)),
        "pasangan_langsung": int((brs["jenis_pasangan"] == "langsung").sum()),
        "pasangan_konteks": int((brs["jenis_pasangan"] == "konteks").sum()),
        "pasangan_bermakna": int(len(bermakna)),
        "selisih_median": None if med is None or pd.isna(med) else round(float(med), 4),
        "periode_tanpa_pasangan": int((rekon["status_pasangan"] != "berpasangan").sum()),
        "belum_terjelaskan": int((brs["kategori_penjelasan"] == "belum terjelaskan").sum()),
        "per_kategori": {k: int((brs["kategori_penjelasan"] == k).sum()) for k in KATEGORI},
    }


def periksa(rekon):
    brs = rekon[rekon["status_pasangan"] == "berpasangan"]
    salah = []
    if brs["kategori_penjelasan"].isna().any():
        salah.append("baris berpasangan tanpa kategori")
    if (~brs["kategori_penjelasan"].isin(KATEGORI)).any():
        salah.append("kategori di luar lima yang diizinkan")
    bt = brs[brs["kategori_penjelasan"] == "belum terjelaskan"]
    if bt[["dugaan", "bukti"]].isna().any().any():
        salah.append("'belum terjelaskan' tanpa dugaan atau bukti")
    if not (brs["selisih"].round(9) == (brs["nilai_utama"] - brs["nilai_pembanding"]).round(9)).all():
        salah.append("selisih tidak sama dengan utama - pembanding")
    tanpa = rekon[rekon["status_pasangan"] != "berpasangan"]
    if tanpa["kategori_penjelasan"].notna().any():
        salah.append("baris tanpa pasangan diberi kategori")
    if salah:
        raise ValueError("Pemeriksaan rekonsiliasi gagal: " + "; ".join(salah))


def jalankan(nasional=None):
    """Membentuk dan menyimpan tabel rekonsiliasi nasional. Mengembalikan DataFrame."""
    rekon = bentuk_rekonsiliasi(nasional)
    periksa(rekon)
    metrik = hitung_metrik(rekon)

    GOLD.mkdir(parents=True, exist_ok=True)
    INTERIM.mkdir(parents=True, exist_ok=True)
    rekon.to_parquet(KELUARAN, index=False, engine="pyarrow")
    METRIK.write_text(json.dumps(metrik, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8", newline="\n")

    print(f"Gold rekonsiliasi: {len(rekon)} baris, {metrik['pasangan_rekonsiliasi']} berpasangan, "
          f"{metrik['periode_tanpa_pasangan']} tanpa pasangan, "
          f"{metrik['belum_terjelaskan']} belum terjelaskan, "
          f"selisih median {metrik['selisih_median']}")
    print(f"Disimpan: {KELUARAN}")
    return rekon
