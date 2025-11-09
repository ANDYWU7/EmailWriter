import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
import streamlit.components.v1 as components
import os
import html
import json

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
    "Mode", options=["Paraphrase", "Grammar check", "Grammarly mode"], label_visibility="collapsed"
)


def run_standard_model():
    input_text = st.session_state.get("input_text", "").strip()
    if not input_text:
        st.warning("Please enter the text below first.")
        return

    if mode == "Paraphrase":
        system_prompt = (
            "You are a helpful writing assistant. "
            "Paraphrase the user's text clearly while preserving meaning. "
            "Output only the improved text."
        )
    elif mode == "Grammar check":
        system_prompt = (
            "You are a grammar correction assistant. "
            "Fix grammar, spelling, and punctuation without changing style more than necessary. "
            "Output only the corrected text."
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


def render_inline_editor(highlighted_html: str):
    components.html(
        f"""
        <style>
          #editor {{
            border: 1px solid #ccc;
            padding: 12px;
            border-radius: 6px;
            min-height: 200px;
            font-family: system-ui, sans-serif;
            white-space: pre-wrap;
          }}
          .suggestion {{
            text-decoration: underline;
            text-decoration-color: red;
            text-decoration-style: wavy;
            cursor: pointer;
          }}
          #tooltip {{
            position: fixed;
            padding: 8px 10px;
            background: #ffffff;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 12px;
            max-width: 260px;
            display: none;
            box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            z-index: 9999;
          }}
          #tooltip strong {{
            display: block;
            margin-bottom: 4px;
          }}
          .accepted {{
            text-decoration: none;
            background-color: #e6ffe6;
          }}
        </style>

        <div id="editor" contenteditable="true">{highlighted_html}</div>
        <div id="tooltip"></div>

        <script>
          const editor = document.getElementById("editor");
          const tooltip = document.getElementById("tooltip");

          function showTooltip(span, event) {{
            const suggestion = span.dataset.suggestion;
            const explanation = span.dataset.explanation;
            tooltip.innerHTML = "<strong>Suggestion:</strong> "
              + suggestion + "<br/><em>" + explanation + "</em><br/><br/>"
              + "<span style='color:#007bff;cursor:pointer;' id='applySuggestion'>Apply change</span>";
            tooltip.style.left = (event.clientX + 10) + "px";
            tooltip.style.top = (event.clientY + 10) + "px";
            tooltip.style.display = "block";

            document.getElementById("applySuggestion").onclick = function() {{
              span.textContent = suggestion;
              span.classList.remove("suggestion");
              span.classList.add("accepted");
              tooltip.style.display = "none";
              sendBackToStreamlit();
            }};
          }}

          function hideTooltip() {{
            tooltip.style.display = "none";
          }}

          editor.addEventListener("mouseover", function(e) {{
            const span = e.target.closest(".suggestion");
            if (span) {{
              showTooltip(span, e);
            }} else {{
              hideTooltip();
            }}
          }});

          editor.addEventListener("scroll", hideTooltip);

          document.addEventListener("click", function(e) {{
            if (!e.target.closest(".suggestion") && !e.target.closest("#tooltip")) {{
              hideTooltip();
            }}
          }});

          function sendBackToStreamlit() {{
            const updated = editor.innerText;
            window.parent.postMessage(
              {{
                isStreamlitMessage: true,
                type: "streamlit:setComponentValue",
                value: updated
              }},
              "*"
            );
          }}

          editor.addEventListener("input", function() {{
            sendBackToStreamlit();
          }});
        </script>
        """,
        height=350,
        scrolling=True,
        key="inline_editor",
    )

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
                max_chars=5000
            )
        submitted = st.form_submit_button(
            "Submit", on_click=run_standard_model)
        with col2:
            st.text_area(
                "Output",
                key="output_box",
                label_visibility="collapsed",
                height=500,
                placeholder=f"Output text will go here.",
                max_chars=5000
            )
elif mode == "Grammarly mode":
    with st.form("grammarly_form"):
        st.text_area(
                "Input",
                key="input_text",
                label_visibility="collapsed",
                height=500,
                placeholder=f"Enter your text here.",
                max_chars=7500
            )
        
        submitted = st.form_submit_button("Submit")
