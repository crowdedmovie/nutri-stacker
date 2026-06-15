import streamlit as st

from app.storage import ensure_storage, load_foods, load_targets
from app.ui import (
    initialize_state,
    inject_styles,
    render_language_selector,
    render_meal_builder,
    render_saved_meals,
    render_targets_editor,
)
from app.i18n import t


st.set_page_config(
    page_title="Nutri Stacker",
    page_icon="🥗",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def main() -> None:
    inject_styles()
    ensure_storage()

    foods, foods_error = load_foods()
    targets, targets_error = load_targets()

    initialize_state(targets)
    render_language_selector()

    st.title(t("app_title"))
    st.write(t("app_intro"))

    if foods_error:
        st.error(foods_error)
        st.stop()
    if targets_error:
        st.warning(targets_error)

    tab_meal, tab_targets, tab_saved_meals = st.tabs([t("tab_meal"), t("tab_targets"), t("tab_saved_meals")])

    with tab_meal:
        render_meal_builder(foods, st.session_state.targets)

    with tab_targets:
        render_targets_editor(st.session_state.targets)

    with tab_saved_meals:
        render_saved_meals(foods)


if __name__ == "__main__":
    main()
