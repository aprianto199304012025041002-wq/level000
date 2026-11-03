"""Backward-compatible re-export: style.py tetap bisa dipakai di app.py."""
from .css import CSS            # noqa: F401
from .components import (       # noqa: F401
    HEADER_HTML,
    FREQ_BAR,
    bento_html,
    welcome_html,
)
