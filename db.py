"""Koneksi MySQL dengan query langsung. Fallback ke CSV jika MySQL tidak tersedia."""
import functools
import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

CSV_PATH = Path(__file__).parent / "data" / "QUERY_14_JANUARI_2026.csv"

PUBLIC_COLS_SQL  = "service, subservice, stn_name, stn_addr, city, district, province, village, clnt_name"
PUBLIC_COLS_PY   = ["SERVICE","SUBSERVICE","STN_NAME","STN_ADDR","CITY","DISTRICT","PROVINCE","VILLAGE","CLNT_NAME"]

_last_error: str = ""
_mysql_ok:   bool | None = None   # None = belum dicek


def _secret(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def _cfg() -> dict | None:
    h = _secret("MYSQL_HOST"); u = _secret("MYSQL_USER")
    p = _secret("MYSQL_PASSWORD"); d = _secret("MYSQL_DB")
    return {"host":h,"user":u,"password":p,"database":d,"port":3306} if all([h,u,p,d]) else None


def _engine():
    """SQLAlchemy engine (pakai pool_pre_ping supaya tidak timeout)."""
    from sqlalchemy import create_engine
    cfg = _cfg()
    if not cfg:
        raise RuntimeError("Secrets MySQL belum diisi.")
    url = (f"mysql+pymysql://{cfg['user']}:{cfg['password']}"
           f"@{cfg['host']}:{cfg['port']}/{cfg['database']}")
    return create_engine(url, pool_pre_ping=True, connect_args={"connect_timeout": 8})


def _conn():
    """Koneksi raw pymysql (untuk SHOW COLUMNS dan test_connection)."""
    import pymysql
    cfg = _cfg()
    if not cfg:
        raise RuntimeError("Secrets MySQL belum diisi.")
    return pymysql.connect(**cfg, connect_timeout=8)


def _use_mysql() -> bool:
    global _mysql_ok, _last_error
    if _mysql_ok is not None:
        return _mysql_ok
    try:
        engine = _engine()
        with engine.connect():
            pass
        _mysql_ok = True
    except Exception as e:
        _mysql_ok = False
        _last_error = str(e)
    return _mysql_ok


def execute(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Jalankan SQL dan kembalikan DataFrame. Raise jika MySQL tidak tersedia."""
    from sqlalchemy import text
    engine = _engine()
    # Konversi %s placeholder ke :p0,:p1,... untuk SQLAlchemy
    named_sql = sql
    named_params = {}
    for i, v in enumerate(params):
        named_sql = named_sql.replace("%s", f":p{i}", 1)
        named_params[f"p{i}"] = v
    with engine.connect() as conn:
        df = pd.read_sql(text(named_sql), conn,
                         params=named_params if named_params else None)
    df.columns = [c.upper() for c in df.columns]
    return df


def search(query_text: str, role: str = "public", limit: int = 10) -> pd.DataFrame:
    """
    Cari baris relevan: MySQL LIKE jika tersedia, BM25 pandas jika fallback CSV.
    """
    if _use_mysql():
        cols   = PUBLIC_COLS_SQL if role == "public" else "*"
        terms  = [f"%{w}%" for w in query_text.split()[:4]]
        if not terms:
            return pd.DataFrame()
        where  = " OR ".join(
            ["stn_name LIKE %s","clnt_name LIKE %s","city LIKE %s","service LIKE %s"][:len(terms)]
        )
        sql = f"SELECT {cols} FROM isr WHERE {where} LIMIT {limit}"
        try:
            return execute(sql, tuple(terms))
        except Exception:
            pass

    # Fallback CSV + BM25
    import rag as _rag
    df = _load_csv(role)
    return _rag.search(query_text, df, k=limit)


@functools.lru_cache(maxsize=2)
def _load_csv(role: str) -> pd.DataFrame:
    df = pd.read_csv(CSV_PATH, low_memory=False)
    if role == "public":
        avail = [c for c in PUBLIC_COLS_PY if c in df.columns]
        return df[avail].copy()
    return df.copy()


def summary(role: str = "public") -> str:
    """Ringkasan dataset via SQL GROUP BY, fallback ke pandas."""
    if _use_mysql():
        try:
            svc  = execute("SELECT service, COUNT(*) AS cnt FROM isr GROUP BY service ORDER BY cnt DESC")
            prov = execute("SELECT province, COUNT(*) AS cnt FROM isr GROUP BY province")
            total = execute("SELECT COUNT(*) AS cnt FROM isr").iloc[0]["CNT"]
            lines = [
                f"Sumber: MySQL. Total izin: {int(total):,}.",
                f"Per layanan:\n{svc.to_string(index=False)}",
                f"Per provinsi:\n{prov.to_string(index=False)}",
            ]
            if role == "officer":
                exp = execute(
                    "SELECT COUNT(*) AS cnt FROM isr WHERE validity_date < CURDATE()"
                ).iloc[0]["CNT"]
                lines.append(f"Expired: {int(exp):,} izin.")
            return "\n".join(lines)
        except Exception:
            pass

    df = _load_csv(role)
    lines = [f"Sumber: CSV. Total: {len(df):,} baris."]
    if "SERVICE" in df.columns:
        lines.append(f"Per layanan:\n{df['SERVICE'].value_counts().to_string()}")
    return "\n".join(lines)


def stats_for_header() -> dict:
    """Statistik untuk kartu header halaman utama."""
    if _use_mysql():
        try:
            row = execute("""
                SELECT
                  COUNT(*) AS total,
                  SUM(validity_date >= CURDATE()) AS active,
                  SUM(validity_date < CURDATE())  AS expired,
                  SUM(validity_date IS NULL)       AS unknown
                FROM isr
            """).iloc[0]
            return {k: int(v or 0) for k, v in row.items()}
        except Exception:
            pass
    df = _load_csv("officer")
    vd = pd.to_datetime(df.get("VALIDITY_DATE", pd.Series()), errors="coerce")
    import datetime
    today = pd.Timestamp(datetime.date.today())
    return {
        "TOTAL":   len(df),
        "ACTIVE":  int((vd >= today).sum()),
        "EXPIRED": int((vd < today).sum()),
        "UNKNOWN": int(vd.isna().sum()),
    }


def data_source(_role: str = "public") -> str:
    return "MySQL" if _use_mysql() else "CSV lokal"


def last_mysql_error() -> str:
    return _last_error


def test_connection() -> tuple[bool, str]:
    cfg = _cfg()
    if not cfg:
        return False, "Secrets MySQL belum diisi."
    try:
        import pymysql
        conn = pymysql.connect(**cfg, connect_timeout=8)
        cur  = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM isr")
        count = cur.fetchone()[0]
        cur.execute("SHOW COLUMNS FROM isr")
        cols = [r[0].upper() for r in cur.fetchall()]
        conn.close()
        global _mysql_ok; _mysql_ok = True
        return True, f"OK. Baris: {count:,}. Kolom ({len(cols)}): {cols[:8]}..."
    except Exception as e:
        return False, str(e)
