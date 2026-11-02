"""Persistensi riwayat chat ke MySQL. Tabel dibuat otomatis jika belum ada."""
import uuid
from datetime import datetime

import streamlit as st

from core import db

_TABLE_CREATED = False


def _ensure_table() -> bool:
    """Buat tabel chat_sessions jika belum ada. Return True kalau MySQL tersedia."""
    global _TABLE_CREATED
    if _TABLE_CREATED:
        return db._use_mysql()
    if not db._use_mysql():
        return False
    try:
        db.execute("""
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id          INT AUTO_INCREMENT PRIMARY KEY,
                session_id  VARCHAR(36)  NOT NULL,
                role        VARCHAR(20)  NOT NULL,
                content     TEXT         NOT NULL,
                created_at  TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                INDEX idx_session (session_id)
            )
        """)
        _TABLE_CREATED = True
        return True
    except Exception:
        return False


def new_session_id() -> str:
    return str(uuid.uuid4())


def save_message(session_id: str, role: str, content: str) -> None:
    """Simpan satu pesan ke MySQL."""
    if not _ensure_table():
        return
    try:
        db.execute(
            "INSERT INTO chat_sessions (session_id, role, content) VALUES (%s, %s, %s)",
            (session_id, role, content[:8000]),
        )
    except Exception:
        pass


def load_session(session_id: str) -> list[dict]:
    """Muat riwayat chat dari MySQL. Return [] kalau tidak ada."""
    if not _ensure_table():
        return []
    try:
        df = db.execute(
            "SELECT role, content FROM chat_sessions "
            "WHERE session_id = %s ORDER BY id ASC",
            (session_id,),
        )
        return [{"role": r["ROLE"], "content": r["CONTENT"]} for _, r in df.iterrows()]
    except Exception:
        return []


def delete_session(session_id: str) -> None:
    """Hapus sesi dari MySQL."""
    if not _ensure_table():
        return
    try:
        db.execute("DELETE FROM chat_sessions WHERE session_id = %s", (session_id,))
    except Exception:
        pass


def init(role: str) -> None:
    """
    Inisialisasi atau pulihkan sesi chat.
    Dipanggil sekali saat masuk ke halaman chat.
    """
    params = st.query_params

    # Kalau ada session_id di URL dan role cocok, pulihkan
    if "sid" in params and "role" in params and params["role"] == role:
        sid = params["sid"]
        if "session_id" not in st.session_state or st.session_state.session_id != sid:
            history = load_session(sid)
            if history:
                st.session_state.session_id = sid
                st.session_state.chat_history = history
                return

    # Buat sesi baru
    sid = new_session_id()
    st.session_state.session_id = sid
    if "chat_history" not in st.session_state or not st.session_state.chat_history:
        st.session_state.chat_history = []

    # Simpan role dan sid ke URL supaya bisa di-share/refresh
    st.query_params["sid"]  = sid
    st.query_params["role"] = role


def append(role: str, content: str) -> None:
    """Tambah pesan ke history dan simpan ke MySQL."""
    st.session_state.chat_history.append({"role": role, "content": content})
    sid = st.session_state.get("session_id", "")
    if sid:
        save_message(sid, role, content)


def clear(role: str) -> None:
    """Hapus riwayat chat sesi ini."""
    sid = st.session_state.get("session_id", "")
    if sid:
        delete_session(sid)
    sid = new_session_id()
    st.session_state.session_id = sid
    st.session_state.chat_history = []
    st.query_params["sid"]  = sid
    st.query_params["role"] = role
