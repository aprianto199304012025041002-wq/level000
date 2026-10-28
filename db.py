"""Koneksi MySQL Hostinger. Fallback ke CSV jika MySQL tidak tersedia."""
import functools
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path(__file__).parent / "data" / "QUERY_14_JANUARI_2026.csv"

PUBLIC_COLS = [
    "SERVICE", "SUBSERVICE", "STN_NAME", "STN_ADDR",
    "CITY", "DISTRICT", "PROVINCE", "VILLAGE", "CLNT_NAME",
]


def _secret(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _mysql_config() -> dict | None:
    host = _secret("MYSQL_HOST")
    user = _secret("MYSQL_USER")
    pwd  = _secret("MYSQL_PASSWORD")
    db   = _secret("MYSQL_DB")
    if all([host, user, pwd, db]):
        return {"host": host, "user": user, "password": pwd, "database": db, "port": 3306}
    return None


def _load_from_mysql(role: str) -> pd.DataFrame | None:
    cfg = _mysql_config()
    if not cfg:
        return None
    try:
        import pymysql
        conn = pymysql.connect(**cfg, connect_timeout=8)
        if role == "public":
            cols = ", ".join(PUBLIC_COLS)
            df = pd.read_sql(f"SELECT {cols} FROM isr LIMIT 20000", conn)
        else:
            df = pd.read_sql("SELECT * FROM isr LIMIT 20000", conn)
        conn.close()
        return df
    except Exception:
        return None


@functools.lru_cache(maxsize=2)
def _load_csv(role: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, low_memory=False)
    if role == "public":
        return df[PUBLIC_COLS].copy()
    return df.copy()


def load(role: str = "public") -> pd.DataFrame:
    """Coba MySQL dulu, fallback ke CSV."""
    df = _load_from_mysql(role)
    if df is not None and not df.empty:
        return df
    return _load_csv(role)


def data_source(role: str = "public") -> str:
    """Kembalikan keterangan sumber data aktif."""
    df = _load_from_mysql(role)
    if df is not None and not df.empty:
        return "MySQL"
    return "CSV lokal"


def summary(role: str = "public") -> str:
    df = load(role)
    src = data_source(role)
    lines = [
        f"Sumber: {src}. Dataset: {len(df):,} baris, {len(df.columns)} kolom.",
        f"Kolom: {', '.join(df.columns.tolist())}.",
        f"Layanan: {df['SERVICE'].value_counts().to_dict()}",
    ]
    if role == "officer":
        lines.append(f"Provinsi: {df['PROVINCE'].value_counts().to_dict()}")
        lines.append(f"Status: {df['STATUS_SIMF'].value_counts().to_dict()}")
    else:
        lines.append(f"Kota (10 terbesar): {df['CITY'].value_counts().head(10).to_dict()}")
    return "\n".join(lines)


def test_connection() -> tuple[bool, str]:
    """Coba konek MySQL, kembalikan (sukses, pesan)."""
    cfg = _mysql_config()
    if not cfg:
        return False, "Secrets MySQL belum diisi (MYSQL_HOST/USER/PASSWORD/DB)."
    try:
        import pymysql
        conn = pymysql.connect(**cfg, connect_timeout=8)
        cur = conn.cursor()
        cur.execute("SHOW TABLES")
        tables = [r[0] for r in cur.fetchall()]
        cur.execute("SELECT COUNT(*) FROM isr")
        count = cur.fetchone()[0]
        conn.close()
        return True, f"OK. Tabel: {tables}. Baris di isr: {count:,}"
    except Exception as e:
        return False, str(e)
