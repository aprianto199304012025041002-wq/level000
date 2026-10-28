"""PAIDI-INSIGHT — redesign total: bento stats + modern AI chat."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analyst
import auth
import db
import llm
import prompts
import rag
import style

st.set_page_config(
    page_title="PAIDI-INSIGHT",
    page_icon="📡",
    layout="centered",
    initial_sidebar_state="auto",
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

    # Statistik bento
    try:
        s = db.stats_for_header()

        # Coba ambil layanan terbesar
        try:
            svc_df = db.execute(
                "SELECT service, COUNT(*) AS cnt FROM isr "
                "GROUP BY service ORDER BY cnt DESC LIMIT 1"
            )
            top_svc   = str(svc_df.iloc[0]["SERVICE"]).replace("Service","Svc").strip()
            top_count = int(svc_df.iloc[0]["CNT"])
        except Exception:
            top_svc, top_count = "Fixed Service", 6107

        st.markdown(
            style.bento_html(s["TOTAL"], s["ACTIVE"], s["EXPIRED"],
                             s["UNKNOWN"], top_svc, top_count, 2),
            unsafe_allow_html=True,
        )

        # Grafik Plotly mini — donut + bar horizontal
        c1, c2 = st.columns([1, 1.4])

        with c1:
            fig_donut = go.Figure(go.Pie(
                labels=["Aktif", "Expired", "Tdk diketahui"],
                values=[s["ACTIVE"], s["EXPIRED"], s["UNKNOWN"]],
                hole=0.62,
                marker_colors=["#16A34A", "#DC2626", "#D97706"],
                textinfo="none",
                hovertemplate="%{label}: %{value:,}<extra></extra>",
            ))
            fig_donut.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                height=160,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                showlegend=True,
                legend=dict(font=dict(size=10), orientation="v",
                            x=1, y=0.5, xanchor="left"),
                annotations=[dict(text=f"<b>{s['TOTAL']:,}</b>", x=0.5, y=0.5,
                                  font_size=13, showarrow=False, font_color="#0D2B55")],
            )
            st.plotly_chart(fig_donut, use_container_width=True, config={"displayModeBar": False})

        with c2:
            try:
                svc_all = db.execute(
                    "SELECT service, COUNT(*) AS cnt FROM isr "
                    "GROUP BY service ORDER BY cnt ASC"
                )
                fig_bar = go.Figure(go.Bar(
                    x=svc_all["CNT"].tolist(),
                    y=svc_all["SERVICE"].tolist(),
                    orientation="h",
                    marker_color="#00B4D8",
                    text=svc_all["CNT"].apply(lambda v: f"{int(v):,}"),
                    textposition="outside",
                    hovertemplate="%{y}: %{x:,}<extra></extra>",
                ))
                fig_bar.update_layout(
                    margin=dict(t=10, b=10, l=10, r=40),
                    height=160,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    xaxis=dict(visible=False),
                    yaxis=dict(tickfont=dict(size=10)),
                    font=dict(family="Inter"),
                )
                st.plotly_chart(fig_bar, use_container_width=True, config={"displayModeBar": False})
            except Exception:
                pass

    except Exception:
        pass

    # Pilih peran
    st.markdown("### Masuk sebagai")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">🏙️</div>
            <div class="role-title">Masyarakat Umum</div>
            <div class="role-desc">Informasi umum — nama stasiun, pemegang izin,
            dan layanan radio di wilayah Anda.</div>
        </div>""", unsafe_allow_html=True)
        if st.button("Masuk sebagai Masyarakat", use_container_width=True, key="btn_pub"):
            st.session_state.role = "public"
            st.session_state.chat_history = []
            st.rerun()

    with col2:
        st.markdown("""
        <div class="role-card">
            <div class="role-icon">🛡️</div>
            <div class="role-title">Petugas Pengendali</div>
            <div class="role-desc">Akses penuh — frekuensi, masa berlaku,
            ERP, analisis teknis, dan pengelolaan database.</div>
        </div>""", unsafe_allow_html=True)
        with st.form("login_form", clear_on_submit=True):
            pwd = st.text_input("Password", type="password",
                                placeholder="Masukkan password petugas",
                                label_visibility="collapsed")
            if st.form_submit_button("Masuk sebagai Petugas", use_container_width=True):
                if auth.check_officer_password(pwd):
                    st.session_state.update(role="officer", auth_failed=False,
                                            chat_history=[])
                    st.rerun()
                else:
                    st.session_state.auth_failed = True

    if st.session_state.auth_failed:
        st.error("Password salah. Silakan coba lagi.")

    st.stop()

# ════════════════════════════════════════════════════════════════════════════
# LAYAR 2 — Chat
# ════════════════════════════════════════════════════════════════════════════
role       = st.session_state.role
is_officer = role == "officer"
uploaded_df = st.session_state.uploaded_df if is_officer else None

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
    st.caption(f"📊 **{src}** · {total:,} izin")

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
    if st.button("← Ganti Peran", use_container_width=True):
        reset()
        st.rerun()

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

# ── Pesan selamat datang (hanya saat history kosong) ─────────────────────
if not st.session_state.chat_history:
    st.markdown(style.welcome_html(role), unsafe_allow_html=True)

# ── Riwayat chat ─────────────────────────────────────────────────────────
for msg in st.session_state.chat_history:
    with st.chat_message(msg["role"],
                         avatar="🧑" if msg["role"] == "user" else "📡"):
        st.markdown(msg["content"])

# ── Input ─────────────────────────────────────────────────────────────────
placeholder = (
    "Tanyakan frekuensi, masa berlaku, ERP, anomali..."
    if is_officer else
    "Tanyakan layanan radio di wilayah Anda..."
)
user_input = st.chat_input(placeholder)

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user", avatar="🧑"):
        st.markdown(user_input)

    with st.chat_message("assistant", avatar="📡"):
        with st.spinner(""):
            try:
                context = analyst.build_context(user_input, uploaded_df, role)
                if not context:
                    context = rag.retrieve(user_input, uploaded_df, k=5)
                if not context:
                    context = db.summary(role)
                messages = prompts.build_messages(user_input, context, role)
                answer = llm.ask(messages, provider=provider)
                st.markdown(answer)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": answer}
                )
            except Exception as e:
                err_msg = f"Terjadi kesalahan: {e}"
                st.error(err_msg)
                st.session_state.chat_history.append(
                    {"role": "assistant", "content": err_msg}
                )
