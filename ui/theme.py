from pathlib import Path

import streamlit as st

from ui.tokens import css_variables


def current_theme() -> str:
    return "dark" if st.context.theme.type == "dark" else "light"


def apply_theme() -> None:
    """Install trusted local CSS once per script render; never interpolate user data."""
    styles = Path(__file__).with_name("styles.css").read_text(encoding="utf-8")
    st.html(f"<style>{css_variables(current_theme())}\n{styles}</style>")
