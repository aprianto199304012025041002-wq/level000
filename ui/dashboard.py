"""Bento dashboard: stat cards + sunburst charts untuk landing page."""
import streamlit as st
import streamlit.components.v1 as components

from core import db
from . import charts

_CARD_JS = (
    "<script>"
    "var M=['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des'];"
    "var D=['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];"
    "function tick(){"
    "var n=new Date(),j=new Date(n.getTime()+25200000);"
    "var h=j.getUTCHours(),m=j.getUTCMinutes(),s=j.getUTCSeconds();"
    "var el=document.getElementById('clk');"
    "if(el)el.textContent=D[j.getUTCDay()]+', '+"
    "String(j.getUTCDate()).padStart(2,'0')+' '+M[j.getUTCMonth()]+' '+j.getUTCFullYear()+"
    "' \u00b7 '+String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0')+' WIB';"
    "}"
    "tick();setInterval(tick,1000);"
    "</script>"
)

_CARD_CSS = (
    "<style>"
    "*{box-sizing:border-box;margin:0;padding:0}"
    "body{background:transparent;font-family:'Inter',sans-serif}"
    ".card{background:linear-gradient(135deg,#0D2B55 0%,#1565C0 60%,#1A4A8A 100%);"
    "border-radius:14px;padding:1.3rem 1.6rem;position:relative;overflow:hidden;"
    "display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;flex-wrap:wrap}"
    ".lbl{font-size:.6rem;font-weight:600;letter-spacing:.1em;color:rgba(255,255,255,.4);"
    "text-transform:uppercase;margin-bottom:.35rem}"
    ".num{font-family:'Space Grotesk','Inter',sans-serif;font-size:3rem;font-weight:700;"
    "color:#fff;line-height:1;margin-bottom:.4rem}"
    ".clk{font-size:.7rem;color:rgba(255,255,255,.65)}"
    ".rtl{text-align:right}"
    ".lbl2{font-size:.58rem;font-weight:600;letter-spacing:.1em;color:rgba(255,255,255,.4);"
    "text-transform:uppercase;margin-bottom:.3rem}"
    ".tgl{font-size:1.35rem;font-weight:700;color:#00B4D8;"
    "font-family:'Space Grotesk','Inter',sans-serif;line-height:1}"
    ".sub{font-size:.58rem;color:rgba(255,255,255,.4);margin-top:.3rem}"
    "</style>"
)


def stat_card_html(total: int, tgl: str) -> str:
    return (
        _CARD_CSS
        + "<div class='card'>"
        + "  <div>"
        + "    <div class='lbl'>Total Izin Stasiun Radio</div>"
        + f"   <div class='num'>{total:,}</div>"
        + "    <div id='clk' class='clk'>--</div>"
        + "  </div>"
        + "  <div class='rtl'>"
        + "    <div class='lbl2'>Data per</div>"
        + f"   <div class='tgl'>{tgl}</div>"
        + "    <div class='sub'>DIY &amp; Jawa Tengah</div>"
        + "  </div>"
        + "</div>"
        + _CARD_JS
    )


def render() -> None:
    """Render seluruh bento dashboard: card total + dua sunburst."""
    try:
        import pandas as pd

        if db._use_mysql():
            tgl_row = db.execute("SELECT MAX(tgl_query) AS tgl FROM isr").iloc[0]
            tgl = str(tgl_row["TGL"] or "-")
            s_row = db.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(STR_TO_DATE(validity_date,'%%d-%%b-%%y') >= "
                "STR_TO_DATE(tgl_query,'%%d-%%b-%%y')) AS active, "
                "SUM(STR_TO_DATE(validity_date,'%%d-%%b-%%y') < "
                "STR_TO_DATE(tgl_query,'%%d-%%b-%%y')) AS expired "
                "FROM isr"
            ).iloc[0]
            total   = int(s_row["TOTAL"]   or 0)
            active  = int(s_row["ACTIVE"]  or 0)
            expired = int(s_row["EXPIRED"] or 0)
            df_wil  = db.execute(
                "SELECT province, city, COUNT(*) AS cnt FROM isr GROUP BY province, city"
            )
            df_svc  = db.execute(
                "SELECT service, subservice, COUNT(*) AS cnt FROM isr GROUP BY service, subservice"
            )
        else:
            import datetime as _dt
            df_all  = db._load_csv("officer")
            total   = len(df_all)
            vd      = pd.to_datetime(df_all.get("VALIDITY_DATE", pd.Series()), errors="coerce")
            today_  = pd.Timestamp(_dt.date.today())
            active  = int((vd >= today_).sum())
            expired = int((vd <  today_).sum())
            tgl     = str(df_all["TGL_QUERY"].iloc[0]) if "TGL_QUERY" in df_all.columns else "-"
            df_wil  = df_all.groupby(["PROVINCE","CITY"]).size().reset_index(name="cnt")
            df_svc  = df_all.groupby(["SERVICE","SUBSERVICE"]).size().reset_index(name="cnt")

        df_wil.columns = [c.upper() for c in df_wil.columns]
        df_svc.columns = [c.upper() for c in df_svc.columns]

        # Baris 1: Card total + jam live
        components.html(stat_card_html(total, tgl), height=150)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Baris 2: Sunburst wilayah + service
        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_wilayah(df_wil),
                                width="stretch",
                                config={"displayModeBar": False})
        with c2:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_service(df_svc),
                                width="stretch",
                                config={"displayModeBar": False})

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    except Exception as e:
        st.caption(f"Dashboard tidak tersedia: {e}")
