"""Koneksi MySQL Hostinger. Versi 3. Fallback ke CSV jika MySQL tidak tersedia."""
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

_last_mysql_error: str = ""


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
    dbname = _secret("MYSQL_DB")
    if all([host, user, pwd, dbname]):
        return {"host": host, "user": user, "password": pwd,
                "database": dbname, "port": 3306}
    return None


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Normalkan nama kolom ke UPPERCASE dan buang kolom 'ID' jika ada."""
    df.columns = [c.strip().upper() for c in df.columns]
    if "ID" in df.columns:
        df = df.drop(columns=["ID"])
    return df


def _load_from_mysql(role: str) -> pd.DataFrame | None:
    global _last_mysql_error
    cfg = _mysql_config()
    if not cfg:
        _last_mysql_error = "Secrets MySQL belum lengkap."
        return None
    try:
        import pymysql
        conn = pymysql.connect(**cfg, connect_timeout=8)
        # Pakai SELECT * lalu filter kolom di Python
        # supaya tidak bergantung pada case nama kolom di SQL
        df = pd.read_sql("SELECT * FROM isr LIMIT 20000", conn)
        conn.close()
        df = _normalize(df)
        if role == "public":
            available = [c for c in PUBLIC_COLS if c in df.columns]
            df = df[available].copy()
        _last_mysql_error = ""
        return df
    except Exception as e:
        _last_mysql_error = str(e)
        return None


@functools.lru_cache(maxsize=2)
def _load_csv(role: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, low_memory=False)
    if role == "public":
        available = [c for c in PUBLIC_COLS if c in df.columns]
        return df[available].copy()
    return df.copy()


def _load_uncached(role: str) -> tuple[pd.DataFrame, str]:
    """Load data dan kembalikan (df, sumber). Tidak di-cache langsung."""
    df = _load_from_mysql(role)
    if df is not None and not df.empty:
        return df, "MySQL"
    return _load_csv(role), "CSV lokal"


try:
    import streamlit as st

    @st.cache_data(ttl=300, show_spinner="Memuat data...")
    def load(role: str = "public") -> pd.DataFrame:
        """Cache 5 menit di Streamlit Cloud. Fallback ke tanpa cache di luar Streamlit."""
        df, _ = _load_uncached(role)
        return df

    @st.cache_data(ttl=300)
    def data_source(role: str = "public") -> str:
        _, src = _load_uncached(role)
        return src

except ImportError:
    # Di luar Streamlit (test lokal, CI)
    def load(role: str = "public") -> pd.DataFrame:
        df, _ = _load_uncached(role)
        return df

    def data_source(role: str = "public") -> str:
        _, src = _load_uncached(role)
        return src


def last_mysql_error() -> str:
    return _last_mysql_error


def summary(role: str = "public") -> str:
    df = load(role)
    src = data_source(role)
    lines = [
        f"Sumber: {src}. Dataset: {len(df):,} baris, {len(df.columns)} kolom.",
        f"Kolom: {', '.join(df.columns.tolist())}.",
    ]
    if "SERVICE" in df.columns:
        lines.append(f"Layanan: {df['SERVICE'].value_counts().to_dict()}")
    if role == "officer":
        if "PROVINCE" in df.columns:
            lines.append(f"Provinsi: {df['PROVINCE'].value_counts().to_dict()}")
        if "STATUS_SIMF" in df.columns:
            lines.append(f"Status: {df['STATUS_SIMF'].value_counts().to_dict()}")
    else:
        if "CITY" in df.columns:
            lines.append(f"Kota (10 terbesar): {df['CITY'].value_counts().head(10).to_dict()}")
    return "\n".join(lines)


def test_connection() -> tuple[bool, str]:
    cfg = _mysql_config()
    if not cfg:
        return False, "Secrets MySQL belum diisi (MYSQL_HOST/USER/PASSWORD/DB)."
    try:
        import pymysql
        conn = pymysql.connect(**cfg, connect_timeout=8)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM isr")
        count = cur.fetchone()[0]
        cur.execute("SHOW COLUMNS FROM isr")
        cols = [r[0].upper() for r in cur.fetchall()]
        conn.close()
        return True, f"OK. Baris: {count:,}. Kolom ({len(cols)}): {cols[:10]}..."
    except Exception as e:
        return False, str(e)
