import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
load_dotenv()
secret_key = os.getenv("api_key")

client = OpenAI(
    api_key=secret_key
)

# init once
if "output_box" not in st.session_state:
    st.session_state["output_box"] = ""

st.markdown("# Writing tool")

mode = st.selectbox(
    "Mode", options=["Paraphrase", "Grammar check"], label_visibility="collapsed"
)


def run_model():
    input_text = st.session_state.get("input_text", "").strip()
    if not input_text:
        st.warning("Please enter the text below first.")
        return

    system_prompt = (
        f"{mode} the user's writing. Output only what the text should be. "
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )

    # This runs before widgets are redrawn, so it is safe
    st.session_state["output_box"] = resp.choices[0].message.content



with st.form("my_form"):
    col1, col2 = st.columns([2, 2])
    with col1:
        st.text_area(
            "Input",
            key="input_text",
            label_visibility="collapsed",
            height=500,
            placeholder=f"{mode} your text here.",
            max_chars=5000
        )
    submitted = st.form_submit_button("Submit", on_click=run_model)
    with col2:
        st.text_area(
            "Output",
            key="output_box",
            label_visibility="collapsed",
            height=500,
            placeholder=f"Output text will go here.",
            max_chars=5000
        )
