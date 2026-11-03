"""HTML komponen untuk PAIDI-INSIGHT."""
from .css import CSS

HEADER_HTML = """
<div class="pi-header">
    <div style="flex:1;min-width:0">
        <div class="pi-logo">
            <span style="color:#fff;font-weight:800;letter-spacing:-.03em">PAIDI</span><span style="color:#00B4D8;font-weight:300;margin:0 1px">·</span><span style="background:linear-gradient(90deg,#00B4D8,#48CAE4);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;font-weight:700;letter-spacing:.04em">INSIGHT</span>
        </div>
        <div style="font-size:0.68rem;color:rgba(0,180,216,0.75);margin-top:3px;
                    font-weight:500;letter-spacing:.02em">
            Platform Analisa Infrastruktur Digital Indonesia
        </div>
    </div>
    <div class="pi-meta" style="text-align:right;line-height:1.6;flex-shrink:0;max-width:55%">
        <span style="color:rgba(255,255,255,0.85);font-size:0.62rem;font-weight:500">Balai Monitor Spektrum Frekuensi Radio dan Infrastruktur Digital Kelas I Yogyakarta</span><br>
        <span style="color:rgba(255,255,255,0.5);font-size:0.58rem">Direktorat Jenderal Infrastruktur Digital</span><br>
        <span style="color:rgba(255,255,255,0.5);font-size:0.58rem">Kementerian Komunikasi dan Digital</span>
    </div>
</div>
<div class="freq-bar"></div>
"""

def bento_html(total: int, active: int, expired: int, unknown: int,
               top_service: str, top_count: int, provinces: int) -> str:
    pct_active  = round(active  / total * 100) if total else 0
    pct_expired = round(expired / total * 100) if total else 0
    return f"""
<div class="bento-grid">
  <div class="bento-card navy span2">
    <div class="bento-label">Total Izin Spektrum</div>
    <div class="bento-number">{total:,}</div>
    <div class="bento-sub">DIY &amp; Jawa Tengah · Balmon Kelas I Yogyakarta</div>
    <span class="badge-pill badge-signal">Database aktif</span>
  </div>
  <div class="bento-card">
    <div class="bento-label">Layanan Terbesar</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;font-weight:700;color:#0D2B55;line-height:1.2">
        {top_service}</div>
    <div class="bento-sub">{top_count:,} izin</div>
  </div>
  <div class="bento-card">
    <div class="bento-label">Masih Berlaku</div>
    <div class="bento-number" style="color:#16A34A">{active:,}</div>
    <span class="badge-pill badge-green">{pct_active}% dari total</span>
  </div>
  <div class="bento-card">
    <div class="bento-label">Sudah Expired</div>
    <div class="bento-number" style="color:#DC2626">{expired:,}</div>
    <span class="badge-pill badge-red">{pct_expired}% dari total</span>
  </div>
  <div class="bento-card sky">
    <div class="bento-label">Data Tidak Lengkap</div>
    <div class="bento-number" style="color:#D97706">{unknown:,}</div>
    <div class="bento-sub">Perlu verifikasi</div>
  </div>
</div>
"""

def welcome_html(role: str, chips: bool = True) -> str:
    if role == "public":
        icon, title = "🏙️", "Halo! Saya PAIDI-INSIGHT."
        desc = ("Tanyakan informasi umum tentang layanan radio, nama pemegang izin, "
                "atau stasiun radio di wilayah DIY dan Jawa Tengah.")
        chips = [
            "Layanan radio apa saja di Bantul?",
            "Siapa pemegang izin di Sleman?",
            "Apa itu Fixed Service?",
        ]
    else:
        icon, title = "🛡️", "Mode Petugas aktif."
        desc = ("Akses penuh ke database spektrum. Tanyakan analisis frekuensi, "
                "status masa berlaku, ERP, atau anomali data.")
        chips = [
            "Berapa izin yang sudah expired?",
            "Stasiun ERP tertinggi?",
            "Jumlah izin per layanan",
            "Izin di frekuensi 150 MHz?",
        ]
    chip_section = "".join(f'<span class="chip">{c}</span>' for c in chips) if chips else ""
    return f"""
<div class="welcome-box">
    <div class="wi">{icon}</div>
    <h3>{title}</h3>
    <p>{desc}</p>
    <div class="chip-row">{chip_section}</div>
</div>
"""
