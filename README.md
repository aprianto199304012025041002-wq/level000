# Prototipe AI (Hackathon)

Kerangka: Streamlit + Qwen (Alibaba Cloud Model Studio, endpoint kompatibel OpenAI).

## Jalankan lokal
```
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # isi DASHSCOPE_API_KEY
streamlit run app.py
```

## Struktur
- `app.py` frontend
- `llm.py` pemanggil model
- `prompts.py` template prompt
- `rag.py` placeholder RAG (opsional)

## Deploy
Push ke GitHub, lalu deploy di Streamlit Community Cloud / Hugging Face Spaces.
Isi `DASHSCOPE_API_KEY` di menu Secrets. Jangan commit `.env`.
