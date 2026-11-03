"""PAIDI-INSIGHT — redesign total: bento stats + modern AI chat."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from core import analyst, auth, db, llm, prompts, rag, session
from ui import charts, style, dashboard

st.set_page_config(
    page_title="PAIDI-INSIGHT",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="collapsed",
)
st.markdown(style.CSS, unsafe_allow_html=True)

# ── State ────────────────────────────────────────────────────────────────────
for k, v in [("role", None), ("auth_failed", False),
             ("chat_history", []), ("provider", "gemini"), ("uploaded_df", None)]:
    if k not in st.session_state:
        st.session_state[k] = v


def reset():
    st.session_state.update(role=None, auth_failed=False,
                            chat_history=[], uploaded_df=None)


# ── Header (selalu tampil) ────────────────────────────────────────────────────
st.markdown(style.HEADER_HTML, unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 1 — Landing: Bento + Pilih Peran
# ════════════════════════════════════════════════════════════════════════════
if st.session_state.role is None:

    # ── Bento 2x2 ────────────────────────────────────────────────────────
    dashboard.render()

    # Pilih peran
    st.markdown("""
    <div style="display:flex;align-items:center;gap:10px;margin-bottom:1rem">
        <div style="height:2px;flex:1;background:linear-gradient(90deg,transparent,#00B4D8)"></div>
        <div style="font-family:'Space Grotesk',sans-serif;font-size:.75rem;font-weight:600;
                    letter-spacing:.12em;color:#64748B;text-transform:uppercase">Pilih Mode Akses</div>
        <div style="height:2px;flex:1;background:linear-gradient(90deg,#00B4D8,transparent)"></div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2, gap="small")

    with col1:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#EFF6FF 0%,#DBEAFE 100%);
                    border:1.5px solid #BFDBFE;border-radius:14px;padding:1.2rem;
                    margin-bottom:.6rem;min-height:140px">
            <div style="width:42px;height:42px;background:linear-gradient(135deg,#1565C0,#00B4D8);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;
                        font-size:1.2rem;margin-bottom:.7rem">🏙️</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:.95rem;
                        color:#0D2B55;margin-bottom:.3rem">Masyarakat Umum</div>
            <div style="font-size:.78rem;color:#475569;line-height:1.5">
                Informasi umum stasiun radio dan pemegang izin di wilayah DIY &amp; Jawa Tengah.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("→ Masuk sebagai Masyarakat", use_container_width=True, key="btn_pub"):
            st.session_state.role = "public"
            st.session_state.chat_history = []
            session.init("public")
            st.rerun()

    with col2:
        st.markdown("""
        <div style="background:linear-gradient(135deg,#F0FDF4 0%,#DCFCE7 100%);
                    border:1.5px solid #BBF7D0;border-radius:14px;padding:1.2rem;
                    margin-bottom:.6rem;min-height:140px">
            <div style="width:42px;height:42px;background:linear-gradient(135deg,#15803D,#16A34A);
                        border-radius:10px;display:flex;align-items:center;justify-content:center;
                        font-size:1.2rem;margin-bottom:.7rem">🛡️</div>
            <div style="font-family:'Space Grotesk',sans-serif;font-weight:700;font-size:.95rem;
                        color:#0D2B55;margin-bottom:.3rem">Petugas Pengendali</div>
            <div style="font-size:.78rem;color:#475569;line-height:1.5">
                Akses penuh data teknis, frekuensi, analisis, dan pengelolaan database spektrum.</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=True):
            pwd = st.text_input("Password", type="password",
                                placeholder="🔑  Password petugas",
                                label_visibility="collapsed")
            if st.form_submit_button("→ Masuk sebagai Petugas", use_container_width=True):
                if auth.check_officer_password(pwd):
                    st.session_state.update(role="officer", auth_failed=False,
                                            chat_history=[])
                    session.init("officer")
                    st.rerun()
                else:
                    st.session_state.auth_failed = True

    if st.session_state.auth_failed:
        st.error("❌ Password salah. Silakan coba lagi.")

    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 2 — Chat
# ════════════════════════════════════════════════════════════════════════════
role       = st.session_state.role
is_officer = role == "officer"
uploaded_df = st.session_state.uploaded_df if is_officer else None

# Pulihkan atau buat sesi baru
if "session_id" not in st.session_state:
    session.init(role)

# ── Sidebar kompak ────────────────────────────────────────────────────────
with st.sidebar:
    badge_cls  = "mode-officer" if is_officer else "mode-public"
    badge_icon = "🛡️" if is_officer else "🏙️"
    badge_text = "Petugas Pengendali" if is_officer else "Masyarakat Umum"
    st.markdown(
        f'<div class="mode-badge {badge_cls}">{badge_icon} {badge_text}</div>',
        unsafe_allow_html=True,
    )

    src = db.data_source(role)
    try:
        s = db.stats_for_header()
        total = s["TOTAL"]
    except Exception:
        total = 0
    if src == "CSV lokal":
        st.warning("⚠️ MySQL tidak tersedia, menggunakan data CSV lokal.", icon="⚠️")
    st.caption(f"📊 **{src}** · {total:,} izin")
    if st.button("🔄 Refresh data", use_container_width=True, key="refresh_data"):
        db._mysql_ok = None  # reset cache koneksi
        st.cache_data.clear()
        st.rerun()

    st.divider()

    # Selector model
    st.markdown('<div style="font-size:0.78rem;font-weight:600;color:#0D2B55;margin-bottom:4px">Model AI</div>', unsafe_allow_html=True)
    provider = st.radio("model", ["gemini", "qwen"],
                        format_func=lambda x: "✨ Gemini" if x == "gemini" else "🧠 Qwen",
                        index=0 if st.session_state.provider == "gemini" else 1,
                        label_visibility="collapsed")
    st.session_state.provider = provider

    if is_officer:
        st.divider()
        st.markdown('<div style="font-size:0.78rem;font-weight:600;color:#0D2B55;margin-bottom:4px">Upload Data</div>', unsafe_allow_html=True)
        uploaded = st.file_uploader("CSV", type=["csv"], label_visibility="collapsed")
        if uploaded:
            try:
                df_new = pd.read_csv(uploaded)
                df_new.columns = [c.strip().upper() for c in df_new.columns]
                st.success(f"✓ {len(df_new):,} baris dimuat")
                st.session_state.uploaded_df = df_new
                uploaded_df = df_new
            except Exception as e:
                st.error(str(e))
        if st.session_state.uploaded_df is not None:
            if st.button("Hapus upload", use_container_width=True):
                st.session_state.uploaded_df = None
                st.rerun()

        st.divider()
        if st.button("🔌 Tes MySQL", use_container_width=True):
            ok, msg = db.test_connection()
            (st.success if ok else st.error)(msg)

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("🗑️ Hapus Chat", use_container_width=True):
            session.clear(role)
            st.rerun()
    with col_b:
        if st.button("← Keluar", use_container_width=True):
            reset()
            st.rerun()

    n_msg = len(st.session_state.chat_history)
    if n_msg > 0:
        st.caption(f"💬 {n_msg} pesan dalam sesi ini")
    err = db.last_mysql_error()
    if err:
        st.warning(f"MySQL: {err}", icon="⚠️")

# ── Chat header ───────────────────────────────────────────────────────────
desc = ("Analisis teknis data spektrum" if is_officer
        else "Informasi umum spektrum frekuensi")
st.markdown(f"""
<div class="chat-header">
    <div>
        <div class="chat-header-title">
            {"🛡️ Mode Petugas" if is_officer else "🏙️ Mode Masyarakat"}
        </div>
        <div class="chat-header-sub">{desc} · {src}</div>
    </div>
    <div style="font-size:0.7rem;color:#64748B">
        {'✨ Gemini' if provider == 'gemini' else '🧠 Qwen'}
    </div>
</div>
""", unsafe_allow_html=True)

# ── Pesan selamat datang + chip yang bisa diklik ─────────────────
if not st.session_state.chat_history:
    st.markdown(style.welcome_html(role, chips=False), unsafe_allow_html=True)
    if role == "public":
        chips = ["Layanan radio apa saja di Bantul?","Siapa pemegang izin di Sleman?","Apa itu Fixed Service?"]
    else:
        chips = ["Berapa izin yang sudah expired?","Stasiun ERP tertinggi?","Rekap izin per layanan","Izin di frekuensi 150 MHz?"]
    st.markdown('<div class="pi-chips"></div>', unsafe_allow_html=True)
    chip_cols = st.columns(len(chips))
    for i, chip in enumerate(chips):
        with chip_cols[i]:
            if st.button(chip, key=f"chip_{i}", use_container_width=True):
                session.append("user", chip)
                with st.chat_message("assistant", avatar="📡"):
                    try:
                        ctx = analyst.build_context(chip, uploaded_df, role)
                        if not ctx:
                            ctx = rag.retrieve(chip, uploaded_df, k=5)
                        if not ctx:
                            ctx = db.summary(role)
                        msgs = prompts.build_messages(chip, ctx, role, history=st.session_state.chat_history)
                        ans = st.write_stream(llm.ask_stream(msgs, provider=st.session_state.provider))
                        session.append("assistant", str(ans))
                    except Exception as ce:
                        err = f"Terjadi kesalahan: {ce}"
                        st.error(err)
                        session.append("assistant", err)
                st.rerun()

# ── Riwayat chat ─────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"],
                         avatar="🧑" if msg["role"] == "user" else "📡"):
        st.markdown(msg["content"])
        if msg.get("ts"):
            st.caption(msg["ts"])

# ── Input ─────────────────────────────────────────────────────────────────
placeholder = (
    "Tanyakan frekuensi, masa berlaku, ERP, anomali..."
    if is_officer else
    "Tanyakan layanan radio di wilayah Anda..."
)
user_input = st.chat_input(placeholder)

if user_input:
    if len(user_input) > 500:
        st.warning("Pertanyaan terlalu panjang (maks 500 karakter). Persingkat pertanyaanmu.")
        st.stop()
    session.append("user", user_input)
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="📡"):
        try:
            context = analyst.build_context(user_input, uploaded_df, role)
            if not context:
                context = rag.retrieve(user_input, uploaded_df, k=5)
            if not context:
                context = db.summary(role)
            messages = prompts.build_messages(user_input, context, role, history=st.session_state.chat_history)
            # Streaming: token muncul satu per satu
            answer = st.write_stream(
                llm.ask_stream(messages, provider=provider)
            )
            session.append("assistant", str(answer))
            # Tampilkan model yang menjawab + timestamp
            _prov = provider or "gemini"
            st.caption(f"{'✨ Gemini' if _prov=='gemini' else '🧠 Qwen'} · {session._last_ts()}")
        except Exception as e:
            msg = str(e)
            if "quota" in msg.lower() or "429" in msg:
                err_msg = "⚠️ Kuota API habis. Coba beberapa saat lagi."
            elif "api key" in msg.lower() or "api_key" in msg.lower():
                err_msg = "⚠️ API key tidak valid atau belum diisi di Secrets."
            elif "kedua model gagal" in msg.lower():
                err_msg = f"⚠️ Gemini dan Qwen keduanya tidak tersedia. Detail: {msg}"
            else:
                err_msg = f"Terjadi kesalahan: {msg}"
            st.error(err_msg)
            session.append("assistant", err_msg)
