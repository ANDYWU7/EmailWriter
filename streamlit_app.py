import streamlit.components.v1 as components
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import os
import html
import json
from grammarly_helper import *

load_dotenv()
secret_key = os.getenv("api_key")

client = OpenAI(api_key=secret_key)

# init once
if "output_box" not in st.session_state:
    st.session_state["output_box"] = ""

if "live_text" not in st.session_state:
    st.session_state["live_text"] = ""

if "live_suggestions" not in st.session_state:
    st.session_state["live_suggestions"] = []

if "last_checked_text" not in st.session_state:
    st.session_state["last_checked_text"] = ""

if "editor_mode" not in st.session_state:
    st.session_state["editor_mode"] = "manual"

if "manual_editor_input" not in st.session_state:
    st.session_state["manual_editor_input"] = st.session_state["live_text"]

if "live_check_ms" not in st.session_state:
    st.session_state["live_check_ms"] = 600


st.markdown("# Writing tool")

mode = st.selectbox(
    "Mode",
    options=["Paraphrase", "Grammar check", "Grammarly mode"],
    label_visibility="collapsed",
)


# ========== Normal modes (Paraphrase / Grammar check) ========== #
def run_standard_model():
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
    elif mode == "Grammar check":
        system_prompt = (
            "You are a grammar correction assistant. "
            "Fix grammar, spelling, and punctuation without changing style more than necessary. "
            "Output only the corrected text. "
            'If there is not enough context, type "Not enough context to grammar check your text."'
        )
    else:
        return

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": input_text},
        ],
    )

    st.session_state["output_box"] = resp.choices[0].message.content


# ========== Grammarly mode helpers ========== #
def get_suggestions(text: str):
    #
    if not text.strip():
        return {"suggestions": []}
    system_prompt = """
    You are an inline writing assistant. 
    Find important grammar, clarity, or word choice issues.
    
    Red is for incorrect spelling.
    Blue is for grammatical errors.
    Yellow is for suggestions to improve the text.
    
    Return ONLY a JSON object with this exact structure:
    
    {
      "suggestions": [
        {
          "start": 0,
          "end": 0,
          "original": "string",
          "suggestion": "string",
          "explanation": "string",
          "color": "red"
        }
      ]
    }
    
    Rules:
    - "start" and "end" are 0-based character indices in the ORIGINAL text, end is exclusive.
    - "original" must exactly match text[start:end].
    - "color" must be one of: "red", "blue", "yellow".
    - Focus on the most useful issues. If none, return { "suggestions": [] }.
    """
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": text},
        ],
    )
    try:
        return json.loads(resp.choices[0].message.content)
    except Exception:
        return {"suggestions": []}


# ========== UI flow based on mode ========== #
if mode in ["Paraphrase", "Grammar check"]:
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
        submitted = st.form_submit_button("Submit", on_click=run_standard_model)
        with col2:
            st.text_area(
                "Output",
                key="output_box",
                label_visibility="collapsed",
                height=500,
                placeholder=f"Output text will go here.",
                max_chars=5000,
            )
elif mode == "Grammarly mode":
    with st.expander("Settings", expanded=False):
        previous_mode = st.session_state.get("editor_mode", "manual")
        auto_mode_default = previous_mode == "auto"
        auto_mode = st.checkbox(
            "Auto-check while typing (inline editor)",
            value=auto_mode_default,
            help="Turn off to type freely and run checks manually.",
        )
        st.session_state["editor_mode"] = "auto" if auto_mode else "manual"
        if auto_mode and previous_mode != "auto":
            st.session_state["live_text"] = st.session_state.get(
                "manual_editor_input", st.session_state["live_text"]
            )
        if (not auto_mode) and previous_mode == "auto":
            st.session_state["manual_editor_input"] = st.session_state["live_text"]
        if auto_mode:
            run_ms = st.slider(
                "Live Checker Rate (ms)", 200, 1500,
                st.session_state.get("live_check_ms", 600), 50,
            )
            st.session_state["live_check_ms"] = run_ms
        else:
            run_ms = st.session_state.get("live_check_ms", 600)

    if auto_mode:
        # Compute suggestions when the text changed since the last check
        if st.session_state["live_text"] != st.session_state["last_checked_text"]:
            result = get_suggestions(st.session_state["live_text"])
            st.session_state["live_suggestions"] = result.get("suggestions", [])
            st.session_state["last_checked_text"] = st.session_state["live_text"]

        # Build highlighted markup and render live editor
        html_view = build_highlighted_html(
            st.session_state["live_text"],
            st.session_state["live_suggestions"]
        )
        new_text = render_live_editor(html_view, debounce_ms=run_ms)
        if new_text is not None and new_text != st.session_state["live_text"]:
            st.session_state["live_text"] = new_text
            st.session_state["manual_editor_input"] = new_text
    else:
        manual_text = st.text_area(
            "Write or paste text",
            key="manual_editor_input",
            height=320,
            placeholder="Type your draft here, then press 'Check text' to highlight issues.",
        )
        run_check = st.button("Check text", type="primary")
        if run_check:
            st.session_state["live_text"] = manual_text
            result = get_suggestions(manual_text)
            st.session_state["live_suggestions"] = result.get("suggestions", [])
            st.session_state["last_checked_text"] = manual_text

        html_view = build_highlighted_html(
            st.session_state["live_text"],
            st.session_state["live_suggestions"]
        )
        render_highlight_preview(html_view)
        if st.session_state["live_text"] != st.session_state["manual_editor_input"]:
            st.caption("Press “Check text” to refresh suggestions for the latest edits.")
