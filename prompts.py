"""Template prompt. Ganti isinya sesuai masalah yang diangkat."""

SYSTEM_PROMPT = (
    "Kamu adalah asisten AI. Jawab dalam bahasa Indonesia yang jelas dan ringkas. "
    "Jika informasi tidak cukup, katakan terus terang."
)


def build_messages(user_input: str, context: str = "") -> list[dict]:
    """Susun pesan untuk model. `context` diisi hasil RAG (opsional)."""
    content = user_input if not context else f"Konteks:\n{context}\n\nPertanyaan:\n{user_input}"
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": content},
    ]
