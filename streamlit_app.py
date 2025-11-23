import os

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


load_dotenv()
secret_key = os.getenv("api_key") or os.getenv("OPENAI_API_KEY")
if not secret_key:
    st.error("Missing OpenAI API key. Set OPENAI_API_KEY (or api_key in .env).")
    st.stop()

client = OpenAI(api_key=secret_key)

if "output_box" not in st.session_state:
    st.session_state["output_box"] = ""

st.markdown("# Writing tool")

mode = st.selectbox(
    "Mode",
    options=["Paraphrase", "Grammar check"],
    label_visibility="collapsed",
)


def run_model():
    input_text = st.session_state.get("input_text", "").strip()
    if not input_text:
        st.warning("Please enter the text below first.")
        return

    if mode == "Paraphrase":
        system_prompt = (
            "You are a helpful writing assistant. "
            "Paraphrase the user's text clearly while preserving meaning. "
            "Output only the improved text. "
            'If there is not enough context, type "Not enough context to paraphrase your text."'
        )
    else:
        system_prompt = (
            "You are a grammar correction assistant. "
            "Fix grammar, spelling, and punctuation without changing style more than necessary. "
            "Output only the corrected text. "
            'If there is not enough context, type "Not enough context to grammar check your text."'
        )

    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text},
            ],
        )
        st.session_state["output_box"] = resp.choices[0].message.content
    except Exception as exc:
        st.error(f"Request failed: {exc}")


with st.form("my_form"):
    col1, col2 = st.columns([2, 2])
    with col1:
        st.text_area(
            "Input",
            key="input_text",
            label_visibility="collapsed",
            height=500,
            placeholder=f"{mode} your text here.",
            max_chars=5000,
        )
    submitted = st.form_submit_button("Submit", on_click=run_model)
    with col2:
        st.text_area(
            "Output",
            key="output_box",
            label_visibility="collapsed",
            height=500,
            placeholder="Output text will go here.",
            max_chars=5000,
        )
