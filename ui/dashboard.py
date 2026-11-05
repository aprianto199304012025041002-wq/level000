"""Dashboard infografis PAIDI-INSIGHT."""
import streamlit as st
from core import db, insights
from ui import charts

_CARD_CSS = (
    "<style>*{box-sizing:border-box;margin:0;padding:0}"
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
_CLOCK_JS = (
    "<script>var M=['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Ags','Sep','Okt','Nov','Des'];"
    "var D=['Minggu','Senin','Selasa','Rabu','Kamis','Jumat','Sabtu'];"
    "function tick(){var n=new Date(),j=new Date(n.getTime()+25200000);"
    "var h=j.getUTCHours(),m=j.getUTCMinutes(),s=j.getUTCSeconds();"
    "var el=document.getElementById('clk');"
    "if(el)el.textContent=D[j.getUTCDay()]+', '+"
    "String(j.getUTCDate()).padStart(2,'0')+' '+M[j.getUTCMonth()]+' '+j.getUTCFullYear()+"
    "' \u00b7 '+String(h).padStart(2,'0')+':'+String(m).padStart(2,'0')+':'+String(s).padStart(2,'0')+' WIB';}"
    "tick();setInterval(tick,1000);</script>"
)

def _stat_card(total, tgl):
    return (_CARD_CSS
        + "<div class='card'><div>"
        + "<div class='lbl'>Total Izin Stasiun Radio</div>"
        + f"<div class='num'>{total:,}</div>"
        + "<div id='clk' class='clk'>--</div>"
        + "</div><div class='rtl'>"
        + "<div class='lbl2'>Data per</div>"
        + f"<div class='tgl'>{tgl}</div>"
        + "<div class='sub'>DIY &amp; Jawa Tengah</div>"
        + "</div></div>" + _CLOCK_JS)

def render():
    try:
        import pandas as pd

        if db._use_mysql():
            tgl = str(db.execute("SELECT MAX(tgl_query) AS tgl FROM isr").iloc[0]["TGL"] or "-")
            s   = db.execute(
                "SELECT COUNT(*) AS total FROM isr"
            ).iloc[0]
            total  = int(s["TOTAL"] or 0)
            df_wil = db.execute("SELECT province,city,COUNT(*) AS cnt FROM isr GROUP BY province,city")
            df_svc = db.execute("SELECT service,subservice,COUNT(*) AS cnt FROM isr GROUP BY service,subservice")
            df_all = db.execute("SELECT service,clnt_name,validity_date,tgl_query FROM isr")
        else:
            df_full = db._load_csv("officer")
            total   = len(df_full)
            tgl     = str(df_full["TGL_QUERY"].iloc[0]) if "TGL_QUERY" in df_full.columns else "-"
            df_wil  = df_full.groupby(["PROVINCE","CITY"]).size().reset_index(name="cnt")
            df_svc  = df_full.groupby(["SERVICE","SUBSERVICE"]).size().reset_index(name="cnt")
            df_all  = df_full[["SERVICE","CLNT_NAME","VALIDITY_DATE","TGL_QUERY"]].copy()

        for d in [df_wil, df_svc, df_all]:
            d.columns = [c.upper() for c in d.columns]

        # Baris 1: stat card
        st.iframe(_stat_card(total, tgl), height=150)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Baris 2: Insight Gemini + Wilayah
        c1, c2 = st.columns(2, gap="small")
        with c1:
            with st.container(border=True):
                st.markdown(
                    "<div style='font-size:.7rem;font-weight:600;letter-spacing:.08em;"
                    "color:#64748B;text-transform:uppercase;margin-bottom:.6rem'>✨ Insight AI</div>",
                    unsafe_allow_html=True)
                with st.spinner("Gemini menganalisis data..."):
                    st.markdown(insights.generate(tgl))
        with c2:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_wilayah(df_wil),
                                width="stretch", config={"displayModeBar": False})

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Baris 3: Jenis Layanan + Masa Berlaku
        c3, c4 = st.columns(2, gap="small")
        with c3:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_service(df_svc),
                                width="stretch", config={"displayModeBar": False})
        with c4:
            with st.container(border=True):
                st.plotly_chart(charts.bar_masa_berlaku(df_all),
                                width="stretch", config={"displayModeBar": False})

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # Baris 4: Top pemegang izin
        with st.container(border=True):
            st.plotly_chart(charts.bar_top_clnt(df_all, top_n=10),
                            width="stretch", config={"displayModeBar": False})

        st.markdown(
            "<div style='text-align:center;font-size:.65rem;color:#94A3B8;margin-top:1rem'>"
            "PAIDI-INSIGHT · Balmon Kelas I Yogyakarta · Ditjen Infrastruktur Digital · "
            "Kementerian Komunikasi dan Digital RI</div>",
            unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Dashboard tidak tersedia: {e}")
