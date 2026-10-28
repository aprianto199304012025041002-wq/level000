"""Autentikasi sederhana: cek password petugas dari Secrets/env."""
import hashlib
import os


def _get_secret(name: str) -> str | None:
    val = os.getenv(name)
    if val:
        return val
    try:
        import streamlit as st
        return st.secrets.get(name)
    except Exception:
        return None


def check_officer_password(entered: str) -> bool:
    """Cocokkan password yang dimasukkan dengan OFFICER_PASSWORD di Secrets."""
    stored = _get_secret("OFFICER_PASSWORD")
    if not stored:
        return False
    # Bandingkan hash supaya password tidak muncul di memori plain
    return hashlib.sha256(entered.encode()).hexdigest() == hashlib.sha256(stored.encode()).hexdigest()
