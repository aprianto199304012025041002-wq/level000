"""Generate narasi insight dari statistik menggunakan Gemini. Di-cache by TGL_QUERY."""
import streamlit as st

from core import db, llm

_SYSTEM = (
    "Kamu adalah analis spektrum frekuensi radio dari Balai Monitor Spektrum "
    "Frekuensi Radio dan Infrastruktur Digital Kelas I Yogyakarta, Ditjen Infrastruktur Digital, "
    "Kementerian Komunikasi dan Digital RI. "
    "Tulis insight singkat dalam Bahasa Indonesia, formal namun mudah dipahami. "
    "Gunakan angka spesifik. Maksimal 4 poin bullet. Jangan mengarang data."
)


@st.cache_data(ttl=3600, show_spinner=False)
def generate(tgl_query: str) -> str:
    """Generate insight berdasarkan statistik. Di-cache per TGL_QUERY."""
    try:
        stats = _collect_stats()
        prompt = (
            f"Berdasarkan data izin spektrum frekuensi radio per {tgl_query}:\n\n"
            f"{stats}\n\n"
            "Tulis 4 poin insight terpenting dalam format bullet yang informatif "
            "untuk publik dan pengambil kebijakan. Fokus pada distribusi layanan, "
            "status masa berlaku, dan pemegang izin dominan."
        )
        msgs = [
            {"role": "system", "content": _SYSTEM},
            {"role": "user", "content": prompt},
        ]
        return llm.ask(msgs, temperature=0.4)
    except Exception as e:
        return f"_(Insight tidak tersedia: {e})_"


def _collect_stats() -> str:
    lines = []
    try:
        r = db.execute(
            "SELECT COUNT(*) AS total, "
            "SUM(STR_TO_DATE(validity_date,'%%d-%%b-%%y') >= "
            "    STR_TO_DATE(tgl_query,'%%d-%%b-%%y')) AS active, "
            "SUM(STR_TO_DATE(validity_date,'%%d-%%b-%%y') < "
            "    STR_TO_DATE(tgl_query,'%%d-%%b-%%y')) AS expired "
            "FROM isr"
        ).iloc[0]
        lines.append(f"Total izin: {int(r['TOTAL'] or 0):,}")
        lines.append(f"Masih berlaku: {int(r['ACTIVE'] or 0):,}")
        lines.append(f"Sudah expired: {int(r['EXPIRED'] or 0):,}")

        svc = db.execute("SELECT service, COUNT(*) AS cnt FROM isr GROUP BY service ORDER BY cnt DESC")
        lines.append("\nPer layanan:")
        for _, row in svc.iterrows():
            pct = int(row["CNT"]) / max(int(r["TOTAL"] or 1), 1) * 100
            lines.append(f"  {row['SERVICE']}: {int(row['CNT']):,} ({pct:.1f}%)")

        prov = db.execute("SELECT province, COUNT(*) AS cnt FROM isr GROUP BY province ORDER BY cnt DESC")
        lines.append("\nPer provinsi:")
        for _, row in prov.iterrows():
            lines.append(f"  {row['PROVINCE']}: {int(row['CNT']):,}")

        top3 = db.execute("SELECT clnt_name, COUNT(*) AS cnt FROM isr GROUP BY clnt_name ORDER BY cnt DESC LIMIT 3")
        lines.append("\nTop 3 pemegang izin:")
        for _, row in top3.iterrows():
            lines.append(f"  {row['CLNT_NAME']}: {int(row['CNT']):,} izin")
    except Exception as e:
        lines.append(f"(gagal: {e})")
    return "\n".join(lines)
