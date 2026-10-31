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
    margin=dict(t=36, b=48, l=10, r=10),
    font=dict(family="Inter, sans-serif", size=11),
)


# Palet wilayah: biru-navy (cool)
_PAL_WILAYAH = [
    "#0D2B55","#1565C0","#1976D2","#1E88E5",
    "#2196F3","#42A5F5","#64B5F6","#90CAF9",
    "#0077B6","#023E8A",
]
# Palet service: teal-hijau (berbeda dari wilayah)
_PAL_SERVICE = [
    "#00695C","#00796B","#00897B","#009688",
    "#26A69A","#4DB6AC","#006064","#00838F",
    "#0097A7","#00ACC1",
]


def _total(values, ids, root_id="root"):
    return next(v for i, v in zip(ids, values) if i == root_id)


def sunburst_wilayah(df: pd.DataFrame) -> go.Figure:
    ids, labels, parents, values = ["root"], ["Wilayah"], [""], [int(df["CNT"].sum())]
    tot = int(df["CNT"].sum())

    provs = df.groupby("PROVINCE")["CNT"].sum().reset_index()
    for _, row in provs.iterrows():
        p = str(row["PROVINCE"])
        short = "D.I. YOGYAKARTA" if "YOGYA" in p.upper() else "JAWA TENGAH"
        ids.append(f"p_{p}"); labels.append(short)
        parents.append("root"); values.append(int(row["CNT"]))

    for _, row in df.iterrows():
        p = str(row["PROVINCE"]); c = str(row["CITY"])
        ids.append(f"c_{p}_{c}"); labels.append(c)
        parents.append(f"p_{p}"); values.append(int(row["CNT"]))

    # Warna per node
    n = len(ids)
    node_colors = []
    for i, pid in enumerate(parents):
        if pid == "":          node_colors.append("#0D2B55")   # root
        elif pid == "root":    node_colors.append(_PAL_WILAYAH[i % 4])
        else:                  node_colors.append(_PAL_WILAYAH[4 + (i % 6)])

    # Persentase di label
    pct = [f"{v/tot*100:.1f}%" if p == "root" and pid != "" else "" 
           for v, pid in zip(values, parents)]
    customdata = [f"{v/tot*100:.1f}" for v in values]

    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        customdata=customdata,
        texttemplate="%{label}<br><b>%{customdata}%</b>",
        hovertemplate="<b>%{label}</b><br>%{value:,} izin · %{customdata}%<extra></extra>",
        insidetextorientation="auto",
        textfont=dict(size=9),
        marker=dict(colors=node_colors, line=dict(color="white", width=1.5)),
        maxdepth=2,
        leaf=dict(opacity=0.85),
    ))
    fig.update_layout(**_LAYOUT, height=320,
        transition=dict(duration=500, easing="cubic-in-out"),
        title=dict(text="Sebaran Wilayah", font=dict(size=12, color=NAVY),
                   x=0.5, xanchor="center", y=0.98),
        annotations=[dict(text="Klik provinsi → detail kab/kota",
            x=0.5, y=-0.09, showarrow=False,
            font=dict(size=9, color="#94A3B8"), xref="paper", yref="paper")])
    return fig


def sunburst_service(df: pd.DataFrame) -> go.Figure:
    """Sunburst interaktif Service → Subservice, styling seragam dengan wilayah."""
    tot = int(df["CNT"].sum())
    ids, labels, parents, values = ["root"], ["Layanan"], [""], [tot]

    svcs = df.groupby("SERVICE")["CNT"].sum().reset_index()
    for _, row in svcs.iterrows():
        s = str(row["SERVICE"])
        ids.append(f"s_{s}"); labels.append(s)
        parents.append("root"); values.append(int(row["CNT"]))

    for _, row in df.iterrows():
        s   = str(row["SERVICE"])
        sub = str(row["SUBSERVICE"]) if pd.notna(row.get("SUBSERVICE")) else "Lainnya"
        ids.append(f"b_{s}_{sub}"); labels.append(sub)
        parents.append(f"s_{s}"); values.append(int(row["CNT"]))

    n = len(ids)
    node_colors = []
    for i, pid in enumerate(parents):
        if pid == "":       node_colors.append("#004D40")
        elif pid == "root": node_colors.append(_PAL_SERVICE[i % len(_PAL_SERVICE)])
        else:               node_colors.append(_PAL_SERVICE[(i+4) % len(_PAL_SERVICE)])

    customdata = [f"{v/tot*100:.1f}" for v in values]

    fig = go.Figure(go.Sunburst(
        ids=ids, labels=labels, parents=parents, values=values,
        branchvalues="total",
        customdata=customdata,
        texttemplate="%{label}<br><b>%{customdata}%</b>",
        hovertemplate="<b>%{label}</b><br>%{value:,} izin · %{customdata}%<extra></extra>",
        insidetextorientation="auto",
        textfont=dict(size=9),
        marker=dict(colors=node_colors, line=dict(color="white", width=1.5)),
        maxdepth=2,
        leaf=dict(opacity=0.88),
    ))
    fig.update_layout(**_LAYOUT, height=320,
        transition=dict(duration=500, easing="cubic-in-out"),
        title=dict(text="Jenis Layanan", font=dict(size=12, color=NAVY),
                   x=0.5, xanchor="center", y=0.98),
        annotations=[dict(text="Klik layanan → detail sub-layanan",
            x=0.5, y=-0.09, showarrow=False,
            font=dict(size=9, color="#94A3B8"), xref="paper", yref="paper")])
    return fig



def card_total_html(total: int, active: int, expired: int, tgl: str = "-", clock: str = "") -> str:
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
    color:rgba(255,255,255,.4);text-transform:uppercase;margin-bottom:.4rem">Total Izin Stasiun Radio</div>
    <div class="pi-total-num" style="font-family:'Space Grotesk',sans-serif;font-size:3.2rem;
    font-weight:700;color:#fff;line-height:1;margin-bottom:.45rem">{total:,}</div>
    <div style="font-size:.68rem;color:rgba(255,255,255,.45)">{clock}</div>
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
