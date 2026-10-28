"""Load dan filter CSV sesuai peran pengguna."""
import functools
from pathlib import Path

import pandas as pd

DATA_PATH = Path(__file__).parent / "data" / "QUERY_14_JANUARI_2026.csv"

PUBLIC_COLS = [
    "SERVICE", "SUBSERVICE", "STN_NAME", "STN_ADDR",
    "CITY", "DISTRICT", "PROVINCE", "VILLAGE", "CLNT_NAME",
]


@functools.lru_cache(maxsize=1)
def _load_full() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, low_memory=False)


def load(role: str = "public") -> pd.DataFrame:
    """
    role='public'  → hanya kolom publik
    role='officer' → semua kolom
    """
    df = _load_full()
    if role == "public":
        return df[PUBLIC_COLS].copy()
    return df.copy()


def summary(role: str = "public") -> str:
    """Ringkasan dataset untuk dimasukkan ke prompt."""
    df = load(role)
    lines = [
        f"Dataset: {len(df):,} baris, {len(df.columns)} kolom.",
        f"Kolom tersedia: {', '.join(df.columns.tolist())}.",
    ]
    if role == "officer":
        lines.append(f"Layanan: {df['SERVICE'].value_counts().to_dict()}")
        lines.append(f"Provinsi: {df['PROVINCE'].value_counts().to_dict()}")
        lines.append(f"Status: {df['STATUS_SIMF'].value_counts().to_dict()}")
    else:
        lines.append(f"Layanan tersedia: {df['SERVICE'].value_counts().to_dict()}")
        lines.append(f"Kota/Kabupaten (10 terbesar): {df['CITY'].value_counts().head(10).to_dict()}")
    return "\n".join(lines)
