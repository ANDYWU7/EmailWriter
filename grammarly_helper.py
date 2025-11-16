import streamlit.components.v1 as components
import html
from live_editor_component import live_editor_component

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
    )

def highlight_text(text:str , suggestions):
    suggestions = sorted(suggestions, key=lambda s: s["start"])
    output = []
    last = 0
    for s in suggestions:
        start = s.get("start", 0)
        end = s.get("end", 0)
        original = s.get("original", "")
        suggestion = s.get("suggestion", "")
        explanation = s.get("explanation", "")

        if start < last or end > len(text) or start >= end:
            continue

        # plain segment
        output.append(html.escape(text[last:start]))

        span_original = html.escape(original)
        span_suggestion = html.escape(suggestion)
        span_explanation = html.escape(explanation)

        span = (
            f"<span class='suggestion' "
            f"data-suggestion='{span_suggestion}' "
            f"data-original='{span_original}' "
            f"data-explanation='{span_explanation}'>"
            f"{span_original}</span>"
        )
        output.append(span)
        last = end

    # remaining text
    output.append(html.escape(text[last:]))

    return "".join(output)


def build_highlighted_html(text: str, suggestions):
    # Build HTML with color-coded, underlined spans and tooltip data
    suggestions = sorted(
        [s for s in suggestions if isinstance(
            s.get("start", None), int) and isinstance(s.get("end", None), int)],
        key=lambda s: s["start"]
    )
    parts = []
    last = 0

    for s in suggestions:
        start = max(0, s.get("start", 0))
        end = min(len(text), s.get("end", 0))
        if start < last or start >= end:
            continue

        # plain text before span
        parts.append(html.escape(text[last:start]))

        original = html.escape(s.get("original", text[start:end]))
        suggestion = html.escape(s.get("suggestion", original))
        explanation = html.escape(s.get("explanation", ""))
        color = (s.get("color") or "yellow").lower()
        if color not in ("red", "blue", "yellow"):
            color = "yellow"

        span = (
            f"<span class='suggestion s-{color}' "
            f"data-suggestion='{suggestion}' "
            f"data-original='{original}' "
            f"data-explanation='{explanation}'>"
            f"{original}</span>"
        )
        parts.append(span)
        last = end

    parts.append(html.escape(text[last:]))
    return "".join(parts)


def render_live_editor(highlighted_html: str, debounce_ms: int = 600):
    return live_editor_component(
        highlighted_html=highlighted_html,
        debounce_ms=debounce_ms,
        height=360,
        key="live_editor",
    )


def render_highlight_preview(highlighted_html: str):
    components.html(
        f"""
        <style>
          .preview-wrapper {{
            border: 1px solid #ccc;
            border-radius: 6px;
            padding: 12px;
            min-height: 260px;
            font-family: system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
            white-space: pre-wrap;
            line-height: 1.5;
          }}
          .suggestion {{
            text-decoration: underline;
            text-decoration-style: wavy;
          }}
          .s-red {{ text-decoration-color: red; }}
          .s-blue {{ text-decoration-color: blue; }}
          .s-yellow {{ text-decoration-color: goldenrod; }}
          .accepted {{
            text-decoration: none;
            background-color: #eafaea;
          }}
        </style>
        <div class="preview-wrapper">{highlighted_html}</div>
        """,
        height=360,
        scrolling=True,
    )
