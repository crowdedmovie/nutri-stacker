from contextlib import contextmanager
from html import escape

import streamlit as st


@contextmanager
def app_shell():
    with st.container(key="ui-shell"):
        yield


def page_header(title: str, description: str) -> None:
    st.html(
        '<header class="ui-page-header">'
        '<div class="ui-brand"><span class="ui-brand-mark" aria-hidden="true">n.</span>Nutri Stacker</div>'
        f'<h1>{escape(title)}</h1><p>{escape(description)}</p></header>'
    )


def split_layout(*, key: str = "meal", widths=(1.05, 1.35)):
    with st.container(key=f"ui-layout-{key}"):
        return st.columns(widths, gap="large")


def tabs(labels: list[str]):
    return st.tabs(labels)
