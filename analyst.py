"""Analitik berbasis pandas untuk query petugas yang butuh agregasi."""
import re
from datetime import date

import pandas as pd


def _today() -> date:
    return date.today()


def build_context(query: str, df: pd.DataFrame, role: str) -> str:
    q = query.lower()
    parts = []

    # Expired / masa berlaku
    if any(w in q for w in ["expired", "habis", "kadaluarsa", "kadaluwarsa", "masa berlaku"]):
        if "VALIDITY_DATE" in df.columns:
            df2 = df.copy()
            df2["_vd"] = pd.to_datetime(df2["VALIDITY_DATE"], format="mixed", dayfirst=False, errors="coerce")
            expired = df2[df2["_vd"] < pd.Timestamp(_today())]
            valid   = df2[df2["_vd"] >= pd.Timestamp(_today())]
            parts.append(
                f"Status masa berlaku (per {_today()}):\n"
                f"- Sudah habis (expired): {len(expired):,} izin\n"
                f"- Masih berlaku: {len(valid):,} izin\n"
                f"- Tidak diketahui: {df2['_vd'].isna().sum():,} izin"
            )
            if len(expired) > 0 and "SERVICE" in df.columns:
                parts.append("Expired per layanan:\n" +
                    expired["SERVICE"].value_counts().to_string())

    # ERP / daya tertinggi
    if any(w in q for w in ["erp", "daya", "tertinggi", "terbesar", "terkuat", "power"]):
        if "ERP_PWR_DBM" in df.columns:
            df2 = df.dropna(subset=["ERP_PWR_DBM"]).copy()
            top = df2.nlargest(5, "ERP_PWR_DBM")[
                [c for c in ["CLNT_NAME","STN_NAME","FREQ","SERVICE","ERP_PWR_DBM","CITY"] if c in df2.columns]
            ]
            parts.append("5 stasiun ERP tertinggi (dBm):\n" + top.to_string(index=False))

    # Hitung / jumlah
    if any(w in q for w in ["berapa", "jumlah", "total", "hitung", "banyak"]):
        if "SERVICE" in df.columns:
            parts.append("Jumlah izin per layanan:\n" +
                df["SERVICE"].value_counts().to_string())
        if "PROVINCE" in df.columns:
            parts.append("Jumlah izin per provinsi:\n" +
                df["PROVINCE"].value_counts().to_string())

    # Frekuensi tertentu
    freq_match = re.search(r"(\d{2,4}(?:[.,]\d+)?)\s*(?:mhz|khz|ghz|MHz|KHz|GHz)", query, re.I)
    if freq_match and "FREQ" in df.columns:
        freq_val = freq_match.group(1).replace(",", ".")
        try:
            fv = float(freq_val)
            hits = df[df["FREQ"].between(fv - 0.1, fv + 0.1)]
            if not hits.empty:
                cols = [c for c in ["CLNT_NAME","STN_NAME","FREQ","SERVICE","CITY","VALIDITY_DATE"] if c in hits.columns]
                parts.append(f"Izin sekitar {freq_match.group(0)}:\n" +
                    hits[cols].head(10).to_string(index=False))
        except ValueError:
            pass

    # Kota / wilayah
    if "CITY" in df.columns:
        for city in df["CITY"].dropna().unique():
            if str(city).lower() in q:
                hits = df[df["CITY"].str.lower() == str(city).lower()]
                cols = [c for c in ["CLNT_NAME","STN_NAME","SERVICE","FREQ","CITY"] if c in hits.columns]
                parts.append(f"Izin di {city} ({len(hits):,} entri):\n" +
                    hits[cols].head(10).to_string(index=False))
                break

    return "\n\n".join(parts)
