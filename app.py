"""Frontend Streamlit: input -> (RAG opsional) -> model -> hasil."""
import streamlit as st

import llm
import prompts
import rag

st.set_page_config(page_title="Prototipe AI", page_icon="🤖")
st.title("Prototipe AI")
st.caption("Kerangka awal hackathon. Ganti judul dan prompt sesuai masalah.")

user_input = st.text_area("Masukkan teks", height=160)

if st.button("Proses", type="primary"):
    if not user_input.strip():
        st.warning("Isi dulu teksnya.")
    else:
        with st.spinner("Model sedang bekerja..."):
            try:
                context = rag.retrieve(user_input)
                messages = prompts.build_messages(user_input, context)
                st.markdown(llm.ask(messages))
            except Exception as e:
                st.error(f"Gagal: {e}")
