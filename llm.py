"""Lapisan pemanggil model (Qwen lewat endpoint kompatibel OpenAI di Alibaba Model Studio)."""
import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    """Ambil dari environment; di Streamlit Cloud/HF Spaces diisi lewat Secrets."""
    value = os.getenv(name)
    if value:
        return value
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_client() -> OpenAI:
    api_key = _get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY belum diisi (.env atau Secrets).")
    base_url = _get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    return OpenAI(api_key=api_key, base_url=base_url)


def ask(messages: list[dict], temperature: float = 0.3) -> str:
    # Mode uji tanpa API: set MOCK_LLM=1 (tidak memanggil model sama sekali).
    if _get("MOCK_LLM") == "1":
        return "[MOCK] Jawaban contoh. Pesan terakhir:\n\n" + messages[-1]["content"]
    client = get_client()
    model = _get("QWEN_MODEL", "qwen-plus")
    resp = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature
    )
    return resp.choices[0].message.content
