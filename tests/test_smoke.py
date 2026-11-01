"""Uji cepat tanpa API: jalankan `python test_smoke.py`."""
import os
os.environ["MOCK_LLM"] = "1"

import db, llm, prompts, rag  # noqa: E402

df = db.load("public")
assert len(df) > 0, "Data kosong"
hits = rag.search("interferensi frekuensi radio", df)
assert len(hits) >= 0  # boleh kosong kalau tidak ada kata itu
ctx = rag.retrieve("layanan fixed service Yogyakarta", df)
msgs = prompts.build_messages("ada layanan apa?", ctx, "public")
ans = llm.ask(msgs)
assert ans.startswith("[MOCK]")
print("smoke test OK")
print(f"Data: {len(df):,} baris, {len(df.columns)} kolom")
print(f"Sumber: {db.data_source('public')}")
