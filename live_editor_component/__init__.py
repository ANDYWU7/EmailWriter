import os
import streamlit.components.v1 as components

_RELEASE = True

_component_func = components.declare_component(
    "live_editor",
    path=os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend"),
)


def live_editor_component(
    highlighted_html: str,
    debounce_ms: int = 600,
    height: int = 360,
    key: str | None = None,
):
    return _component_func(
        highlighted_html=highlighted_html,
        debounce_ms=debounce_ms,
        height=height,
        key=key,
    )
