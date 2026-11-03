"""Analitik: SQL langsung jika MySQL tersedia, pandas jika fallback CSV."""
import re
from datetime import date


def build_context(query: str, df_fallback, role: str) -> str:
    from core import db
    q = query.lower()
    parts = []

    if db._use_mysql():
        parts = _sql_context(q, query, role)
    else:
        parts = _pandas_context(q, query, df_fallback, role)

    if not parts:
        # Tidak ada query khusus terdeteksi — kembalikan ringkasan singkat
        try:
            total = db.execute("SELECT COUNT(*) AS cnt FROM isr").iloc[0]["CNT"]
            return f"Database aktif: {int(total):,} izin spektrum tersedia untuk dianalisis."
        except Exception:
            return ""
    return "\n\n".join(parts)


def _sql_context(q: str, query: str, role: str) -> list[str]:
    from core import db
    parts = []

    # Expired / masa berlaku
    if any(w in q for w in ["expired","habis","kadaluarsa","kadaluwarsa","masa berlaku",
                             "tidak berlaku","sudah mati","lewat masa","kedaluarsa"]):
        try:
            r = db.execute("""
                SELECT
                  SUM(STR_TO_DATE(validity_date, '%%d-%%b-%%y') <
                      STR_TO_DATE(tgl_query, '%%d-%%b-%%y'))      AS expired,
                  SUM(STR_TO_DATE(validity_date, '%%d-%%b-%%y') >=
                      STR_TO_DATE(tgl_query, '%%d-%%b-%%y'))      AS active,
                  SUM(validity_date IS NULL OR validity_date = '') AS unknown,
                  MAX(tgl_query) AS tgl_ref
                FROM isr
            """).iloc[0]
            tgl_ref = r.get("TGL_REF", "-")
            parts.append(
                f"Status masa berlaku (per tanggal data: {tgl_ref}):\n"
                f"- Expired : {int(r.get('EXPIRED',0) or 0):,}\n"
                f"- Aktif   : {int(r.get('ACTIVE',0) or 0):,}\n"
                f"- Tidak diketahui: {int(r.get('UNKNOWN',0) or 0):,}"
            )
            svc = db.execute("""
                SELECT service, COUNT(*) AS cnt FROM isr
                WHERE STR_TO_DATE(validity_date, '%%d-%%b-%%y') <
                      STR_TO_DATE(tgl_query, '%%d-%%b-%%y')
                GROUP BY service ORDER BY cnt DESC
            """)
            parts.append("Expired per layanan:\n" + svc.to_string(index=False))
        except Exception as e:
            parts.append(f"(gagal query expired: {e})")

    # ERP tertinggi
    if any(w in q for w in ["erp","daya","tertinggi","terbesar","terkuat","power","kuat","sinyal","transmit"]):
        try:
            df = db.execute("""
                SELECT clnt_name, stn_name, freq, service, erp_pwr_dbm, city
                FROM isr ORDER BY erp_pwr_dbm DESC LIMIT 5
            """)
            parts.append("5 stasiun ERP tertinggi (dBm):\n" + df.to_string(index=False))
        except Exception as e:
            parts.append(f"(gagal query ERP: {e})")

    # Jumlah / berapa
    if any(w in q for w in ["berapa","jumlah","total","hitung","banyak","statistik","rekapitulasi","rekap","distribusi"]):
        try:
            svc = db.execute(
                "SELECT service, COUNT(*) AS jumlah FROM isr GROUP BY service ORDER BY jumlah DESC"
            )
            parts.append("Jumlah izin per layanan:\n" + svc.to_string(index=False))
            prov = db.execute(
                "SELECT province, COUNT(*) AS jumlah FROM isr GROUP BY province ORDER BY jumlah DESC"
            )
            parts.append("Jumlah izin per provinsi:\n" + prov.to_string(index=False))
        except Exception as e:
            parts.append(f"(gagal query jumlah: {e})")

    # Frekuensi tertentu
    fm = re.search(r"(\d{2,4}(?:[.,]\d+)?)\s*(?:mhz|khz|ghz|MHz|KHz|GHz)", query, re.I)
    if fm:
        try:
            fv = float(fm.group(1).replace(",","."))
            df = db.execute(
                "SELECT clnt_name,stn_name,freq,service,city,validity_date "
                "FROM isr WHERE freq BETWEEN %s AND %s LIMIT 10",
                (fv - 0.1, fv + 0.1)
            )
            if not df.empty:
                parts.append(f"Izin sekitar {fm.group(0)}:\n" + df.to_string(index=False))
        except Exception as e:
            parts.append(f"(gagal query frekuensi: {e})")

    # Kota
    # Ambil kota dari database (cache sederhana via modul)
    PUBLIC_SAFE = "service, subservice, clnt_name, stn_name, stn_addr, city, district, province, village"
    OFFICER_ALL = "clnt_name, stn_name, freq, service, city, validity_date, erp_pwr_dbm, curr_lic_num"
    try:
        _city_df = db.execute("SELECT DISTINCT LOWER(city) AS c FROM isr WHERE city IS NOT NULL LIMIT 100")
        _cities = _city_df["C"].tolist()
    except Exception:
        _cities = ["bantul","sleman","yogyakarta","kulonprogo","gunungkidul",
                   "magelang","klaten","semarang","purworejo","kebumen"]
    for city in _cities:
        if str(city).lower() in q:
            try:
                cols = PUBLIC_SAFE if role == "public" else OFFICER_ALL
                df = db.execute(
                    f"SELECT {cols} FROM isr WHERE LOWER(city) LIKE %s LIMIT 15",
                    (f"%{city}%",)
                )
                if not df.empty:
                    parts.append(f"Izin di {city.title()} ({len(df)} entri ditampilkan):\n"
                                 + df.to_string(index=False))
            except Exception as e:
                parts.append(f"(gagal query kota: {e})")
            break

    return parts


def _pandas_context(q: str, query: str, df, role: str) -> list[str]:
    """Fallback pandas untuk mode CSV."""
    import re
    from datetime import date
    import pandas as pd
    parts = []

    if any(w in q for w in ["expired","habis","kadaluarsa","masa berlaku"]):
        if "VALIDITY_DATE" in df.columns:
            df2 = df.copy()
            df2["_vd"] = pd.to_datetime(df2["VALIDITY_DATE"], errors="coerce")
            today = pd.Timestamp(date.today())
            exp = df2[df2["_vd"] < today]
            act = df2[df2["_vd"] >= today]
            parts.append(
                f"Status masa berlaku (per {date.today()}):\n"
                f"- Expired: {len(exp):,}\n- Aktif: {len(act):,}\n"
                f"- Tidak diketahui: {df2['_vd'].isna().sum():,}"
            )

    if any(w in q for w in ["erp","daya","tertinggi","terbesar","power"]):
        if "ERP_PWR_DBM" in df.columns:
            top = df.dropna(subset=["ERP_PWR_DBM"]).nlargest(5,"ERP_PWR_DBM")[
                [c for c in ["CLNT_NAME","STN_NAME","FREQ","SERVICE","ERP_PWR_DBM","CITY"] if c in df.columns]
            ]
            parts.append("5 stasiun ERP tertinggi:\n" + top.to_string(index=False))

    if any(w in q for w in ["berapa","jumlah","total","banyak"]):
        if "SERVICE" in df.columns:
            parts.append("Jumlah per layanan:\n" + df["SERVICE"].value_counts().to_string())

    if "CITY" in df.columns:
        PUBLIC_SAFE = ["CLNT_NAME","STN_NAME","SERVICE","SUBSERVICE","CITY","DISTRICT","PROVINCE"]
        for city in df["CITY"].dropna().unique():
            if str(city).lower() in q:
                hits = df[df["CITY"].str.lower() == str(city).lower()]
                cols = [c for c in PUBLIC_SAFE if c in hits.columns]
                parts.append(f"Izin di {city}:\n" + hits[cols].head(10).to_string(index=False))
                break

    return parts
