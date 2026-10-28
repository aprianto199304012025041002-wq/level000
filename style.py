"""CSS kustom untuk PAIDI-INSIGHT."""

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=Space+Grotesk:wght@400;500;700&display=swap');

html, body, [class*="css"] { font-family: 'Plus Jakarta Sans', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.stDeployButton { display: none; }
.block-container { padding-top: 1.5rem !important; max-width: 880px; }

:root {
    --navy:   #0D2B55;
    --blue:   #1565C0;
    --signal: #00B4D8;
    --border: #CBD5E1;
    --grey:   #64748B;
    --green:  #16A34A;
    --red:    #DC2626;
    --amber:  #D97706;
}

.paidi-header {
    background: linear-gradient(135deg, #0D2B55 0%, #1A4A8A 100%);
    border-radius: 12px;
    padding: 1.4rem 1.8rem;
    margin-bottom: 1rem;
    position: relative;
    overflow: hidden;
}
.paidi-header::after {
    content: '';
    position: absolute;
    right: -30px; top: -30px;
    width: 180px; height: 180px;
    border-radius: 50%;
    background: rgba(0,180,216,0.12);
}
.paidi-title {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.7rem;
    font-weight: 700;
    color: #FFFFFF;
    margin: 0 0 0.25rem 0;
    letter-spacing: -0.02em;
}
.paidi-badge {
    display: inline-block;
    background: rgba(0,180,216,0.25);
    color: #00B4D8;
    font-size: 0.68rem;
    font-weight: 600;
    padding: 2px 8px;
    border-radius: 20px;
    margin-bottom: 0.5rem;
    letter-spacing: 0.04em;
}
.paidi-subtitle {
    font-size: 0.8rem;
    color: rgba(255,255,255,0.65);
    margin: 0;
}

.stat-row { display: flex; gap: 12px; margin-bottom: 1rem; }
.stat-card {
    flex: 1;
    background: #fff;
    border: 1px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1rem;
    text-align: center;
}
.stat-number {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.5rem;
    font-weight: 700;
    color: var(--navy);
    line-height: 1.1;
}
.stat-label { font-size: 0.72rem; color: var(--grey); margin-top: 2px; }
.green .stat-number { color: var(--green); }
.red   .stat-number { color: var(--red); }
.amber .stat-number { color: var(--amber); }

.freq-bar { display: flex; gap: 3px; height: 5px; border-radius: 3px; overflow: hidden; margin: 0.6rem 0 1rem; }
.freq-bar span { flex: 1; }

.stButton > button {
    background: var(--navy) !important;
    color: white !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
}
.stButton > button:hover { background: var(--blue) !important; }
</style>
"""

HEADER_HTML = """
<div class="paidi-header">
    <div class="paidi-badge">📡 BALMON KELAS I YOGYAKARTA</div>
    <div class="paidi-title">PAIDI-INSIGHT</div>
    <div class="paidi-subtitle">
        Platform AI Informasi Spektrum Frekuensi Radio &nbsp;·&nbsp;
        Ditjen SDPPI · Kementerian Komunikasi dan Digital RI
    </div>
</div>
"""

FREQ_BAR = (
    '<div class="freq-bar">'
    + "".join(
        f'<span style="background:{c}"></span>'
        for c in ["#0D2B55","#1565C0","#0077B6","#00B4D8",
                  "#48CAE4","#90E0EF","#48CAE4","#00B4D8","#0077B6","#1565C0"]
    )
    + "</div>"
)


def stat_cards_html(total: int, active: int, expired: int, unknown: int) -> str:
    return f"""
<div class="stat-row">
  <div class="stat-card">
    <div class="stat-number">{total:,}</div>
    <div class="stat-label">Total Izin</div>
  </div>
  <div class="stat-card green">
    <div class="stat-number">{active:,}</div>
    <div class="stat-label">Masih Berlaku</div>
  </div>
  <div class="stat-card red">
    <div class="stat-number">{expired:,}</div>
    <div class="stat-label">Sudah Expired</div>
  </div>
  <div class="stat-card amber">
    <div class="stat-number">{unknown:,}</div>
    <div class="stat-label">Tidak Diketahui</div>
  </div>
</div>"""
