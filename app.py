"""PAIDI-INSIGHT — Infografis Spektrum Frekuensi Radio."""
import streamlit as st

from ui import style, dashboard

st.set_page_config(
    page_title="PAIDI-INSIGHT · Balmon Kelas I Yogyakarta",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.markdown(style.CSS, unsafe_allow_html=True)
st.markdown(style.HEADER_HTML, unsafe_allow_html=True)

dashboard.render()
