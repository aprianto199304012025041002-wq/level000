"""Pemanggil model: Gemini (Google) dan Qwen (Alibaba). Pilih lewat MODEL_PROVIDER."""
import os

from dotenv import load_dotenv

load_dotenv()


def _get(name: str, default: str | None = None) -> str | None:
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name, default)
    except Exception:
        return default


class QuotaError(Exception):
    """API quota/rate-limit habis."""

class ModelError(Exception):
    """Error dari model yang tidak bisa di-recover."""


def ask(messages: list[dict], temperature: float = 0.3, provider: str | None = None) -> str:
    # Mode uji tanpa API
    if _get("MOCK_LLM") == "1":
        return "[MOCK] " + messages[-1]["content"]

    p = provider or _get("MODEL_PROVIDER", "gemini")
    try:
        if p == "gemini":
            return _ask_gemini(messages, temperature)
        return _ask_qwen(messages, temperature)
    except QuotaError:
        # Otomatis fallback ke model lain
        fallback = "qwen" if p == "gemini" else "gemini"
        try:
            if fallback == "gemini":
                return _ask_gemini(messages, temperature)
            return _ask_qwen(messages, temperature)
        except Exception as e2:
            raise ModelError(f"Kedua model gagal. {fallback}: {e2}") from e2
    except ModelError:
        raise
    except Exception as e:
        raise ModelError(str(e)) from e


# ── Gemini ────────────────────────────────────────────────────────────────────
def _ask_gemini(messages: list[dict], temperature: float) -> str:
    import google.generativeai as genai
    api_key = _get("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY belum diisi di Secrets.")
    genai.configure(api_key=api_key)

    model_name = _get("GEMINI_MODEL", "gemini-3.8-flash")
    system = next((m["content"] for m in messages if m["role"] == "system"), None)
    history = [
        {"role": "user" if m["role"] == "user" else "model", "parts": [m["content"]]}
        for m in messages if m["role"] != "system"
    ]
    model = genai.GenerativeModel(
        model_name,
        system_instruction=system,
        generation_config={"temperature": temperature},
    )
    chat = model.start_chat(history=history[:-1] if len(history) > 1 else [])
    try:
        resp = chat.send_message(history[-1]["parts"][0])
        return resp.text
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ["quota", "rate", "limit", "429", "resource exhausted"]):
            raise QuotaError(f"Gemini quota: {e}") from e
        raise


# ── Qwen ──────────────────────────────────────────────────────────────────────
def _ask_qwen(messages: list[dict], temperature: float) -> str:
    from openai import OpenAI
    api_key = _get("DASHSCOPE_API_KEY")
    if not api_key:
        raise RuntimeError("DASHSCOPE_API_KEY belum diisi di Secrets.")
    base_url = _get("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1")
    client = OpenAI(api_key=api_key, base_url=base_url)
    model = _get("QWEN_MODEL", "qwen-plus")
    try:
        resp = client.chat.completions.create(
            model=model, messages=messages, temperature=temperature
        )
        return resp.choices[0].message.content
    except Exception as e:
        msg = str(e).lower()
        if any(k in msg for k in ["quota", "rate", "limit", "429", "throttle"]):
            raise QuotaError(f"Qwen quota: {e}") from e
        raise
