"""Uji cepat tanpa API: jalankan `python test_smoke.py`."""
import os

os.environ["MOCK_LLM"] = "1"

import llm, prompts, rag  # noqa: E402

hits = rag.search("interferensi frekuensi radio")
assert hits and hits[0][0] == "contoh.md", hits
assert rag.retrieve("kata yang tidak ada xyzzy") == ""
msgs = prompts.build_messages("halo", rag.retrieve("frekuensi"))
assert "Konteks" in msgs[1]["content"]
assert llm.ask(msgs).startswith("[MOCK]")
print("smoke test OK")
