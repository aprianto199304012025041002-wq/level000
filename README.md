# PAIDI-INSIGHT

**Platform Analisa Infrastruktur Digital Indonesia**

Sistem informasi berbasis AI untuk pengelolaan data izin spektrum frekuensi radio, dikembangkan untuk mendukung kerja Balai Monitor Spektrum Frekuensi Radio dan Infrastruktur Digital Kelas I Yogyakarta, Direktorat Jenderal Infrastruktur Digital, Kementerian Komunikasi dan Digital Republik Indonesia.

🔗 **Live:** [paidi-jogja.streamlit.app](https://paidi-jogja.streamlit.app)

---

## Fitur Utama

### 🏙️ Mode Masyarakat Umum
- Informasi umum stasiun radio: nama pemegang izin, lokasi stasiun, jenis layanan
- Cakupan wilayah: Daerah Istimewa Yogyakarta dan Jawa Tengah
- Antarmuka percakapan natural berbasis AI
- Data disaring agar tidak menampilkan informasi sensitif

### 🛡️ Mode Petugas Pengendali Frekuensi
- Akses penuh ke seluruh data teknis: frekuensi, ERP, koordinat, masa berlaku izin, BHP
- Analisis data berbasis AI: identifikasi izin expired, distribusi layanan, anomali data
- Upload CSV untuk memperbarui sumber data secara langsung dalam sesi
- Pilihan model AI: Gemini (Google) atau Qwen (Alibaba)

### 📊 Dashboard Interaktif
- Total izin stasiun radio real-time dari database MySQL
- Jam dan tanggal WIB live
- Sunburst chart interaktif: sebaran wilayah (provinsi → kab/kota) dan jenis layanan (service → sub-service)
- Klik segmen untuk drill-down ke level berikutnya

---

## Arsitektur

```
level000/
├── app.py                  # Entry point Streamlit
│
├── core/                   # Business logic
│   ├── auth.py             # Autentikasi password petugas
│   ├── db.py               # Koneksi MySQL Hostinger + fallback CSV
│   ├── llm.py              # Multi-model: Gemini (Google) + Qwen (Alibaba)
│   ├── prompts.py          # System prompt per peran
│   ├── analyst.py          # Analitik SQL langsung (expired, ERP, agregasi)
│   └── rag.py              # BM25 search untuk data yang diupload
│
├── ui/                     # Komponen tampilan
│   ├── charts.py           # Plotly sunburst & stat card
│   └── style.py            # CSS kustom & komponen HTML
│
├── tests/
│   └── test_smoke.py       # Smoke test tanpa API
│
└── data/
    └── QUERY_14_JANUARI_2026.csv
```

**Stack:**
- Frontend & hosting: [Streamlit Cloud](https://streamlit.io/cloud)
- Model AI: Gemini via Google AI Studio API / Qwen via Alibaba Cloud Model Studio
- Database: MySQL di Hostinger (query langsung, tanpa load semua baris)
- Fallback data: CSV lokal (SIMF Balmon Kelas I Yogyakarta, 10.653 baris, 83 kolom)

---

## Menjalankan Lokal

```bash
git clone https://github.com/aprianto199304012025041002-wq/level000.git
cd level000
python -m venv .venv && source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # isi API key dan credential MySQL
streamlit run app.py
```

### Konfigurasi `.env`

```env
# Model AI (pilih: gemini atau qwen)
MODEL_PROVIDER=gemini
GEMINI_API_KEY=...
GEMINI_MODEL=gemini-3.8-flash

# Qwen (isi setelah dapat dari panitia)
DASHSCOPE_API_KEY=...
QWEN_MODEL=qwen-plus
QWEN_BASE_URL=https://dashscope-intl.aliyuncs.com/compatible-mode/v1

# MySQL
MYSQL_HOST=srv1415.hstgr.io
MYSQL_USER=...
MYSQL_PASSWORD=...
MYSQL_DB=...

# Password petugas (isi sendiri)
OFFICER_PASSWORD=...

# Mode uji tanpa API (isi 1 untuk aktif)
MOCK_LLM=0
```

---

## Data

Data bersumber dari Sistem Informasi Manajemen Frekuensi (SIMF) Balmon Kelas I Yogyakarta:
- Cakupan: Daerah Istimewa Yogyakarta dan Jawa Tengah
- Jumlah: 10.653 izin stasiun radio
- Kolom: 83 atribut teknis dan administratif
- Layanan: Fixed Service, Land Mobile (public/private), Broadcast, Aeronautical, dan lainnya

Kolom yang ditampilkan ke masyarakat umum dibatasi pada informasi non-sensitif: nama pemegang izin, nama stasiun, alamat, kota, kecamatan, provinsi, desa, jenis layanan, dan sub-layanan.

---

## Dikembangkan untuk

Hackathon AI — Kementerian Komunikasi dan Digital Republik Indonesia, 2026

---

> *PAIDI-INSIGHT: Platform Analisa Infrastruktur Digital Indonesia*
