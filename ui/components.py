"""Streamlit adapters: preserve widget state, callbacks and native accessibility."""
from contextlib import contextmanager
from html import escape
from typing import Literal

import streamlit as st

Size = Literal["small", "medium", "large"]


def _scope(kind: str, key: str, size: Size = "medium", variant: str = "outline"):
    if size not in {"small", "medium", "large"}:
        raise ValueError(f"Unsupported size: {size}")
    # Streamlit exposes container keys as stable CSS classes. Widget keys stay intact.
    return st.container(key=f"ui-{kind}-{variant}-{size}-{key}", border=False)


def button(label: str, *, key: str, variant: str = "secondary", size: Size = "medium", **kwargs) -> bool:
    if variant not in {"primary", "secondary", "ghost", "danger"}:
        raise ValueError(f"Unsupported button variant: {variant}")
    # Compatibility for existing callers; new code should use variant.
    native_type = kwargs.pop("type", None)
    if native_type == "primary":
        variant = "primary"
    stretch = kwargs.pop("use_container_width", False)
    kwargs.setdefault("width", "stretch" if stretch else "content")
    with _scope("button", key, size, variant):
        return st.button(label, key=key, type="primary" if variant == "primary" else "secondary", **kwargs)


@contextmanager
def _field(kind: str, key: str, size: Size, error: str | None, helper: str | None, variant: str):
    if variant not in {"outline", "solid"}:
        raise ValueError(f"Unsupported input variant: {variant}")
    with _scope(kind, key, size, "error" if error else variant):
        yield
        if error or helper:
            role = ' role="alert"' if error else ""
            st.html(f'<div class="ui-field-help{ " ui-field-error" if error else ""}"{role}>{escape(error or helper)}</div>')


def input(label: str, *, key: str, size: Size = "medium", helper: str | None = None, error: str | None = None, variant: str = "outline", **kwargs) -> str:
    with _field("input", key, size, error, helper, variant):
        return st.text_input(label, key=key, **kwargs)


def number_input(label: str, *, key: str, size: Size = "medium", helper: str | None = None, error: str | None = None, **kwargs):
    with _field("number", key, size, error, helper, "outline"):
        return st.number_input(label, key=key, **kwargs)


def select(label: str, options, *, key: str, size: Size = "medium", helper: str | None = None, error: str | None = None, **kwargs):
    with _field("select", key, size, error, helper, "outline"):
        return st.selectbox(label, options, key=key, **kwargs)


@contextmanager
def card(*, key: str, title: str | None = None, description: str | None = None, compact: bool = False):
    with st.container(border=True, key=f"ui-card-{'compact' if compact else 'default'}-{key}"):
        if title:
            st.html(f'<h3 class="ui-card-title">{escape(title)}</h3>')
        if description:
            st.html(f'<p class="ui-card-description">{escape(description)}</p>')
        yield


def stat_card(label: str, value: str, *, target: str, progress: float, progress_label: str) -> None:
    value_percent = max(0, min(progress, 1)) * 100
    st.html(
        '<article class="ui-stat-card">'
        f'<div class="ui-stat-label">{escape(label)}</div>'
        f'<div class="ui-stat-value">{escape(value)}</div>'
        f'<div class="ui-stat-target">{escape(target)}</div>'
        f'<div class="ui-stat-track" role="progressbar" aria-label="{escape(progress_label, quote=True)}" '
        f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{value_percent:.1f}">'
        f'<span style="width:{value_percent:.2f}%"></span></div></article>'
    )


def data_table(headers: list[str], rows: list[list], *, progress_column: int | None = None) -> None:
    """Accessible, horizontally scrollable table; all text cells are escaped."""
    heading = "".join(f'<th scope="col">{escape(header)}</th>' for header in headers)
    body = []
    for row in rows:
        cells = []
        for index, value in enumerate(row):
            if index == progress_column:
                percent = max(0, min(float(value), 1)) * 100
                label = escape(f"{headers[index]} · {row[0]}", quote=True)
                content = (f'<div class="ui-stat-track" role="progressbar" aria-label="{label}" '
                           f'aria-valuemin="0" aria-valuemax="100" aria-valuenow="{percent:.1f}">'
                           f'<span style="width:{percent:.2f}%"></span></div>')
            else:
                content = escape(str(value))
            tag = 'th scope="row"' if index == 0 else "td"
            cells.append(f'<{tag}>{content}</{ "th" if index == 0 else "td"}>')
        body.append(f'<tr>{"".join(cells)}</tr>')
    st.html('<div class="ui-table-scroll" role="region" tabindex="0" '
            f'aria-label="{escape(headers[0], quote=True)}"><table class="ui-data-table">'
            f'<thead><tr>{heading}</tr></thead><tbody>{"".join(body)}</tbody></table></div>')
