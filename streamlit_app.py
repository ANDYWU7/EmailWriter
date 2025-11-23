import os
import html
import difflib

import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI


TONES = ["Neutral", "Formal", "Friendly", "Casual", "Academic"]


def join_words(words):
    return " ".join(html.escape(w) for w in words)


def build_diffs(original: str, revised: str):
    """Return HTML for original/revised with changes highlighted."""
    o_words = original.split()
    r_words = revised.split()
    sm = difflib.SequenceMatcher(None, o_words, r_words)

    orig_parts = []
    rev_parts = []

    for tag, i1, i2, j1, j2 in sm.get_opcodes():
        if tag == "equal":
            orig_parts.append(join_words(o_words[i1:i2]))
            rev_parts.append(join_words(r_words[j1:j2]))
        elif tag == "replace":
            if i2 > i1:
                orig_parts.append(
                    f"<span class='diff-del'>{join_words(o_words[i1:i2])}</span>"
                )
            if j2 > j1:
                rev_parts.append(
                    f"<span class='diff-add'>{join_words(r_words[j1:j2])}</span>"
                )
        elif tag == "delete":
            if i2 > i1:
                orig_parts.append(
                    f"<span class='diff-del'>{join_words(o_words[i1:i2])}</span>"
                )
        elif tag == "insert":
            if j2 > j1:
                rev_parts.append(
                    f"<span class='diff-add'>{join_words(r_words[j1:j2])}</span>"
                )

    diff_css = """
    <style>
      .diff-box {border: 1px solid #ddd; border-radius: 6px; padding: 10px; min-height: 160px; background: #fafafa; font-family: system-ui, sans-serif;}
      .diff-add {background: #e6ffed;}
      .diff-del {background: #ffecec; text-decoration: line-through;}
    </style>
    """
    orig_html = diff_css + f"<div class='diff-box'>{' '.join(orig_parts) or html.escape(original)}</div>"
    rev_html = diff_css + f"<div class='diff-box'>{' '.join(rev_parts) or html.escape(revised)}</div>"
    return orig_html, rev_html


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

tone = st.radio(
    "Tone",
    options=TONES,
    index=TONES.index("Neutral"),
    horizontal=True,
)


def run_model():
    input_text = st.session_state.get("input_text", "").strip()
    if not input_text:
        st.warning("Please enter the text below first.")
        return

    tone_clause = f"Use a {tone.lower()} tone."

    if mode == "Paraphrase":
        system_prompt = (
            "You are a helpful writing assistant. "
            "Paraphrase the user's text clearly while preserving meaning. "
            f"{tone_clause} "
            "Output only the improved text. "
            'If there is not enough context, type "Not enough context to paraphrase your text."'
        )
    else:
        system_prompt = (
            "You are a grammar correction assistant. "
            "Fix grammar, spelling, and punctuation without changing style more than necessary. "
            f"Maintain meaning and adopt a {tone.lower()} tone with minimal rewriting. "
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
            height=400,
            placeholder=f"{mode} your text here.",
            max_chars=5000,
        )
    submitted = st.form_submit_button("Submit", on_click=run_model)
    with col2:
        st.text_area(
            "Output",
            key="output_box",
            label_visibility="collapsed",
            height=400,
            placeholder="Output text will go here.",
            max_chars=5000,
        )

if st.session_state["output_box"].strip():
    st.markdown("#### Changes highlighted")
    orig_html, rev_html = build_diffs(
        st.session_state.get("input_text", ""),
        st.session_state["output_box"],
    )
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("Original (removed/changed words highlighted)")
        st.markdown(orig_html, unsafe_allow_html=True)
    with c2:
        st.markdown("Revised (additions/replacements highlighted)")
        st.markdown(rev_html, unsafe_allow_html=True)
