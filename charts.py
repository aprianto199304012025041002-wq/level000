"""Plotly chart builders untuk bento dashboard PAIDI-INSIGHT."""
import plotly.graph_objects as go
import pandas as pd

NAVY   = "#0D2B55"
BLUE   = "#1565C0"
SIGNAL = "#00B4D8"
COLORS = ["#0D2B55","#1565C0","#0077B6","#00B4D8","#48CAE4","#90E0EF","#023E8A","#0096C7"]

_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    margin=dict(t=36, b=20, l=10, r=10),
    font=dict(family="Inter, sans-serif", size=11),
)


def sunburst_wilayah(df: pd.DataFrame) -> go.Figure:
    ids, labels, parents, values = ["root"], ["Wilayah"], [""], [int(df["CNT"].sum())]
    for _, row in df.groupby("PROVINCE")["CNT"].sum().reset_index().iterrows():
        p = str(row["PROVINCE"])
        short = "DIY" if "YOGYA" in p.upper() else "JATENG"
        ids.append(f"p_{p}"); labels.append(short)
        parents.append("root"); values.append(int(row["CNT"]))
    for _, row in df.iterrows():
        p = str(row["PROVINCE"]); c = str(row["CITY"])
        ids.append(f"c_{p}_{c}"); labels.append(c.title())
        parents.append(f"p_{p}"); values.append(int(row["CNT"]))
    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>%{value:,} izin<extra></extra>",
        insidetextorientation="radial",
        marker=dict(colorscale=[[0,SIGNAL],[0.5,BLUE],[1,NAVY]],
                    line=dict(color="white", width=1.5)),
        maxdepth=2,
    ))
    fig.update_layout(**_LAYOUT, height=280,
        title=dict(text="Sebaran Wilayah", font=dict(size=12,color=NAVY),
                   x=0.5, xanchor="center", y=0.97),
        annotations=[dict(text="Klik provinsi untuk detail kab/kota",
            x=0.5, y=-0.03, showarrow=False,
            font=dict(size=9,color="#94A3B8"), xref="paper", yref="paper")])
    return fig


def sunburst_service(df: pd.DataFrame) -> go.Figure:
    ids, labels, parents, values = ["root"], ["Layanan"], [""], [int(df["CNT"].sum())]
    for _, row in df.groupby("SERVICE")["CNT"].sum().reset_index().iterrows():
        s = str(row["SERVICE"])
        short = (s.replace("Service","Svc").replace("Land Mobile","LM")
                  .replace("(public)","Pub").replace("(private)","Prv")
                  .replace("Aeronautical","Aero").replace("Other Services","Other"))
        ids.append(f"s_{s}"); labels.append(short)
        parents.append("root"); values.append(int(row["CNT"]))
    for _, row in df.iterrows():
        s = str(row["SERVICE"])
        sub = str(row["SUBSERVICE"]) if pd.notna(row.get("SUBSERVICE")) else "Lainnya"
        ids.append(f"b_{s}_{sub}"); labels.append(sub)
        parents.append(f"s_{s}"); values.append(int(row["CNT"]))
    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        hovertemplate="<b>%{label}</b><br>%{value:,} izin<extra></extra>",
        insidetextorientation="radial",
        marker=dict(colorscale=[[0,"#48CAE4"],[0.4,SIGNAL],[0.7,BLUE],[1,NAVY]],
                    line=dict(color="white", width=1.5)),
        maxdepth=2,
    ))
    fig.update_layout(**_LAYOUT, height=280,
        title=dict(text="Jenis Layanan", font=dict(size=12,color=NAVY),
                   x=0.5, xanchor="center", y=0.97),
        annotations=[dict(text="Klik layanan untuk detail sub-layanan",
            x=0.5, y=-0.03, showarrow=False,
            font=dict(size=9,color="#94A3B8"), xref="paper", yref="paper")])
    return fig


def card_total_html(total: int, active: int, expired: int, tgl: str = "-") -> str:
    pa = round(active/total*100) if total else 0
    pe = round(expired/total*100) if total else 0
    return f"""
<div class="pi-total-wrap" style="background:linear-gradient(135deg,#0D2B55 0%,#1565C0 60%,#1A4A8A 100%);
border-radius:14px;padding:1.4rem 1.8rem;position:relative;overflow:hidden;">
<div style="position:absolute;right:-30px;top:-30px;width:180px;height:180px;
border-radius:50%;background:rgba(0,180,216,0.10)"></div>
<div style="position:absolute;right:60px;bottom:-20px;width:100px;height:100px;
border-radius:50%;background:rgba(0,180,216,0.06)"></div>
<div style="display:flex;align-items:flex-start;justify-content:space-between;flex-wrap:wrap;gap:1rem">
  <div>
    <div style="font-size:.62rem;font-weight:600;letter-spacing:.1em;
    color:rgba(255,255,255,.4);text-transform:uppercase;margin-bottom:.4rem">Total Izin Spektrum</div>
    <div class="pi-total-num" style="font-family:'Space Grotesk',sans-serif;font-size:3.2rem;
    font-weight:700;color:#fff;line-height:1;margin-bottom:.5rem">{total:,}</div>
    <div style="display:flex;gap:7px;flex-wrap:wrap">
      <span style="background:rgba(22,163,74,.28);color:#86EFAC;font-size:.63rem;
      font-weight:600;padding:3px 10px;border-radius:20px">✓ {active:,} aktif ({pa}%)</span>
      <span style="background:rgba(220,38,38,.28);color:#FCA5A5;font-size:.63rem;
      font-weight:600;padding:3px 10px;border-radius:20px">✕ {expired:,} exp ({pe}%)</span>
    </div>
  </div>
  <div style="text-align:right">
    <div style="font-size:.6rem;font-weight:600;letter-spacing:.1em;
    color:rgba(255,255,255,.4);text-transform:uppercase;margin-bottom:.3rem">Data per</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
    font-weight:700;color:#00B4D8;line-height:1">{tgl}</div>
    <div style="font-size:.62rem;color:rgba(255,255,255,.4);margin-top:.3rem">
    DIY &amp; Jawa Tengah</div>
  </div>
</div></div>"""


def card_date_inner_html(tgl: str, sumber: str, n_prov: int, n_kota: int) -> str:
    """Konten info dataset tanpa card wrapper (untuk st.container border=True)."""
    return f"""
<div style="padding:.2rem .1rem">
<div style="font-size:.62rem;font-weight:600;letter-spacing:.08em;
color:#94A3B8;text-transform:uppercase;margin-bottom:.7rem">Informasi Dataset</div>
<div class="pi-info-grid" style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem">
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Tanggal Query</div>
    <div class="pi-info-val" style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;
    font-weight:700;color:#0D2B55">{tgl}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Sumber</div>
    <div class="pi-info-val" style="font-family:'Space Grotesk',sans-serif;font-size:1.1rem;
    font-weight:700;color:#1565C0">{sumber}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Provinsi</div>
    <div class="pi-info-val" style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
    font-weight:700;color:#0D2B55">{n_prov}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Kab/Kota</div>
    <div class="pi-info-val" style="font-family:'Space Grotesk',sans-serif;font-size:1.4rem;
    font-weight:700;color:#0D2B55">{n_kota}</div>
  </div>
</div></div>"""


def card_date_html(tgl: str, sumber: str, n_prov: int, n_kota: int) -> str:
    return f"""
<div style="background:#F8FAFC;border:1px solid #E2E8F0;border-radius:14px;
padding:1.3rem 1.5rem;height:100%;min-height:160px;">
<div style="font-size:.62rem;font-weight:600;letter-spacing:.08em;
color:#94A3B8;text-transform:uppercase;margin-bottom:.7rem">Informasi Dataset</div>
<div style="display:grid;grid-template-columns:1fr 1fr;gap:.8rem">
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Tanggal Query</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
    font-weight:700;color:#0D2B55">{tgl}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Sumber</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
    font-weight:700;color:#1565C0">{sumber}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Provinsi</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
    font-weight:700;color:#0D2B55">{n_prov}</div>
  </div>
  <div>
    <div style="font-size:.68rem;color:#64748B;margin-bottom:2px">Kab/Kota</div>
    <div style="font-family:'Space Grotesk',sans-serif;font-size:1.15rem;
    font-weight:700;color:#0D2B55">{n_kota}</div>
  </div>
</div></div>"""
