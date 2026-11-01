"""CSS dan komponen HTML untuk PAIDI-INSIGHT."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=Inter:wght@300;400;500;600&display=swap');

/* ── Responsive breakpoints ── */

/* Mobile portrait */
@media (max-width: 479px) {
    .block-container { padding: 0.7rem 0.7rem 2rem !important; }
    .pi-header { padding: 0.8rem 1rem; border-radius: 10px; }
    .pi-logo { font-size: 1.05rem; }
    .pi-meta { font-size: 0.58rem; }
    .freq-bar { margin-bottom: 0.7rem; }

    /* Bento 2x2 tetap, tapi lebih compact */
    [data-testid="stHorizontalBlock"] { gap: 0.4rem !important; }

    /* Bento total card: angka lebih kecil */
    .pi-total-num { font-size: 2.2rem !important; }
    .pi-total-wrap { padding: 1rem !important; border-radius: 10px !important; }
    .pi-total-sub { font-size: 0.65rem !important; }
    .pi-info-grid { grid-template-columns: 1fr 1fr !important; gap: .5rem !important; }
    .pi-info-val { font-size: 1rem !important; }

    /* Chat */
    .chat-header { padding: 0.5rem 0.7rem; border-radius: 8px; }
    .chat-header-title { font-size: 0.82rem; }
    .welcome-box { padding: 1.5rem 0.5rem; }
    .welcome-box .wi { font-size: 1.8rem; }
    .welcome-box h3 { font-size: 0.9rem; }
    .chip { font-size: 0.7rem; padding: 4px 9px; }
}

/* Mobile landscape & tablet */
@media (min-width: 480px) and (max-width: 767px) {
    .block-container { padding: 0.9rem 1rem 2rem !important; }
    .pi-logo { font-size: 1.2rem; }
    .pi-total-num { font-size: 2.5rem !important; }

    /* Biarkan 2 kolom tapi lebih rapat */
    [data-testid="stHorizontalBlock"] { gap: 0.6rem !important; }
}

/* Tablet besar & desktop */
@media (min-width: 768px) {
    .block-container { max-width: 960px !important; }
    .pi-total-num { font-size: 3rem; }
}

/* ── Reset ── */
html, body, [class*="css"] { font-family: 'Inter', sans-serif !important; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container {
    padding: 1.2rem 1.5rem 2rem !important;
    max-width: 960px !important;
}

/* ── Tokens ── */
:root {
    --navy:    #0D2B55;
    --blue:    #1565C0;
    --signal:  #00B4D8;
    --sky:     #E0F7FA;
    --surface: #F8FAFC;
    --border:  #E2E8F0;
    --grey:    #64748B;
    --green:   #16A34A;
    --green-bg:#DCFCE7;
    --red:     #DC2626;
    --red-bg:  #FEE2E2;
    --amber:   #D97706;
    --amber-bg:#FEF3C7;
    --white:   #FFFFFF;
}

/* ── Header strip ── */
.pi-header {
    background: var(--navy);
    border-radius: 14px;
    padding: 1.1rem 1.6rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.8rem;
    position: relative;
    overflow: hidden;
}
.pi-header::before {
    content: '';
    position: absolute;
    right: -40px; top: -40px;
    width: 200px; height: 200px;
    background: radial-gradient(circle, rgba(0,180,216,0.18) 0%, transparent 70%);
}
.pi-logo {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.55rem;
    font-weight: 800;
    color: #fff;
    letter-spacing: -0.03em;
    line-height: 1;
}
.pi-logo span { color: var(--signal); }
.pi-meta {
    font-size: 0.7rem;
    color: rgba(255,255,255,0.55);
    text-align: right;
    line-height: 1.5;
}

/* ── Plotly chart container: jangan dipotong ── */
[data-testid="stPlotlyChart"] {
    overflow: visible !important;
}
[data-testid="stPlotlyChart"] > div {
    overflow: visible !important;
}
/* Bento panel: biarkan chart berkembang */
[data-testid="stVerticalBlockBorderWrapper"] {
    overflow: visible !important;
}
@media (max-width: 479px) {
    .block-container { max-width: 100% !important; }
}

/* ── Frekuensi bar ── */
.freq-bar {
    height: 4px;
    border-radius: 2px;
    background: linear-gradient(90deg,
        #0D2B55 0%, #1565C0 20%, #0077B6 35%,
        #00B4D8 50%, #48CAE4 65%, #00B4D8 80%,
        #1565C0 90%, #0D2B55 100%);
    margin-bottom: 1.1rem;
    opacity: 0.7;
}

/* ── Bento grid ── */
.bento-grid {
    display: grid;
    grid-template-columns: 1fr 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 10px;
    margin-bottom: 1.2rem;
}
.bento-card {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 1rem 1.1rem;
    position: relative;
    overflow: hidden;
}
.bento-card.span2 { grid-column: span 2; }
.bento-card.navy  { background: var(--navy); border-color: var(--navy); }
.bento-card.sky   { background: var(--sky);  border-color: #B2EBF2; }

.bento-label {
    font-size: 0.68rem;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    color: var(--grey);
    margin-bottom: 0.3rem;
}
.bento-card.navy .bento-label { color: rgba(255,255,255,0.55); }
.bento-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 2.2rem;
    font-weight: 700;
    color: var(--navy);
    line-height: 1;
}
.bento-card.navy .bento-number { color: #fff; }
.bento-sub {
    font-size: 0.72rem;
    color: var(--grey);
    margin-top: 0.25rem;
}
.bento-card.navy .bento-sub { color: rgba(255,255,255,0.5); }

.badge-pill {
    display: inline-block;
    font-size: 0.65rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    margin-top: 0.35rem;
}
.badge-green  { background: var(--green-bg); color: var(--green); }
.badge-red    { background: var(--red-bg);   color: var(--red); }
.badge-amber  { background: var(--amber-bg); color: var(--amber); }
.badge-signal { background: var(--sky);      color: #0077B6; }

/* ── Role cards ── */
.role-wrap { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-bottom: 1rem; }
.role-card {
    background: var(--white);
    border: 1.5px solid var(--border);
    border-radius: 12px;
    padding: 1.2rem;
    cursor: pointer;
    transition: border-color .2s, box-shadow .2s;
}
.role-card:hover { border-color: var(--signal); box-shadow: 0 4px 16px rgba(0,180,216,.12); }
.role-icon { font-size: 1.6rem; margin-bottom: 0.5rem; }
.role-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 0.95rem;
    color: var(--navy); margin-bottom: 0.3rem;
}
.role-desc { font-size: 0.78rem; color: var(--grey); line-height: 1.55; }

/* ── Chat header strip ── */
.chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0.65rem 1rem;
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 10px;
    margin-bottom: 0.8rem;
}
.chat-header-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700; font-size: 0.9rem; color: var(--navy);
}
.chat-header-sub { font-size: 0.7rem; color: var(--grey); }

/* ── Chat bubbles ── */
[data-testid="stChatMessage"] {
    border-radius: 12px !important;
    padding: 0.6rem 0.8rem !important;
    margin-bottom: 0.5rem !important;
    border: none !important;
    background: transparent !important;
}
[data-testid="stChatMessage"][data-role="user"] {
    background: var(--sky) !important;
    border-left: 3px solid var(--signal) !important;
}
[data-testid="stChatMessage"][data-role="assistant"] {
    background: var(--surface) !important;
    border-left: 3px solid var(--border) !important;
}
.stChatMessage p { font-size: 0.88rem !important; line-height: 1.6 !important; }

/* ── Chat input ── */
[data-testid="stChatInput"] {
    border-radius: 10px !important;
    border-color: var(--border) !important;
    font-size: 0.88rem !important;
}
[data-testid="stChatInput"]:focus-within {
    border-color: var(--signal) !important;
    box-shadow: 0 0 0 3px rgba(0,180,216,0.12) !important;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: var(--surface) !important;
    border-right: 1px solid var(--border) !important;
}
[data-testid="stSidebar"] .block-container { padding: 1rem !important; }

/* ── Tombol ── */
.stButton > button {
    background: var(--navy) !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
    font-size: 0.83rem !important;
    font-weight: 600 !important;
    padding: 0.45rem 1rem !important;
    transition: background .2s !important;
}
.stButton > button:hover { background: var(--blue) !important; }

/* ── Mode badge ── */
.mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.75rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
}
.mode-officer { background: #DCFCE7; color: #15803D; }
.mode-public  { background: #DBEAFE; color: #1D4ED8; }

/* ── Container border Streamlit (bento panel) ── */
[data-testid="stVerticalBlockBorderWrapper"] {
    border-radius: 14px !important;
    border-color: #E2E8F0 !important;
    box-shadow: 0 1px 4px rgba(0,0,0,0.06) !important;
    overflow: hidden;
}

/* ── Welcome message ── */
.welcome-box {
    text-align: center;
    padding: 2.5rem 1rem;
    color: var(--grey);
}
.welcome-box .wi { font-size: 2.5rem; margin-bottom: 0.6rem; }
.welcome-box h3 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.05rem;
    color: var(--navy);
    font-weight: 700;
    margin-bottom: 0.4rem;
}
.welcome-box p { font-size: 0.8rem; line-height: 1.6; max-width: 380px; margin: 0 auto; }

/* ── Suggestion chips ── */
.chip-row { display: flex; flex-wrap: wrap; gap: 7px; justify-content: center; margin-top: 1rem; }
.chip {
    background: var(--white);
    border: 1px solid var(--border);
    border-radius: 20px;
    padding: 5px 12px;
    font-size: 0.75rem;
    color: var(--navy);
    cursor: pointer;
    font-weight: 500;
    transition: border-color .2s;
}
.chip:hover { border-color: var(--signal); color: var(--signal); }
</style>
"""
