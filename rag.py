"""RAG ringan tanpa dependensi tambahan: BM25 di atas file .txt/.md di folder data/.

Cara pakai: taruh dokumen di data/, lalu retrieve(query) mengembalikan potongan teks
paling relevan. Kalau data/ kosong, hasilnya string kosong (aplikasi tetap jalan).
"""
import math
import re
from collections import Counter
from functools import lru_cache
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
CHUNK_WORDS = 120
OVERLAP_WORDS = 20


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


def _chunk(text: str) -> list[str]:
    words = text.split()
    step = CHUNK_WORDS - OVERLAP_WORDS
    return [" ".join(words[i:i + CHUNK_WORDS]) for i in range(0, max(len(words), 1), step) if words[i:i + CHUNK_WORDS]]


@lru_cache(maxsize=1)
def _index():
    chunks, sources = [], []
    for path in sorted(DATA_DIR.glob("**/*")):
        if path.suffix.lower() in {".txt", ".md"} and path.is_file():
            for c in _chunk(path.read_text(encoding="utf-8", errors="ignore")):
                chunks.append(c)
                sources.append(path.name)
    tokens = [_tokenize(c) for c in chunks]
    df = Counter(t for toks in tokens for t in set(toks))
    avg_len = (sum(len(t) for t in tokens) / len(tokens)) if tokens else 0
    return chunks, sources, tokens, df, avg_len


def search(query: str, k: int = 3, k1: float = 1.5, b: float = 0.75) -> list[tuple[str, str, float]]:
    """Kembalikan [(sumber, potongan, skor)] urut skor tertinggi."""
    chunks, sources, tokens, df, avg_len = _index()
    if not chunks:
        return []
    q = _tokenize(query)
    n = len(chunks)
    scored = []
    for i, toks in enumerate(tokens):
        tf = Counter(toks)
        score = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df[term] + 0.5) / (df[term] + 0.5))
            score += idf * tf[term] * (k1 + 1) / (tf[term] + k1 * (1 - b + b * len(toks) / avg_len))
        if score > 0:
            scored.append((sources[i], chunks[i], score))
    return sorted(scored, key=lambda x: x[2], reverse=True)[:k]


def retrieve(query: str, k: int = 3) -> str:
    """Konteks siap tempel ke prompt."""
    hits = search(query, k)
    return "\n\n".join(f"[{src}] {text}" for src, text, _ in hits)
