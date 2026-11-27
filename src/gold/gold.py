"""Tahap Gold: Silver (13 kolom, panjang) -> model analitik berbasis DuckDB.

Dipanggil dari pipeline.py:  gold.jalankan(hasil["silver"])

Keluaran (data/gold/, juga disimpan sebagai tabel di data/gold/gold.duckdb):
    dim_wilayah       satu baris per wilayah_kode (9999 = nasional)
    dim_seri          satu baris per (sumber, seri_kode, rincian) + nama kolom panel
    dim_waktu         satu baris per periode
    fakta_observasi   Silver tanpa duplikat lintas berkas + penanda kualitas per baris
    panel_tahunan     panjang: (seri_id, wilayah_kode, tahun) -> nilai
    panel_lebar       lebar: (wilayah_kode, tahun) x satu kolom per seri
    gold_metrik       angka rekonsiliasi Silver -> Gold

Prinsip yang diwarisi dari Silver: tidak ada imputasi. Sel yang tidak teramati tetap
tidak ada (panel_lebar memakai NULL, bukan 0 atau interpolasi).
"""
import json
import re
from pathlib import Path

import duckdb

SILVER_PARQUET = Path("data/silver/silver.parquet")
GOLD_DIR = Path("data/gold")
GOLD_DB = GOLD_DIR / "gold.duckdb"
INTERIM_DIR = Path("data/interim")

KOLOM_SILVER = ["sumber", "seri_kode", "wilayah_kode", "nama_wilayah", "periode",
                "jenis_periode", "rincian", "nilai", "satuan", "_berkas_raw",
                "_sha256_raw", "obs_status", "note_indicator"]

# Sama dengan pembersihan.py / profil.py (lihat laporan Silver, bagian 6 dan 7)
AMBANG_PATAHAN = 5.0
POLA_PATAHAN = ("patahan|break|perubahan definisi|perubahan metodologi|"
                "metodologi baru|revisi definisi")
MIN_BARIS_OUTLIER = 4
MAKS_KOLOM_LEBAR = 500          # pengaman bila rincian ILOSTAT meledak

TABEL_KELUARAN = ["dim_wilayah", "dim_seri", "dim_waktu", "fakta_observasi",
                  "panel_tahunan", "panel_lebar", "gold_metrik"]


# --------------------------------------------------------------------------- sumber
def _sumber_silver(silver_hasil):
    """Tentukan sumber Silver. Menerima DataFrame, jalur berkas, dict berisi jalur,
    atau None (pakai data/silver/silver.parquet)."""
    if hasattr(silver_hasil, "columns"):                      # DataFrame
        return silver_hasil
    kandidat = silver_hasil
    if isinstance(silver_hasil, dict):
        kandidat = next((silver_hasil[k] for k in ("parquet", "path", "jalur", "berkas", "silver")
                         if k in silver_hasil), None)
    if isinstance(kandidat, (str, Path)) and Path(kandidat).is_file():
        return Path(kandidat)
    if SILVER_PARQUET.is_file():
        return SILVER_PARQUET
    raise FileNotFoundError(f"Silver tidak ditemukan: {SILVER_PARQUET}. Jalankan tahap silver dahulu.")


def _muat_silver(con, sumber):
    if isinstance(sumber, Path):
        lit = str(sumber).replace("'", "''")
        con.execute(f"CREATE VIEW silver_src AS SELECT * FROM read_parquet('{lit}')")
    else:
        con.register("silver_df", sumber)
        con.execute("CREATE VIEW silver_src AS SELECT * FROM silver_df")
    ada = {r[0] for r in con.execute("DESCRIBE silver_src").fetchall()}
    kurang = [k for k in KOLOM_SILVER if k not in ada]
    if kurang:
        raise ValueError(f"Silver melanggar kontrak 13 kolom; kolom hilang: {kurang}")


# --------------------------------------------------------------------------- helper
def _slug(teks, maks=40):
    s = re.sub(r"[^0-9a-zA-Z]+", "_", str(teks).lower()).strip("_")
    return (s[:maks] or "x")


def _q(ident):
    return '"' + ident.replace('"', '""') + '"'


def _skalar(con, sql):
    return con.execute(sql).fetchone()[0]


# --------------------------------------------------------------------------- tahap SQL
def _staging(con):
    """Buang duplikat lintas berkas (kunci alami tanpa _berkas_raw), simpan snapshot terbaru."""
    con.execute("""
        CREATE TABLE stg_observasi AS
        SELECT *,
               count(*) OVER k AS n_berkas_sama
        FROM (
            SELECT sumber, seri_kode, CAST(wilayah_kode AS BIGINT) AS wilayah_kode,
                   nama_wilayah, periode, jenis_periode, rincian,
                   CAST(nilai AS DOUBLE) AS nilai, satuan, _berkas_raw, _sha256_raw,
                   coalesce(obs_status, '') AS obs_status,
                   coalesce(note_indicator, '') AS note_indicator,
                   TRY_CAST(left(periode, 4) AS INTEGER) AS tahun
            FROM silver_src
        )
        WINDOW k AS (PARTITION BY sumber, seri_kode, wilayah_kode, periode, rincian)
        QUALIFY row_number() OVER (
                    PARTITION BY sumber, seri_kode, wilayah_kode, periode, rincian
                    ORDER BY _berkas_raw DESC) = 1
    """)
    salah = _skalar(con, "SELECT count(*) FROM stg_observasi WHERE tahun IS NULL")
    if salah:
        raise ValueError(f"{salah} baris dengan periode yang tidak diawali tahun 4 digit.")


def _dimensi(con):
    con.execute("""
        CREATE TABLE dim_wilayah AS
        SELECT wilayah_kode,
               mode(nama_wilayah)                                  AS nama_wilayah,
               CASE WHEN wilayah_kode = 9999 THEN 'nasional' ELSE 'subnasional' END AS tingkat,
               wilayah_kode = 9999                                 AS is_nasional,
               string_agg(DISTINCT sumber, ',' ORDER BY sumber)    AS sumber_tersedia
        FROM stg_observasi
        GROUP BY wilayah_kode
        ORDER BY wilayah_kode
    """)
    con.execute("""
        CREATE TABLE dim_waktu AS
        SELECT periode,
               any_value(tahun)          AS tahun,
               any_value(jenis_periode)  AS jenis_periode,
               CASE any_value(jenis_periode) WHEN 'tahun' THEN NULL
                    ELSE regexp_extract(periode, '^[0-9]{4}-(.+)$', 1) END AS sub_periode
        FROM stg_observasi
        GROUP BY periode
        ORDER BY periode
    """)
    con.execute("""
        CREATE TABLE dim_seri AS
        SELECT row_number() OVER (ORDER BY sumber, seri_kode, rincian) AS seri_id,
               sumber, seri_kode, rincian,
               string_agg(DISTINCT satuan, ',' ORDER BY satuan)        AS satuan,
               string_agg(DISTINCT jenis_periode, ',' ORDER BY jenis_periode) AS jenis_periode,
               min(periode) AS periode_min, max(periode) AS periode_max,
               count(DISTINCT wilayah_kode) AS n_wilayah,
               count(DISTINCT periode)      AS n_periode,
               count(*)                     AS n_observasi
        FROM stg_observasi
        GROUP BY sumber, seri_kode, rincian
    """)
    # nama kolom panel lebar yang stabil dan unik
    baris = con.execute("SELECT seri_id, seri_kode, rincian FROM dim_seri ORDER BY seri_id").fetchall()
    dipakai, nama = set(), {}
    for sid, kode, rinci in baris:
        n = f"{_slug(kode)}__{_slug(rinci)}"
        if n in dipakai:
            n = f"{n}_{sid}"
        dipakai.add(n)
        nama[sid] = n
    con.execute("ALTER TABLE dim_seri ADD COLUMN kolom_panel VARCHAR")
    con.executemany("UPDATE dim_seri SET kolom_panel = ? WHERE seri_id = ?",
                    [(v, k) for k, v in nama.items()])
    return nama


def _patahan_kandidat(con):
    """Heuristik patahan BPS: median lintas wilayah dari |selisih| antarperiode,
    lalu penanda 3*MAD dan ambang mutlak (padanan pembersihan.py)."""
    con.execute(f"""
        CREATE TABLE _patahan_kandidat AS
        WITH rata AS (
            SELECT seri_kode, rincian, wilayah_kode, periode, avg(nilai) AS nilai
            FROM stg_observasi WHERE sumber = 'bps' GROUP BY ALL
        ),
        urut AS (
            SELECT seri_kode, rincian, periode,
                   row_number() OVER (PARTITION BY seri_kode, rincian ORDER BY periode) AS r
            FROM (SELECT DISTINCT seri_kode, rincian, periode FROM rata)
        ),
        delta AS (
            SELECT a.seri_kode, a.rincian, ua.periode, abs(a.nilai - b.nilai) AS d
            FROM rata a
            JOIN urut ua ON ua.seri_kode = a.seri_kode AND ua.rincian = a.rincian
                        AND ua.periode = a.periode
            JOIN urut ub ON ub.seri_kode = ua.seri_kode AND ub.rincian = ua.rincian
                        AND ub.r = ua.r - 1
            JOIN rata b  ON b.seri_kode = a.seri_kode AND b.rincian = a.rincian
                        AND b.wilayah_kode = a.wilayah_kode AND b.periode = ub.periode
        ),
        perub AS (SELECT seri_kode, rincian, periode, median(d) AS v FROM delta GROUP BY ALL),
        stat  AS (SELECT seri_kode, rincian, median(v) AS med
                  FROM perub GROUP BY seri_kode, rincian HAVING count(*) >= 3),
        mad   AS (SELECT p.seri_kode, p.rincian, s.med, median(abs(p.v - s.med)) AS mad
                  FROM perub p JOIN stat s USING (seri_kode, rincian)
                  GROUP BY p.seri_kode, p.rincian, s.med)
        SELECT p.seri_kode, p.rincian, p.periode, p.v AS perubahan_median
        FROM perub p JOIN mad m USING (seri_kode, rincian)
        WHERE m.mad > 0 AND abs(p.v - m.med) > 3 * m.mad AND abs(p.v) >= {AMBANG_PATAHAN}
    """)


def _fakta(con):
    _patahan_kandidat(con)
    con.execute(f"""
        CREATE TABLE fakta_observasi AS
        WITH s AS (
            SELECT *,
                   count(*)                   OVER w AS n,
                   avg(nilai)                 OVER w AS mu,
                   stddev_pop(nilai)          OVER w AS sd,
                   quantile_cont(nilai, 0.25) OVER w AS q1,
                   quantile_cont(nilai, 0.75) OVER w AS q3
            FROM stg_observasi
            WINDOW w AS (PARTITION BY sumber, seri_kode, rincian)
        ),
        f AS (
            SELECT s.*,
                   (n >= {MIN_BARIS_OUTLIER} AND sd > 0 AND abs(nilai - mu) / sd > 3) AS outlier_z,
                   (n >= {MIN_BARIS_OUTLIER} AND q3 > q1
                    AND (nilai < q1 - 1.5 * (q3 - q1) OR nilai > q3 + 1.5 * (q3 - q1))) AS outlier_iqr,
                   regexp_matches(lower(note_indicator), '{POLA_PATAHAN}') AS patahan_definisi,
                   (k.periode IS NOT NULL)                                  AS patahan_kandidat
            FROM s
            LEFT JOIN _patahan_kandidat k
                   ON s.sumber = 'bps' AND k.seri_kode = s.seri_kode
                  AND k.rincian = s.rincian AND k.periode = s.periode
        )
        SELECT row_number() OVER (ORDER BY f.sumber, f.seri_kode, f.rincian,
                                           f.wilayah_kode, f.periode)       AS obs_id,
               d.seri_id, f.sumber, f.seri_kode, f.rincian,
               f.wilayah_kode, f.nama_wilayah, f.wilayah_kode = 9999        AS is_nasional,
               f.periode, f.tahun, f.jenis_periode,
               f.nilai, f.satuan, f.obs_status, f.note_indicator,
               f.outlier_z, f.outlier_iqr, f.patahan_definisi, f.patahan_kandidat,
               (f.outlier_z OR f.outlier_iqr OR f.patahan_definisi OR f.patahan_kandidat) AS ada_anomali,
               f._berkas_raw, f._sha256_raw, f.n_berkas_sama
        FROM f
        JOIN dim_seri d USING (sumber, seri_kode, rincian)
        ORDER BY obs_id
    """)
    con.execute("DROP TABLE _patahan_kandidat")


def _panel(con, nama_kolom):
    # Seri sub-tahunan dirata-ratakan ke tahun; n_obs mencatat berapa periode yang dirata-ratakan.
    con.execute("""
        CREATE TABLE panel_tahunan AS
        SELECT seri_id, sumber, seri_kode, rincian, wilayah_kode, tahun,
               avg(nilai)                  AS nilai,
               any_value(satuan)           AS satuan,
               any_value(jenis_periode)    AS jenis_periode,
               count(*)                    AS n_obs,
               bool_or(ada_anomali)        AS ada_anomali
        FROM fakta_observasi
        GROUP BY seri_id, sumber, seri_kode, rincian, wilayah_kode, tahun
        ORDER BY seri_id, wilayah_kode, tahun
    """)
    if len(nama_kolom) > MAKS_KOLOM_LEBAR:
        print(f"  peringatan: {len(nama_kolom)} seri > {MAKS_KOLOM_LEBAR}; panel_lebar dilewati.")
        con.execute("CREATE TABLE panel_lebar AS SELECT NULL::BIGINT AS wilayah_kode WHERE false")
        return
    kolom = ",\n               ".join(
        f"max(p.nilai) FILTER (WHERE p.seri_id = {sid}) AS {_q(n)}"
        for sid, n in sorted(nama_kolom.items()))
    con.execute(f"""
        CREATE TABLE panel_lebar AS
        SELECT p.wilayah_kode, w.nama_wilayah, p.tahun,
               {kolom}
        FROM panel_tahunan p
        JOIN dim_wilayah w USING (wilayah_kode)
        GROUP BY p.wilayah_kode, w.nama_wilayah, p.tahun
        ORDER BY p.wilayah_kode, p.tahun
    """)


def _metrik(con):
    m = con.execute("""
        SELECT (SELECT count(*) FROM silver_src)                      AS baris_silver,
               (SELECT sum(nilai) FROM silver_src)                    AS jumlah_nilai_silver,
               (SELECT count(*) FROM fakta_observasi)                 AS baris_fakta,
               (SELECT sum(nilai) FROM fakta_observasi)               AS jumlah_nilai_fakta,
               (SELECT count(*) FROM dim_wilayah)                     AS n_wilayah,
               (SELECT count(*) FROM dim_seri)                        AS n_seri,
               (SELECT count(*) FROM dim_waktu)                       AS n_periode,
               (SELECT count(*) FROM panel_tahunan)                   AS baris_panel_tahunan,
               (SELECT count(*) FROM panel_lebar)                     AS baris_panel_lebar,
               (SELECT count(*) FROM fakta_observasi WHERE outlier_z) AS outlier_z,
               (SELECT count(*) FROM fakta_observasi WHERE outlier_iqr) AS outlier_iqr,
               (SELECT count(*) FROM fakta_observasi WHERE patahan_definisi) AS patahan_definisi,
               (SELECT count(*) FROM fakta_observasi WHERE patahan_kandidat) AS patahan_kandidat
    """).fetchdf().iloc[0].to_dict()
    m = {k: (float(v) if k.startswith("jumlah") else int(v)) for k, v in m.items()}
    m["duplikat_lintas_berkas_dibuang"] = m["baris_silver"] - m["baris_fakta"]
    return m


def _periksa(con, m):
    """Pemeriksaan integritas Gold. Gagal keras bila model tidak konsisten."""
    gagal = []
    if m["baris_fakta"] + m["duplikat_lintas_berkas_dibuang"] != m["baris_silver"]:
        gagal.append("rekonsiliasi baris Silver -> Gold tidak cocok")
    if m["baris_fakta"] == 0:
        gagal.append("fakta_observasi kosong")
    if _skalar(con, "SELECT count(*) FROM (SELECT 1 FROM fakta_observasi "
                    "GROUP BY sumber, seri_kode, wilayah_kode, periode, rincian HAVING count(*) > 1)"):
        gagal.append("kunci alami ganda di fakta_observasi")
    if _skalar(con, "SELECT count(*) FROM fakta_observasi f ANTI JOIN dim_wilayah w USING (wilayah_kode)"):
        gagal.append("wilayah_kode yatim di fakta_observasi")
    if _skalar(con, "SELECT count(*) FROM fakta_observasi WHERE NOT isfinite(nilai)"):
        gagal.append("nilai tidak terhingga di fakta_observasi")
    if _skalar(con, "SELECT count(*) FROM (SELECT 1 FROM panel_tahunan "
                    "GROUP BY seri_id, wilayah_kode, tahun HAVING count(*) > 1)"):
        gagal.append("panel_tahunan tidak unik pada (seri_id, wilayah_kode, tahun)")
    if gagal:
        raise ValueError("Pemeriksaan Gold gagal: " + "; ".join(gagal))


# --------------------------------------------------------------------------- ekspor
def _ekspor(con):
    jalur = {}
    for t in TABEL_KELUARAN:
        p = GOLD_DIR / f"{t}.parquet"
        con.execute(f"COPY {t} TO '{p.as_posix()}' (FORMAT parquet, COMPRESSION zstd)")
        jalur[t] = str(p)
    return jalur


# --------------------------------------------------------------------------- titik masuk
def jalankan(silver_hasil=None):
    """Bangun Gold dari Silver. Mengembalikan dict: db, parquet, metrik."""
    GOLD_DIR.mkdir(parents=True, exist_ok=True)
    INTERIM_DIR.mkdir(parents=True, exist_ok=True)
    if GOLD_DB.exists():                       # bangun ulang dari nol agar reproduksibel
        GOLD_DB.unlink()
    sumber = _sumber_silver(silver_hasil)

    con = duckdb.connect(str(GOLD_DB))
    try:
        _muat_silver(con, sumber)
        _staging(con)
        nama_kolom = _dimensi(con)
        _fakta(con)
        _panel(con, nama_kolom)
        m = _metrik(con)
        _periksa(con, m)
        kol = ", ".join(f"{_q(k)} {'DOUBLE' if k.startswith('jumlah') else 'BIGINT'}" for k in m)
        con.execute(f"CREATE TABLE gold_metrik ({kol})")
        con.execute(f"INSERT INTO gold_metrik VALUES ({', '.join('?' * len(m))})", list(m.values()))
        jalur = _ekspor(con)
        con.execute("CHECKPOINT")
    finally:
        con.close()

    (INTERIM_DIR / "gold_metrik.json").write_text(
        json.dumps(m, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    print(f"  gold: {m['baris_fakta']} baris fakta, {m['n_seri']} seri, "
          f"{m['n_wilayah']} wilayah, {m['baris_panel_tahunan']} baris panel tahunan "
          f"({m['duplikat_lintas_berkas_dibuang']} duplikat lintas berkas dibuang)")
    return {"db": str(GOLD_DB), "parquet": jalur, "metrik": m}


if __name__ == "__main__":
    jalankan()
