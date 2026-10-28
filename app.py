"""PAIDI-INSIGHT — Streamlit app: dua peran, multi-model, MySQL/CSV."""
import streamlit as st

import auth
import db
import llm
import prompts
import rag

st.set_page_config(page_title="PAIDI-INSIGHT", page_icon="📡", layout="wide")

# ── State ────────────────────────────────────────────────────────────────────
for k, v in [("role", None), ("auth_failed", False), ("chat_history", []),
             ("provider", "gemini"), ("uploaded_df", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


def reset():
    for k in ("role", "auth_failed", "chat_history", "uploaded_df"):
        st.session_state[k] = None if k == "role" else (False if k == "auth_failed" else
                               [] if k == "chat_history" else None)


# ── Header ───────────────────────────────────────────────────────────────────
st.title("📡 PAIDI-INSIGHT")
st.caption("Sistem Informasi Spektrum Frekuensi Radio — Balmon Kelas I Yogyakarta")
st.divider()

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 1: Pilih Peran
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.role is None:
    st.subheader("Selamat datang! Silakan pilih peran Anda.")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🏙️ Masyarakat Umum")
        st.write("Dapatkan informasi umum tentang stasiun radio dan pemegang izin di wilayah Anda.")
        if st.button("Masuk sebagai Masyarakat", use_container_width=True):
            st.session_state.role = "public"
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        st.markdown("### 🛡️ Petugas Pengendali Frekuensi")
        st.write("Akses penuh untuk analisis data teknis, frekuensi, dan pengelolaan database.")
        with st.form("login_form"):
            password = st.text_input("Password Petugas", type="password")
            submitted = st.form_submit_button("Masuk sebagai Petugas", use_container_width=True)
            if submitted:
                if auth.check_officer_password(password):
                    st.session_state.role = "officer"
                    st.session_state.auth_failed = False
                    st.session_state.chat_history = []
                    st.rerun()
                else:
                    st.session_state.auth_failed = True

    if st.session_state.auth_failed:
        st.error("Password salah. Silakan coba lagi.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 2: Chat
# ════════════════════════════════════════════════════════════════════════════
role = st.session_state.role
is_officer = role == "officer"

with st.sidebar:
    if is_officer:
        st.success("🛡️ Mode Petugas")
    else:
        st.info("🏙️ Mode Masyarakat")

    # Pilihan model
    st.divider()
    st.markdown("**Model AI**")
    provider = st.radio(
        "Pilih model",
        options=["gemini", "qwen"],
        format_func=lambda x: "✨ Gemini (Google)" if x == "gemini" else "🧠 Qwen (Alibaba)",
        index=0 if st.session_state.provider == "gemini" else 1,
        label_visibility="collapsed",
    )
    st.session_state.provider = provider

    # Info sumber data
    st.divider()
    src = db.data_source(role)
    df_main = st.session_state.uploaded_df if (is_officer and st.session_state.uploaded_df is not None) else db.load(role)
    st.caption(f"Sumber data: **{src}**")
    st.caption(f"Baris: {len(df_main):,}")
    if is_officer:
        if st.button("🔌 Tes Koneksi MySQL", use_container_width=True):
            ok, msg = db.test_connection()
            if ok:
                st.success(msg)
            else:
                st.error(msg)

    # Upload data baru (petugas)
    if is_officer:
        st.divider()
        st.markdown("**Upload Data Terbaru**")
        uploaded = st.file_uploader("Upload CSV baru", type=["csv"])
        if uploaded:
            try:
                import pandas as pd
                df_new = pd.read_csv(uploaded)
                st.success(f"Dimuat: {len(df_new):,} baris")
                st.session_state.uploaded_df = df_new
            except Exception as e:
                st.error(f"Gagal: {e}")
        if st.session_state.uploaded_df is not None:
            if st.button("Hapus data upload", use_container_width=True):
                st.session_state.uploaded_df = None
                st.rerun()

    st.divider()
    if st.button("🚪 Keluar / Ganti Peran", use_container_width=True):
        reset()
        st.rerun()

# Judul per peran
if is_officer:
    st.subheader("🛡️ Analisis Data Frekuensi Radio")
    st.caption("Akses penuh ke seluruh database izin spektrum.")
else:
    st.subheader("🏙️ Informasi Spektrum Frekuensi")
    st.caption("Informasi umum tentang layanan radio di wilayah DIY dan Jawa Tengah.")

# Riwayat chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
placeholder = (
    "Tanyakan frekuensi, perangkat, masa berlaku izin, anomali data..."
    if is_officer else
    "Tanyakan layanan radio di kota atau wilayah tertentu..."
)
user_input = st.chat_input(placeholder)

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("Menganalisis..."):
            try:
                df = df_main
                context = rag.retrieve(user_input, df, k=5)
                if not context:
                    context = db.summary(role)
                messages = prompts.build_messages(user_input, context, role)
                answer = llm.ask(messages, provider=st.session_state.provider)
                st.markdown(answer)
                st.session_state.chat_history.append({"role": "assistant", "content": answer})
            except Exception as e:
                err = f"Terjadi kesalahan: {e}"
                st.error(err)
                st.session_state.chat_history.append({"role": "assistant", "content": err})
