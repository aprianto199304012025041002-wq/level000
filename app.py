"""PAIDI-INSIGHT — redesign total: bento stats + modern AI chat."""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import streamlit.components.v1 as components
import analyst
import charts
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

    # ── Bento 2x2 ────────────────────────────────────────────────────────
    try:
        import pandas as pd
        from functools import lru_cache

        # Ambil semua data sekaligus (SQL atau CSV fallback)
        if db._use_mysql():
            # Ambil tanggal query dari data, pakai sebagai acuan aktif/expired
            tgl_row = db.execute("SELECT MAX(tgl_query) AS tgl FROM isr").iloc[0]
            tgl     = str(tgl_row["TGL"] or "-")
            s_row   = db.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(STR_TO_DATE(validity_date, '%%d-%%b-%%y') >= STR_TO_DATE(tgl_query, '%%d-%%b-%%y')) AS active, "
                "SUM(STR_TO_DATE(validity_date, '%%d-%%b-%%y') < STR_TO_DATE(tgl_query, '%%d-%%b-%%y')) AS expired, "
                "SUM(validity_date IS NULL OR validity_date = '') AS unknown "
                "FROM isr"
            ).iloc[0]
            total  = int(s_row["TOTAL"] or 0)
            active = int(s_row["ACTIVE"] or 0)
            expired= int(s_row["EXPIRED"] or 0)
            df_wil = db.execute("SELECT province, city, COUNT(*) AS cnt "
                                "FROM isr GROUP BY province, city")
            df_svc = db.execute("SELECT service, subservice, COUNT(*) AS cnt "
                                "FROM isr GROUP BY service, subservice")
        else:
            df_all = db._load_csv("officer")
            total  = len(df_all)
            vd = pd.to_datetime(df_all.get("VALIDITY_DATE", pd.Series()), errors="coerce")
            import datetime as _dt
            today_ = pd.Timestamp(_dt.date.today())
            active = int((vd >= today_).sum())
            expired= int((vd < today_).sum())
            tgl    = str(df_all["TGL_QUERY"].iloc[0]) if "TGL_QUERY" in df_all.columns else "-"
            df_wil = df_all.groupby(["PROVINCE","CITY"]).size().reset_index(name="cnt")
            df_svc = df_all.groupby(["SERVICE","SUBSERVICE"]).size().reset_index(name="cnt")

        df_wil.columns = [c.upper() for c in df_wil.columns]
        df_svc.columns = [c.upper() for c in df_svc.columns]
        n_prov = df_wil["PROVINCE"].nunique()
        n_kota = df_wil["CITY"].nunique()
        src = db.data_source()

        # ── Baris 1: Total + Tanggal (satu card full width) ────────────
        components.html(f"""
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:transparent;font-family:'Inter',sans-serif}
.card{background:linear-gradient(135deg,#0D2B55 0%,#1565C0 60%,#1A4A8A 100%);
  border-radius:14px;padding:1.3rem 1.6rem;position:relative;overflow:hidden;
  display:flex;align-items:flex-start;justify-content:space-between;gap:1rem;flex-wrap:wrap}
.card::before{content:'';position:absolute;right:-30px;top:-30px;width:180px;height:180px;
  border-radius:50%;background:rgba(0,180,216,0.10)}
.lbl{font-size:.6rem;font-weight:600;letter-spacing:.1em;color:rgba(255,255,255,.4);
  text-transform:uppercase;margin-bottom:.35rem}
.num{font-family:'Space Grotesk','Inter',sans-serif;font-size:3rem;font-weight:700;
  color:#fff;line-height:1;margin-bottom:.4rem}
.clk{font-size:.7rem;color:rgba(255,255,255,.65)}
.rtl{text-align:right}
.lbl2{font-size:.58rem;font-weight:600;letter-spacing:.1em;color:rgba(255,255,255,.4);
  text-transform:uppercase;margin-bottom:.3rem}
.tgl{font-size:1.35rem;font-weight:700;color:#00B4D8;
  font-family:'Space Grotesk','Inter',sans-serif;line-height:1}
.sub{font-size:.58rem;color:rgba(255,255,255,.4);margin-top:.3rem}
</style>
<div class="card">
  <div>
    <div class="lbl">Total Izin Stasiun Radio</div>
    <div class="num">{total:,}</div>
    <div id="clk" class="clk">memuat...</div>
  </div>
  <div class="rtl">
    <div class="lbl2">Data per</div>
    <div class="tgl">{tgl}</div>
    <div class="sub">DIY &amp; Jawa Tengah</div>
  </div>
</div>
<script>
var M=["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Ags","Sep","Okt","Nov","Des"];
var D=["Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"];
function tick(){
  var n=new Date(),j=new Date(n.getTime()+25200000);
  var h=j.getUTCHours(),m=j.getUTCMinutes(),s=j.getUTCSeconds();
  var el=document.getElementById("clk");
  if(el) el.textContent=D[j.getUTCDay()]+", "+
    String(j.getUTCDate()).padStart(2,"0")+" "+M[j.getUTCMonth()]+" "+j.getUTCFullYear()+
    " · "+String(h).padStart(2,"0")+":"+String(m).padStart(2,"0")+":"+
    String(s).padStart(2,"0")+" WIB";
}
tick(); setInterval(tick,1000);
</script>""", height=150)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        # ── Baris 2: Sunburst Wilayah + Sunburst Service ────────────────
        r2c1, r2c2 = st.columns(2, gap="small")
        with r2c1:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_wilayah(df_wil),
                                width='stretch',
                                config={"displayModeBar": False})
        with r2c2:
            with st.container(border=True):
                st.plotly_chart(charts.sunburst_service(df_svc),
                                width="stretch",
                                config={"displayModeBar": False})

        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    except Exception as _e:
        st.caption(f"Dashboard tidak tersedia: {_e}")

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
