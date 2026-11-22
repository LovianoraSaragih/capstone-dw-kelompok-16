-- DDL Silver (SQLite). Skema mengikuti KOLOM/WAJIB di transformasi.py.
-- Untuk PostgreSQL: ganti TEXT->TEXT, INTEGER->BIGINT, REAL->DOUBLE PRECISION,
-- hapus "WITHOUT ROWID", dan ganti CHECK(typeof(...)) dengan tipe kolom yang ketat.

PRAGMA foreign_keys = ON;

CREATE TABLE silver_observasi (
    sumber          TEXT    NOT NULL CHECK (sumber IN ('bps','ilostat','wdi')),
    seri_kode       TEXT    NOT NULL,
    wilayah_kode    INTEGER NOT NULL,          -- 9999 = nasional (lihat panel.py)
    nama_wilayah    TEXT    NOT NULL,
    periode         TEXT    NOT NULL,          -- disimpan sebagai teks, sama dengan Silver parquet
    jenis_periode   TEXT    NOT NULL,
    rincian         TEXT    NOT NULL,
    nilai           REAL    NOT NULL,          -- WAJIB di transformasi.py; kosong tidak diimputasi
    satuan          TEXT    NOT NULL,
    _berkas_raw     TEXT    NOT NULL,          -- jejak asal: nama berkas mentah
    _sha256_raw     TEXT    NOT NULL,          -- jejak asal: checksum berkas mentah
    obs_status      TEXT    NOT NULL DEFAULT '',
    note_indicator  TEXT    NOT NULL DEFAULT '',
    -- kunci sama dengan KUNCI di pembersihan.py (cek_duplikat)
    PRIMARY KEY (sumber, seri_kode, wilayah_kode, periode, rincian, _berkas_raw),
    CHECK (typeof(nilai) IN ('real','integer')),
    CHECK (length(_sha256_raw) = 64)
) WITHOUT ROWID;

CREATE INDEX ix_silver_seri_wilayah_periode
    ON silver_observasi (seri_kode, wilayah_kode, periode);
CREATE INDEX ix_silver_wilayah
    ON silver_observasi (wilayah_kode);

-- Log setiap pemuatan, agar isi database bisa dilacak ke berkas parquet-nya.
CREATE TABLE silver_muat_log (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    waktu_utc       TEXT    NOT NULL,
    berkas_parquet  TEXT    NOT NULL,
    sha256_parquet  TEXT    NOT NULL,
    jumlah_baris    INTEGER NOT NULL,
    jumlah_seri     INTEGER NOT NULL,
    jumlah_nilai    REAL    NOT NULL           -- SUM(nilai), pemeriksaan silang
);
