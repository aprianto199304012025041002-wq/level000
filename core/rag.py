"""Pencarian konteks: delegasi ke db.search() (SQL) atau BM25 (CSV fallback)."""
import math
import re
from collections import Counter

import pandas as pd


def retrieve(query: str, df: pd.DataFrame | None, k: int = 5) -> str:
    """
    Jika df adalah None atau kosong, gunakan db.search().
    Jika df diisi (upload CSV), gunakan BM25 lokal.
    """
    if df is None or df.empty:
        import db
        hits = db.search(query, k=k)
        return hits.to_string(index=False) if not hits.empty else ""

    hits = search(query, df, k)
    return hits.to_string(index=False) if not hits.empty else ""


def search(query: str, df: pd.DataFrame, k: int = 5,
           k1: float = 1.5, b: float = 0.75) -> pd.DataFrame:
    """BM25 di atas DataFrame (dipakai saat CSV/upload aktif)."""
    def tok(t): return re.findall(r"\w+", str(t).lower())

    corpus = [" ".join(str(v) for v in row if pd.notna(v)) for _, row in df.iterrows()]
    tokens = [tok(c) for c in corpus]
    q = tok(query)
    n = len(corpus)
    if n == 0 or not q:
        return df.head(0)

    df_freq = Counter(t for toks in tokens for t in set(toks))
    avg_len = sum(len(t) for t in tokens) / n

    scores = []
    for toks in tokens:
        tf = Counter(toks)
        score = sum(
            math.log(1 + (n - df_freq[t] + 0.5) / (df_freq[t] + 0.5))
            * tf[t] * (k1 + 1) / (tf[t] + k1 * (1 - b + b * len(toks) / avg_len))
            for t in q if t in tf
        )
        scores.append(score)

    out = df.copy()
    out["_score"] = scores
    return out[out["_score"] > 0].nlargest(k, "_score").drop(columns=["_score"])
