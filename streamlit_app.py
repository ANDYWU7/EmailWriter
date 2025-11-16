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
        
        run_ms = st.slider("Live Checker Rate (ms)", 200, 1500, 600, 50)

    incoming_text = st.session_state.get("live_editor") 
    if incoming_text is not None:
        st.session_state["live_text"] = incoming_text

        # Compute suggestions when the text changed since the last check
    if st.session_state["live_text"] != st.session_state["last_checked_text"]:
        result = get_suggestions(st.session_state["live_text"])
        st.session_state["live_suggestions"] = result.get("suggestions", [])
        st.session_state["last_checked_text"] = st.session_state["live_text"]

        # Build and render the editor with colored underlines
    html_view = build_highlighted_html(
        st.session_state["live_text"],
        st.session_state["live_suggestions"]
    )
    render_live_editor(html_view, debounce_ms=run_ms)
