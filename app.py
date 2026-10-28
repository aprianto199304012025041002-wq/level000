"""PAIDI-INSIGHT — Streamlit app: dua peran, multi-model, MySQL/CSV."""
import datetime

import pandas as pd
import streamlit as st

import analyst
import auth
import db
import llm
import prompts
import rag
import style

st.set_page_config(page_title="PAIDI-INSIGHT", page_icon="📡", layout="centered")
st.markdown(style.CSS, unsafe_allow_html=True)

# ── State ────────────────────────────────────────────────────────────────────
for k, v in [("role", None), ("auth_failed", False),
             ("chat_history", []), ("provider", "gemini"), ("uploaded_df", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


def reset():
    st.session_state.update(
        role=None, auth_failed=False, chat_history=[], uploaded_df=None
    )


# ── Header ───────────────────────────────────────────────────────────────────
st.markdown(style.HEADER_HTML, unsafe_allow_html=True)
st.markdown(style.FREQ_BAR, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 1: Pilih Peran + Statistik
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.role is None:

    # Statistik ringkas dari MySQL/CSV
    try:
        s = db.stats_for_header()
        st.markdown(
            style.stat_cards_html(s["TOTAL"], s["ACTIVE"], s["EXPIRED"], s["UNKNOWN"]),
            unsafe_allow_html=True,
        )
    except Exception:
        pass

    st.subheader("Silakan pilih peran Anda")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div style='background:#EFF6FF;border:1.5px solid #BFDBFE;
                    border-radius:12px;padding:1.2rem;margin-bottom:0.8rem'>
            <div style='font-size:1.8rem;margin-bottom:0.4rem'>🏙️</div>
            <div style='font-weight:700;color:#1E3A5F;font-size:1rem;margin-bottom:0.3rem'>
                Masyarakat Umum</div>
            <div style='font-size:0.8rem;color:#475569;line-height:1.5'>
                Informasi umum stasiun radio dan pemegang izin di wilayah DIY dan Jawa Tengah.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Masuk sebagai Masyarakat", use_container_width=True):
            st.session_state.role = "public"
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        st.markdown("""
        <div style='background:#F0FDF4;border:1.5px solid #BBF7D0;
                    border-radius:12px;padding:1.2rem;margin-bottom:0.8rem'>
            <div style='font-size:1.8rem;margin-bottom:0.4rem'>🛡️</div>
            <div style='font-weight:700;color:#1E3A5F;font-size:1rem;margin-bottom:0.3rem'>
                Petugas Pengendali</div>
            <div style='font-size:0.8rem;color:#475569;line-height:1.5'>
                Akses penuh analisis data teknis, frekuensi, dan pengelolaan database spektrum.</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form"):
            password = st.text_input("Password Petugas", type="password",
                                     placeholder="Masukkan password")
            submitted = st.form_submit_button("Masuk sebagai Petugas",
                                              use_container_width=True)
            if submitted:
                if auth.check_officer_password(password):
                    st.session_state.update(role="officer", auth_failed=False,
                                            chat_history=[])
                    st.rerun()
                else:
                    st.session_state.auth_failed = True

    if st.session_state.auth_failed:
        st.error("Password salah. Silakan coba lagi.")

    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 2: Chat
# ════════════════════════════════════════════════════════════════════════════
role      = st.session_state.role
is_officer = role == "officer"

# Sidebar
with st.sidebar:
    badge_cls  = "officer" if is_officer else "public"
    badge_icon = "🛡️" if is_officer else "🏙️"
    badge_text = "Mode Petugas" if is_officer else "Mode Masyarakat"
    st.markdown(
        f'<div class="mode-badge {badge_cls}" '
        f'style="display:inline-flex;align-items:center;gap:6px;padding:5px 12px;'
        f'border-radius:20px;font-size:0.82rem;font-weight:600;'
        f'background:{("#DCFCE7" if is_officer else "#DBEAFE")};'
        f'color:{("#15803D" if is_officer else "#1D4ED8")}">'
        f'{badge_icon} {badge_text}</div>',
        unsafe_allow_html=True,
    )

    st.divider()
    st.markdown("**Model AI**")
    provider = st.radio(
        "Model",
        options=["gemini", "qwen"],
        format_func=lambda x: "✨ Gemini (Google)" if x == "gemini" else "🧠 Qwen (Alibaba)",
        index=0 if st.session_state.provider == "gemini" else 1,
        label_visibility="collapsed",
    )
    st.session_state.provider = provider

    st.divider()
    uploaded_df = st.session_state.uploaded_df if is_officer else None
    src = db.data_source(role)
    try:
        s = db.stats_for_header()
        total = s["TOTAL"]
    except Exception:
        total = 0
    st.caption(f"Sumber: **{src}** · {total:,} baris")

    mysql_err = db.last_mysql_error()
    if mysql_err:
        st.warning(f"MySQL: {mysql_err}")

    if is_officer:
        if st.button("🔌 Tes Koneksi MySQL", use_container_width=True):
            ok, msg = db.test_connection()
            (st.success if ok else st.error)(msg)

        st.divider()
        st.markdown("**Upload Data Terbaru**")
        uploaded = st.file_uploader("CSV baru", type=["csv"],
                                    label_visibility="collapsed")
        if uploaded:
            try:
                df_new = pd.read_csv(uploaded)
                df_new.columns = [c.strip().upper() for c in df_new.columns]
                st.success(f"Dimuat: {len(df_new):,} baris")
                st.session_state.uploaded_df = df_new
                uploaded_df = df_new
            except Exception as e:
                st.error(f"Gagal: {e}")
        if st.session_state.uploaded_df is not None:
            if st.button("Hapus upload", use_container_width=True):
                st.session_state.uploaded_df = None
                st.rerun()

    st.divider()
    if st.button("🚪 Keluar / Ganti Peran", use_container_width=True):
        reset()
        st.rerun()

# Judul area chat
if is_officer:
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;color:#0D2B55;margin-bottom:0.2rem'>"
        "🛡️ Analisis Data Frekuensi Radio</div>"
        "<div style='font-size:0.78rem;color:#64748B;margin-bottom:1rem'>"
        "Akses penuh ke seluruh database izin spektrum DIY dan Jawa Tengah.</div>",
        unsafe_allow_html=True,
    )
else:
    st.markdown(
        "<div style='font-size:1rem;font-weight:700;color:#0D2B55;margin-bottom:0.2rem'>"
        "🏙️ Informasi Spektrum Frekuensi</div>"
        "<div style='font-size:0.78rem;color:#64748B;margin-bottom:1rem'>"
        "Tanyakan informasi umum tentang layanan radio di wilayah Anda.</div>",
        unsafe_allow_html=True,
    )

# Riwayat chat
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Input
placeholder = (
    "Tanyakan frekuensi, masa berlaku, ERP, anomali data..."
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
                # uploaded_df diisi hanya jika petugas upload CSV baru
                context = analyst.build_context(user_input, uploaded_df, role)
                if not context:
                    context = rag.retrieve(user_input, uploaded_df, k=5)
                if not context:
                    context = db.summary(role)
                messages = prompts.build_messages(user_input, context, role)
                answer = llm.ask(messages, provider=st.session_state.provider)
                st.markdown(answer)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                err = f"Terjadi kesalahan: {e}"
                st.error(err)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": err}
                )
