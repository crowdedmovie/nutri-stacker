import streamlit as st

import ui

from app.storage import ensure_storage, load_favorite_foods, load_foods, load_live_state, load_targets
from app.ui import (
    initialize_state,
    render_language_selector,
    render_meal_builder,
    render_saved_meals,
    render_targets_editor,
    persist_live_state,
)
from app.i18n import t


st.set_page_config(
    page_title="Nutri Stacker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    ui.apply_theme()
    ensure_storage()

    foods, foods_error = load_foods()
    targets, targets_error = load_targets()
    live_state, live_state_error = load_live_state()
    favorite_foods, favorites_error = load_favorite_foods()

    initialize_state(targets, favorite_foods, live_state)
    render_language_selector()

    with ui.app_shell():
        ui.page_header(t("app_title"), t("app_intro"))

        if foods_error:
            st.error(foods_error)
            st.stop()
        if targets_error:
            st.warning(targets_error)
        if live_state_error:
            st.warning(live_state_error)
        if favorites_error:
            st.warning(favorites_error)

        tab_meal, tab_targets, tab_saved_meals = ui.tabs([t("tab_meal"), t("tab_targets"), t("tab_saved_meals")])

        with tab_meal:
            render_meal_builder(foods, st.session_state.targets)

        with tab_targets, ui.card(key="targets-editor"):
            render_targets_editor(st.session_state.targets)

        with tab_saved_meals, ui.card(key="saved-meals"):
            render_saved_meals(foods)

    persist_live_state()


if __name__ == "__main__":
    main()
