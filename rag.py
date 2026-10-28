"""BM25 di atas dataframe yang sudah difilter per peran."""
import math
import re
from collections import Counter
from functools import lru_cache

import pandas as pd


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", str(text).lower())


def _build_corpus(df: pd.DataFrame) -> list[tuple[str, list[str]]]:
    """Gabungkan setiap baris menjadi satu dokumen teks."""
    docs = []
    for _, row in df.iterrows():
        text = " ".join(str(v) for v in row.values if pd.notna(v))
        docs.append((text, _tokenize(text)))
    return docs


def search(query: str, df: pd.DataFrame, k: int = 5,
           k1: float = 1.5, b: float = 0.75) -> pd.DataFrame:
    """Kembalikan k baris paling relevan dari df."""
    corpus = _build_corpus(df)
    q = _tokenize(query)
    n = len(corpus)
    if n == 0 or not q:
        return df.head(0)

    df_freq = Counter(t for _, toks in corpus for t in set(toks))
    avg_len = sum(len(toks) for _, toks in corpus) / n

    scores = []
    for _, toks in corpus:
        tf = Counter(toks)
        score = 0.0
        for term in q:
            if term not in tf:
                continue
            idf = math.log(1 + (n - df_freq[term] + 0.5) / (df_freq[term] + 0.5))
            score += idf * tf[term] * (k1 + 1) / (
                tf[term] + k1 * (1 - b + b * len(toks) / avg_len)
            )
        scores.append(score)

    df = df.copy()
    df["_score"] = scores
    result = df[df["_score"] > 0].nlargest(k, "_score").drop(columns=["_score"])
    return result


def retrieve(query: str, df: pd.DataFrame, k: int = 5) -> str:
    """Konteks siap tempel ke prompt."""
    hits = search(query, df, k)
    if hits.empty:
        return ""
    return hits.to_string(index=False)
