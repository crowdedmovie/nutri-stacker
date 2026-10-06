"""Custom Component v2 for debounced search and input accessories."""
from functools import lru_cache
from pathlib import Path

import streamlit as st

from ui.theme import current_theme
from ui.tokens import css_variables


@lru_cache(maxsize=1)
def _renderer():
    assets = Path(__file__).parent / "frontend"
    return st.components.v2.component(
        "nutri_live_input",
        html='<div class="ui-live-root"></div>',
        css=css_variables("light", ":host") + (assets / "live_input.css").read_text(encoding="utf-8"),
        js=(assets / "live_input.js").read_text(encoding="utf-8"),
        isolate_styles=True,
    )


def live_input(label: str, *, key: str, placeholder: str = "", helper: str = "", error: str = "", disabled: bool = False, clear_label: str = "Clear", debounce_ms: int = 180) -> str:
    initial = str(st.session_state.get(key, ""))
    result = _renderer()(
        key=f"ui-live-{key}",
        data={"label": label, "placeholder": placeholder, "value": initial, "helper": helper, "error": error,
              "disabled": disabled, "clearLabel": clear_label, "debounce": max(0, debounce_ms),
              "tokens": css_variables(current_theme(), ":host")},
        default={"value": initial},
        on_value_change=lambda: None,
    )
    value = result.value if isinstance(result.value, str) else initial
    st.session_state[key] = value
    return value
