import html
import math
from copy import deepcopy

import streamlit as st
import streamlit.components.v1 as components

from app.calculations import (
    calculate_recommended_targets,
    calculate_totals,
    get_default_quantity,
)
from app.config import (
    ACTIVITY_FACTORS,
    DEFAULT_TARGETS,
    GOAL_MODES,
    MACRO_CONFIG,
    MICRO_CONFIG,
    NUTRIENT_GROUPS,
    STRENGTH_INTENSITIES,
)
from app.food_catalog import SORT_MODES, filter_and_sort_foods, get_nutrient_value
from app.i18n import (
    LANGUAGE_OPTIONS,
    activity_description,
    activity_label,
    food_label,
    format_food_names,
    goal_label,
    nutrient_label,
    set_lang,
    strength_label,
    t,
)
from app.storage import (
    list_saved_meals,
    load_meal_file,
    normalize_targets,
    save_favorite_foods,
    save_live_state,
    save_meal,
    save_targets,
)


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        :root {
            --card-bg: color-mix(in srgb, var(--secondary-background-color) 82%, transparent);
            --card-bg-strong: color-mix(in srgb, var(--secondary-background-color) 92%, transparent);
            --card-border: color-mix(in srgb, var(--text-color) 14%, transparent);
            --muted-text: color-mix(in srgb, var(--text-color) 72%, transparent);
            --header-text: color-mix(in srgb, var(--text-color) 92%, white 8%);
        }
        .macro-card {
            border: 1px solid var(--card-border);
            border-radius: 14px;
            padding: 1rem;
            background: linear-gradient(180deg, var(--card-bg-strong) 0%, var(--card-bg) 100%);
            min-height: 150px;
            box-shadow: 0 6px 18px rgba(0, 0, 0, 0.08);
        }
        .macro-label {
            color: var(--muted-text);
            font-size: 0.95rem;
            margin-bottom: 0.3rem;
        }
        .macro-value {
            font-size: 1.55rem;
            font-weight: 700;
            color: var(--text-color);
            margin-bottom: 0.15rem;
        }
        .macro-target {
            color: var(--muted-text);
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }
        .table-header {
            font-weight: 700;
            color: var(--header-text);
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 0.45rem;
            margin-bottom: 0.5rem;
        }
        .food-summary {
            border: 1px solid var(--card-border);
            border-radius: 12px;
            padding: 0.75rem 1rem;
            background: var(--card-bg);
            color: var(--text-color);
            margin-bottom: 0.75rem;
        }
        .food-item-title {
            font-size: 1rem;
            font-weight: 700;
            color: var(--text-color);
            margin-bottom: 0.2rem;
        }
        .food-item-meta {
            color: var(--muted-text);
            font-size: 0.92rem;
        }
        .food-detail-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
            gap: 0.65rem;
            margin: 0.35rem 0 0.85rem;
        }
        .food-detail-card {
            border: 1px solid var(--card-border);
            border-radius: 10px;
            padding: 0.7rem 0.8rem;
            background: var(--card-bg);
        }
        .food-detail-label {
            color: var(--muted-text);
            font-size: 0.82rem;
            margin-bottom: 0.2rem;
        }
        .food-detail-value {
            color: var(--text-color);
            font-size: 1rem;
            font-weight: 700;
        }
        .food-micro-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
            gap: 0.45rem 0.9rem;
        }
        .food-micro-item {
            display: flex;
            justify-content: space-between;
            gap: 0.75rem;
            padding: 0.45rem 0.55rem;
            border-radius: 8px;
            background: color-mix(in srgb, var(--card-bg) 82%, transparent);
        }
        .food-micro-name {
            color: var(--muted-text);
            font-size: 0.88rem;
        }
        .food-micro-value {
            color: var(--text-color);
            font-size: 0.9rem;
            font-weight: 600;
            white-space: nowrap;
        }
        .food-catalog-meta {
            color: var(--muted-text);
            font-size: 0.88rem;
            line-height: 1.35;
            padding-bottom: 0.25rem;
        }
        .food-catalog-name {
            color: var(--text-color);
            font-size: 0.98rem;
            font-weight: 700;
            margin-bottom: 0.15rem;
        }
        .food-catalog-bottom-space {
            height: 0.25rem;
        }
        .st-key-notice-success {
            background: rgba(34, 197, 94, 0.22) !important;
            border: 1px solid rgba(74, 222, 128, 0.55) !important;
            border-radius: 0.55rem;
            padding: 0.65rem 0.8rem !important;
        }
        .st-key-notice-warning {
            background: rgba(245, 158, 11, 0.2) !important;
            border: 1px solid rgba(251, 191, 36, 0.55) !important;
            border-radius: 0.55rem;
            padding: 0.65rem 0.8rem !important;
        }
        .st-key-notice-info {
            background: rgba(59, 130, 246, 0.2) !important;
            border: 1px solid rgba(96, 165, 250, 0.52) !important;
            border-radius: 0.55rem;
            padding: 0.65rem 0.8rem !important;
        }
        .st-key-notice-success > div,
        .st-key-notice-warning > div,
        .st-key-notice-info > div {
            background: transparent !important;
        }
        .st-key-notice-success [data-testid="stHorizontalBlock"],
        .st-key-notice-warning [data-testid="stHorizontalBlock"],
        .st-key-notice-info [data-testid="stHorizontalBlock"] {
            align-items: stretch !important;
        }
        .st-key-notice-success [data-testid="stColumn"],
        .st-key-notice-warning [data-testid="stColumn"],
        .st-key-notice-info [data-testid="stColumn"] {
            align-self: stretch !important;
        }
        .st-key-notice-success [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
        .st-key-notice-warning [data-testid="stColumn"] > [data-testid="stVerticalBlock"],
        .st-key-notice-info [data-testid="stColumn"] > [data-testid="stVerticalBlock"] {
            height: 100% !important;
            justify-content: center !important;
        }
        .st-key-notice-success button,
        .st-key-notice-warning button,
        .st-key-notice-info button {
            border: 0;
            background: transparent;
            color: var(--text-color);
            min-height: 2.25rem;
            font-size: 1.15rem;
        }
        .st-key-notice-success [data-testid="stButton"],
        .st-key-notice-warning [data-testid="stButton"],
        .st-key-notice-info [data-testid="stButton"] {
            display: flex;
            align-items: center;
            justify-content: center;
            height: 100%;
        }
        .st-key-notice-success [data-testid="stButton"] > button,
        .st-key-notice-warning [data-testid="stButton"] > button,
        .st-key-notice-info [data-testid="stButton"] > button {
            margin: 0 auto;
        }
        .st-key-notice-success [data-testid="stMarkdownContainer"],
        .st-key-notice-warning [data-testid="stMarkdownContainer"],
        .st-key-notice-info [data-testid="stMarkdownContainer"] {
            margin: 0 !important;
            padding: 0 !important;
        }
        .st-key-notice-success [data-testid="stMarkdownContainer"] p,
        .st-key-notice-warning [data-testid="stMarkdownContainer"] p,
        .st-key-notice-info [data-testid="stMarkdownContainer"] p {
            margin: 0 !important;
        }
        .notice-copy {
            display: flex;
            align-items: center;
            height: 2.25rem;
            min-height: 2.25rem;
            padding: 0 0.65rem;
            color: var(--text-color);
            line-height: 1.2;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def inject_instant_food_search() -> None:
    components.html(
        """
        <script>
        const doc = window.parent.document;
        if (doc.__nutriStackerInstantFoodSearchObserver) {
            doc.__nutriStackerInstantFoodSearchObserver.disconnect();
        }
        const previousHandler = doc.__nutriStackerInstantFoodSearchHandler;
        if (previousHandler) {
            doc.querySelectorAll('input[data-testid="stTextInputField"]').forEach(function(input) {
                input.removeEventListener("input", previousHandler);
                input.__nutriStackerInstantSearchAttached = false;
            });
        }

        const instantFoodSearchHandler = function(event) {
            const input = event.target;
            window.clearTimeout(input.__nutriStackerSearchTimer);
            input.__nutriStackerSearchTimer = window.setTimeout(function() {
                if (!input.isConnected) {
                    return;
                }
                const eventWindow = doc.defaultView || window;
                input.dispatchEvent(new eventWindow.Event("change", {bubbles: true}));
                input.dispatchEvent(new eventWindow.KeyboardEvent("keydown", {
                    key: "Enter",
                    code: "Enter",
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true,
                }));
            }, 120);
        };

        const attachInstantSearch = function() {
            doc.querySelectorAll('input[data-testid="stTextInputField"][type="search"]').forEach(function(input) {
                if (input.__nutriStackerInstantSearchAttached) {
                    return;
                }
                input.addEventListener("input", instantFoodSearchHandler);
                input.__nutriStackerInstantSearchAttached = true;
            });
        };

        const instantFoodSearchObserver = new MutationObserver(attachInstantSearch);
        instantFoodSearchObserver.observe(doc.body, {childList: true, subtree: true});
        attachInstantSearch();
        doc.__nutriStackerInstantFoodSearchObserver = instantFoodSearchObserver;
        doc.__nutriStackerInstantFoodSearchHandler = instantFoodSearchHandler;
        </script>
        """,
        height=0,
    )


def format_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def push_notice(message: str, scope: str, kind: str = "success") -> None:
    st.session_state.notice = {"message": message, "kind": kind, "scope": scope}


def render_notice(scope: str) -> None:
    notice = st.session_state.get("notice")
    if not notice or notice.get("scope") != scope:
        return

    notice_kind = notice.get("kind", "info")
    if notice_kind not in {"success", "warning", "info"}:
        notice_kind = "info"
    safe_message = html.escape(str(notice.get("message", ""))).replace("\n", "<br>")

    with st.container(border=False, key=f"notice-{notice_kind}"):
        message_col, close_col = st.columns([0.94, 0.06], gap="small", vertical_alignment="center")
        with message_col:
            st.markdown(f"<div class='notice-copy'>{safe_message}</div>", unsafe_allow_html=True)
        with close_col:
            if st.button("✕", key=f"close_notice_{scope}", help=t("close_message")):
                st.session_state.notice = None
                rerun_with_live_state()


def render_language_selector() -> None:
    current = st.session_state.get("lang", "fr")
    if "language_selector" not in st.session_state:
        st.session_state.language_selector = current

    st.sidebar.selectbox(
        t("language"),
        options=list(LANGUAGE_OPTIONS.keys()),
        format_func=lambda code: LANGUAGE_OPTIONS[code],
        help=t("language_help"),
        key="language_selector",
    )
    selected = st.session_state.language_selector

    if selected != current:
        set_lang(selected)
        st.session_state.targets["app_settings"]["language"] = selected
        save_targets(st.session_state.targets)
        rerun_with_live_state()


def render_macro_cards(macro_totals: dict, targets: dict) -> None:
    macro_columns = st.columns(len(MACRO_CONFIG))
    for column, (nutrient_name, config) in zip(macro_columns, MACRO_CONFIG.items()):
        current_value = macro_totals[nutrient_name]
        target_value = targets["macros"][nutrient_name]
        progress = 0.0 if target_value <= 0 else min(current_value / target_value, 1.0)
        percent = 0.0 if target_value <= 0 else (current_value / target_value) * 100

        with column:
            st.markdown(
                (
                    "<div class='macro-card'>"
                    f"<div class='macro-label'>{nutrient_label(nutrient_name)}</div>"
                    f"<div class='macro-value'>{format_number(current_value)} {config['unit']}</div>"
                    f"<div class='macro-target'>{t('target_word')}: {format_number(target_value)} {config['unit']} "
                    f"({percent:.0f}%)</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            st.progress(progress)


def render_micro_table(micro_totals: dict, targets: dict) -> None:
    header_columns = st.columns([2.3, 1.1, 1.1, 1.0, 1.3, 1.4])
    headers = [
        t("micro_header_nutrient"),
        t("micro_header_current"),
        t("micro_header_target"),
        t("micro_header_percent"),
        t("micro_header_gap"),
        t("micro_header_progress"),
    ]
    for column, header in zip(header_columns, headers):
        with column:
            st.markdown(f"<div class='table-header'>{header}</div>", unsafe_allow_html=True)

    for nutrient_name, config in MICRO_CONFIG.items():
        current_value = micro_totals[nutrient_name]
        target_value = targets["micros"][nutrient_name]
        percent = 0.0 if target_value <= 0 else (current_value / target_value) * 100
        difference = current_value - target_value
        status = (
            t("status_excess", value=format_number(difference), unit=config["unit"])
            if difference >= 0
            else t("status_remaining", value=format_number(abs(difference)), unit=config["unit"])
        )

        row_columns = st.columns([2.3, 1.1, 1.1, 1.0, 1.3, 1.4])
        row_columns[0].write(nutrient_label(nutrient_name))
        row_columns[1].write(f"{format_number(current_value)} {config['unit']}")
        row_columns[2].write(f"{format_number(target_value)} {config['unit']}")
        row_columns[3].write(f"{percent:.0f}%")
        row_columns[4].write(status)
        with row_columns[5]:
            st.progress(0.0 if target_value <= 0 else min(current_value / target_value, 1.0))


def render_food_breakdown(detail: dict) -> None:
    macro_cards = []
    for nutrient_name, config in MACRO_CONFIG.items():
        macro_cards.append(
            (
                "<div class='food-detail-card'>"
                f"<div class='food-detail-label'>{nutrient_label(nutrient_name)}</div>"
                f"<div class='food-detail-value'>{format_number(detail['macros'][nutrient_name])} {config['unit']}</div>"
                "</div>"
            )
        )

    micro_items = []
    for nutrient_name, config in MICRO_CONFIG.items():
        micro_items.append(
            (
                "<div class='food-micro-item'>"
                f"<span class='food-micro-name'>{nutrient_label(nutrient_name)}</span>"
                f"<span class='food-micro-value'>{format_number(detail['micros'][nutrient_name])} {config['unit']}</span>"
                "</div>"
            )
        )

    st.markdown(f"**{t('food_macros_title')}**")
    st.markdown(f"<div class='food-detail-grid'>{''.join(macro_cards)}</div>", unsafe_allow_html=True)
    st.markdown(f"**{t('food_micros_title')}**")
    st.markdown(f"<div class='food-micro-grid'>{''.join(micro_items)}</div>", unsafe_allow_html=True)


def render_simple_food_selector(foods: dict) -> None:
    food_to_display = {food_name: food_label(food_name) for food_name in foods}
    if st.session_state.pop("simple_food_picker_reset", False):
        st.session_state.simple_food_picker = None

    available_foods = [
        food_name for food_name in foods if food_name not in st.session_state.meal_items
    ]
    if not available_foods:
        st.info(t("food_all_selected"))
        return
    display_to_food = {food_to_display[name]: name for name in available_foods}
    selected_display_name = st.selectbox(
        t("foods_label"),
        options=sorted(display_to_food),
        index=None,
        placeholder=t("foods_placeholder"),
        key="simple_food_picker",
        filter_mode="contains",
    )
    if selected_display_name:
        food_name = display_to_food[selected_display_name]
        default_quantity = get_default_quantity(food_name, foods)
        st.session_state.meal_items[food_name] = default_quantity
        st.session_state[f"qty_{food_name}"] = default_quantity
        st.session_state.simple_food_picker_reset = True
        rerun_with_live_state()


def render_advanced_food_catalog(foods: dict) -> None:
    food_to_display = {food_name: food_label(food_name) for food_name in foods}
    nutrient_options = [*MACRO_CONFIG, *MICRO_CONFIG]
    if st.session_state.get("food_sort_nutrient") not in nutrient_options:
        st.session_state.food_sort_nutrient = nutrient_options[0]
    if st.session_state.get("food_sort_mode") not in SORT_MODES:
        st.session_state.food_sort_mode = SORT_MODES[0]

    search_col, nutrient_col = st.columns([1.3, 1], gap="medium")
    with search_col:
        search_query = st.text_input(
            t("food_search_label"),
            placeholder=t("foods_placeholder"),
            type="search",
            key="food_search_query",
        )
        inject_instant_food_search()
    with nutrient_col:
        nutrient_name = st.selectbox(
            t("food_sort_criterion"),
            options=nutrient_options,
            format_func=nutrient_label,
            key="food_sort_nutrient",
        )

    filter_col, sort_col = st.columns([1.3, 1], gap="medium", vertical_alignment="center")
    with filter_col:
        favorites_only = st.checkbox(t("food_favorites_only"), key="food_favorites_only")
    with sort_col:
        mode = st.session_state.food_sort_mode
        mode_key = {
            "alpha": "food_sort_mode_alpha",
            "asc": "food_sort_mode_asc",
            "desc": "food_sort_mode_desc",
        }[mode]
        if st.button(
            t("food_sort_button", mode=t(mode_key)),
            help=t("food_sort_button_help"),
            key="food_sort_mode_button",
            use_container_width=True,
        ):
            current_index = SORT_MODES.index(mode)
            st.session_state.food_sort_mode = SORT_MODES[(current_index + 1) % len(SORT_MODES)]
            rerun_with_live_state()

    favorite_foods = set(st.session_state.get("favorite_foods", []))
    displayed_foods = filter_and_sort_foods(
        foods,
        food_to_display,
        search_query,
        favorite_foods,
        favorites_only,
        nutrient_name,
        st.session_state.food_sort_mode,
        excluded_foods=set(st.session_state.meal_items),
    )

    if not displayed_foods:
        if favorites_only and not any(food_name in foods for food_name in favorite_foods):
            st.info(t("food_no_favorites"))
        else:
            st.info(t("food_no_results"))
        return

    with st.expander(
        t("food_search_results", count=len(displayed_foods)),
        expanded=bool(search_query.strip()),
    ):
        st.caption(t("food_results_count", count=len(displayed_foods)))
        for food_name in displayed_foods:
            food_data = foods[food_name]
            nutrient_value = get_nutrient_value(food_data, nutrient_name)
            nutrient_config = {**MACRO_CONFIG, **MICRO_CONFIG}[nutrient_name]
            is_favorite = food_name in favorite_foods

            with st.container(border=True):
                info_col, actions_col = st.columns([3.5, 1.5], gap="small", vertical_alignment="center")
                with info_col:
                    st.markdown(
                        (
                            f"<div class='food-catalog-name'>{food_to_display[food_name]}</div>"
                            f"<div class='food-catalog-meta'>{t('reference_label')} : "
                            f"{food_data['Ref_Qte']} {food_data['Unite']}<br>"
                            f"{t('food_value_reference', value=format_number(nutrient_value), unit=nutrient_config['unit'], quantity=food_data['Ref_Qte'], reference_unit=food_data['Unite'])}</div>"
                        ),
                        unsafe_allow_html=True,
                    )
                with actions_col:
                    add_col, favorite_col = st.columns([1.25, 0.7], gap="small", vertical_alignment="center")
                    with add_col:
                        if st.button(
                            t("food_add"),
                            key=f"food_meal_toggle_{food_name}",
                            use_container_width=True,
                        ):
                            default_quantity = get_default_quantity(food_name, foods)
                            st.session_state.meal_items[food_name] = default_quantity
                            st.session_state[f"qty_{food_name}"] = default_quantity
                            rerun_with_live_state()
                    with favorite_col:
                        if st.button(
                            "★" if is_favorite else "☆",
                            key=f"food_favorite_toggle_{food_name}",
                            help=t("food_favorite_remove" if is_favorite else "food_favorite_add"),
                            use_container_width=True,
                        ):
                            if is_favorite:
                                favorite_foods.remove(food_name)
                            else:
                                favorite_foods.add(food_name)
                            updated_favorites = sorted(
                                favorite_foods,
                                key=lambda name: food_to_display.get(name, name).casefold(),
                            )
                            st.session_state.favorite_foods = updated_favorites
                            save_favorite_foods(updated_favorites)
                            rerun_with_live_state()
                st.markdown("<div class='food-catalog-bottom-space'></div>", unsafe_allow_html=True)


def render_food_catalog(foods: dict) -> None:
    st.markdown(f"#### {t('food_catalog_title')}")
    st.caption(t("food_catalog_intro"))
    search_mode = st.radio(
        t("food_search_mode"),
        options=["simple", "advanced"],
        format_func=lambda mode: t(f"food_search_mode_{mode}"),
        key="food_search_mode",
        horizontal=True,
    )
    if search_mode == "simple":
        render_simple_food_selector(foods)
    else:
        render_advanced_food_catalog(foods)


def render_meal_builder(foods: dict, targets: dict) -> None:
    st.subheader(t("meal_subheader"))
    col_input, col_results = st.columns([1.05, 1.35], gap="large")

    with col_input:
        st.write(t("meal_intro"))
        render_food_catalog(foods)

    selected_foods = [food_name for food_name in st.session_state.meal_items if food_name in foods]
    macro_totals, micro_totals, details, missing_foods = calculate_totals(st.session_state.meal_items, foods)

    with col_input:
        if not selected_foods:
            st.info(t("meal_empty"))
        else:
            st.markdown(f"#### {t('selected_foods')}")
            for food_name in selected_foods:
                food_data = foods[food_name]
                reference_quantity = food_data["Ref_Qte"]
                reference_unit = food_data["Unite"]
                quantity_key = f"qty_{food_name}"
                if quantity_key not in st.session_state:
                    st.session_state[quantity_key] = st.session_state.meal_items.get(
                        food_name,
                        get_default_quantity(food_name, foods),
                    )

                with st.container(border=True):
                    info_col, remove_col = st.columns([3.2, 1], gap="medium", vertical_alignment="center")
                    with info_col:
                        st.markdown(
                            (
                                f"<div class='food-item-title'>{food_label(food_name)}</div>"
                                f"<div class='food-item-meta'>{t('reference_label')} : {reference_quantity} {reference_unit}</div>"
                            ),
                            unsafe_allow_html=True,
                        )
                    with remove_col:
                        if st.button(
                            t("food_remove"),
                            key=f"selected_food_remove_{food_name}",
                            use_container_width=True,
                        ):
                            st.session_state.meal_items.pop(food_name, None)
                            st.session_state.pop(quantity_key, None)
                            rerun_with_live_state()

                    quantity = st.number_input(
                        t("quantity_label"),
                        min_value=0.0,
                        step=1.0 if float(reference_quantity) == 1 else 10.0,
                        key=quantity_key,
                        help=t("quantity_help", unit=reference_unit),
                    )
                    st.session_state.meal_items[food_name] = float(quantity)

                    single_details = calculate_totals({food_name: float(quantity)}, foods)[2]
                    if single_details:
                        with st.expander(t("food_detail"), expanded=False):
                            render_food_breakdown(single_details[0])

    with col_results:
        st.subheader(t("nutrition_analysis"))
        if missing_foods:
            st.warning(t("missing_saved_foods", foods=format_food_names(missing_foods)))

        if details:
            render_macro_cards(macro_totals, targets)
            st.markdown(f"### {t('micronutrients_title')}")
            render_micro_table(micro_totals, targets)
        else:
            st.info(t("results_waiting"))


def apply_recommended_targets(recommendation: dict) -> None:
    for nutrient_name, value in recommendation["target_macros"].items():
        st.session_state.target_inputs[nutrient_name] = float(value)
        st.session_state[f"target_{nutrient_name}"] = float(value)
    for nutrient_name, value in recommendation["target_micros"].items():
        st.session_state.target_inputs[nutrient_name] = float(value)
        st.session_state[f"target_{nutrient_name}"] = float(value)

    st.session_state.targets["macros"] = {name: float(st.session_state.target_inputs[name]) for name in MACRO_CONFIG}
    st.session_state.targets["micros"] = {name: float(st.session_state.target_inputs[name]) for name in MICRO_CONFIG}


def update_profile_from_inputs() -> None:
    st.session_state.targets["calculator_profile"] = {
        "sex": st.session_state.calc_sex,
        "age": int(st.session_state.calc_age),
        "height_cm": float(st.session_state.calc_height_cm),
        "weight_kg": float(st.session_state.calc_weight_kg),
        "body_fat_mode": st.session_state.calc_body_fat_mode,
        "body_fat_pct": float(st.session_state.calc_body_fat_pct),
        "neck_cm": float(st.session_state.calc_neck_cm),
        "waist_cm": float(st.session_state.calc_waist_cm),
        "hip_cm": float(st.session_state.calc_hip_cm),
        "lifestyle_activity": st.session_state.calc_lifestyle_activity,
        "walk_km": float(st.session_state.calc_walk_km),
        "run_km": float(st.session_state.calc_run_km),
        "strength_minutes": float(st.session_state.calc_strength_minutes),
        "strength_intensity": st.session_state.calc_strength_intensity,
        "goal_mode": st.session_state.calc_goal_mode,
    }


def build_live_state() -> dict:
    targets = deepcopy(st.session_state.get("targets", DEFAULT_TARGETS))
    target_inputs = st.session_state.get("target_inputs", {})

    for group_name, config in NUTRIENT_GROUPS.items():
        target_group = targets.setdefault(group_name, {})
        for nutrient_name in config:
            value = st.session_state.get(
                f"target_{nutrient_name}",
                target_inputs.get(nutrient_name, DEFAULT_TARGETS[group_name][nutrient_name]),
            )
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                target_group[nutrient_name] = float(value)

    profile = targets.setdefault("calculator_profile", {})
    for field_name, default_value in DEFAULT_TARGETS["calculator_profile"].items():
        value = st.session_state.get(f"calc_{field_name}", profile.get(field_name, default_value))
        if isinstance(default_value, str):
            if isinstance(value, str):
                profile[field_name] = value
        elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
            profile[field_name] = int(value) if isinstance(default_value, int) else float(value)

    meal_items = {}
    for food_name, quantity in st.session_state.get("meal_items", {}).items():
        if isinstance(food_name, str) and isinstance(quantity, (int, float)) and not isinstance(quantity, bool):
            if math.isfinite(float(quantity)):
                meal_items[food_name] = float(quantity)

    return {
        "meal": {
            "name": str(st.session_state.get("meal_name", "")),
            "items": meal_items,
        },
        "targets": targets,
    }


def persist_live_state() -> None:
    save_live_state(build_live_state())


def rerun_with_live_state() -> None:
    persist_live_state()
    st.rerun()


def restore_targets_from_live_state(targets: dict, live_state: dict | None) -> dict:
    if not isinstance(live_state, dict) or not isinstance(live_state.get("targets"), dict):
        return deepcopy(targets)

    merged_targets = deepcopy(targets)
    snapshot_targets = live_state["targets"]
    for group_name, config in NUTRIENT_GROUPS.items():
        snapshot_group = snapshot_targets.get(group_name, {})
        if not isinstance(snapshot_group, dict):
            continue
        for nutrient_name in config:
            value = snapshot_group.get(nutrient_name)
            if isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                merged_targets[group_name][nutrient_name] = float(value)

    snapshot_profile = snapshot_targets.get("calculator_profile", {})
    if isinstance(snapshot_profile, dict):
        for field_name, default_value in DEFAULT_TARGETS["calculator_profile"].items():
            value = snapshot_profile.get(field_name)
            if isinstance(default_value, str) and isinstance(value, str):
                merged_targets["calculator_profile"][field_name] = value
            elif isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value)):
                merged_targets["calculator_profile"][field_name] = value

    snapshot_settings = snapshot_targets.get("app_settings", {})
    if isinstance(snapshot_settings, dict) and snapshot_settings.get("language") in {"fr", "en"}:
        merged_targets["app_settings"]["language"] = snapshot_settings["language"]

    return normalize_targets(merged_targets)


def missing_target_values() -> list[str]:
    missing = []
    for config in NUTRIENT_GROUPS.values():
        for nutrient_name in config:
            value = st.session_state.get(f"target_{nutrient_name}")
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
                missing.append(nutrient_label(nutrient_name))
    return missing


def save_targets_from_inputs() -> None:
    missing = missing_target_values()
    if missing:
        push_notice(
            t("targets_missing_values", fields=", ".join(missing)),
            "targets_actions",
            kind="warning",
        )
        return

    update_profile_from_inputs()
    new_targets = {
        "macros": {
            nutrient_name: float(st.session_state[f"target_{nutrient_name}"])
            for nutrient_name in MACRO_CONFIG
        },
        "micros": {
            nutrient_name: float(st.session_state[f"target_{nutrient_name}"])
            for nutrient_name in MICRO_CONFIG
        },
        "calculator_profile": deepcopy(st.session_state.targets["calculator_profile"]),
        "app_settings": deepcopy(
            st.session_state.targets.get("app_settings", DEFAULT_TARGETS["app_settings"])
        ),
    }
    st.session_state.target_inputs = {
        nutrient_name: new_targets[group_name][nutrient_name]
        for group_name, config in NUTRIENT_GROUPS.items()
        for nutrient_name in config
    }
    save_targets(new_targets)
    st.session_state.targets = deepcopy(new_targets)
    push_notice(t("targets_saved"), "targets_actions")


def reset_targets_to_defaults() -> None:
    reset_targets = deepcopy(DEFAULT_TARGETS)
    save_targets(reset_targets)
    st.session_state.targets = deepcopy(reset_targets)
    st.session_state.target_inputs = {
        nutrient_name: reset_targets[group_name][nutrient_name]
        for group_name, config in NUTRIENT_GROUPS.items()
        for nutrient_name in config
    }
    for group_name, config in NUTRIENT_GROUPS.items():
        for nutrient_name in config:
            st.session_state[f"target_{nutrient_name}"] = reset_targets[group_name][nutrient_name]
    for field_name, value in reset_targets["calculator_profile"].items():
        st.session_state[f"calc_{field_name}"] = value
    push_notice(t("targets_reset"), "targets_actions")


def render_energy_calculator() -> dict:
    st.markdown(t("energy_calculator_title"))
    st.caption(t("energy_calculator_intro"))
    st.info(t("energy_calculator_info"))

    profile_col, activity_col = st.columns(2, gap="large")

    with profile_col:
        st.markdown(t("profile_section"))
        st.radio(
            t("sex"),
            options=["homme", "femme"],
            format_func=lambda value: t("male") if value == "homme" else t("female"),
            key="calc_sex",
            horizontal=True,
            help=t("sex_help"),
        )
        st.number_input(t("age"), min_value=15, max_value=90, step=1, key="calc_age", help=t("age_help"))
        st.number_input(t("height_cm"), min_value=120.0, max_value=230.0, step=1.0, key="calc_height_cm", help=t("height_help"))
        st.number_input(t("weight_kg"), min_value=35.0, max_value=250.0, step=0.1, key="calc_weight_kg", help=t("weight_help"))

        body_fat_mode = st.radio(
            t("body_fat"),
            options=["unknown", "known", "estimate_navy"],
            format_func=lambda value: {
                "unknown": t("body_fat_unknown"),
                "known": t("body_fat_known"),
                "estimate_navy": t("body_fat_estimate"),
            }[value],
            key="calc_body_fat_mode",
            help=t("body_fat_help"),
        )
        if body_fat_mode == "known":
            st.number_input(
                t("body_fat_pct"),
                min_value=2.0,
                max_value=60.0,
                step=0.1,
                key="calc_body_fat_pct",
                help=t("body_fat_pct_help"),
            )
        elif body_fat_mode == "estimate_navy":
            st.number_input(t("neck_cm"), min_value=20.0, max_value=70.0, step=0.1, key="calc_neck_cm", help=t("neck_help"))
            st.number_input(t("waist_cm"), min_value=40.0, max_value=200.0, step=0.1, key="calc_waist_cm", help=t("waist_help"))
            if st.session_state.calc_sex == "femme":
                st.number_input(t("hip_cm"), min_value=50.0, max_value=220.0, step=0.1, key="calc_hip_cm", help=t("hip_help"))
            st.caption(t("body_fat_caption"))

    with activity_col:
        st.markdown(t("activity_goal_section"))
        st.selectbox(
            t("activity_daily"),
            options=list(ACTIVITY_FACTORS.keys()),
            format_func=activity_label,
            key="calc_lifestyle_activity",
            help=t("activity_help"),
        )
        st.caption(activity_description(st.session_state.calc_lifestyle_activity))
        st.info(t("activity_extra_info"))
        st.number_input(t("walk_km"), min_value=0.0, max_value=60.0, step=0.5, key="calc_walk_km", help=t("walk_help"))
        st.number_input(t("run_km"), min_value=0.0, max_value=60.0, step=0.5, key="calc_run_km", help=t("run_help"))
        st.number_input(t("strength_minutes"), min_value=0.0, max_value=300.0, step=5.0, key="calc_strength_minutes", help=t("strength_minutes_help"))
        st.selectbox(t("strength_intensity"), options=list(STRENGTH_INTENSITIES.keys()), format_func=strength_label, key="calc_strength_intensity", help=t("strength_intensity_help"))
        st.selectbox(t("goal_nutrition"), options=list(GOAL_MODES.keys()), format_func=goal_label, key="calc_goal_mode", help=t("goal_nutrition_help"))

    update_profile_from_inputs()
    recommendation = calculate_recommended_targets(st.session_state.targets["calculator_profile"])

    if recommendation["body_fat_error"]:
        st.warning(recommendation["body_fat_error"])

    summary_columns = st.columns(4)
    summary_columns[0].metric(t("estimated_metabolism"), f"{format_number(recommendation['weighted_ree'])} kcal")
    summary_columns[1].metric(t("estimated_maintenance"), f"{format_number(recommendation['maintenance_kcal'])} kcal")
    summary_columns[2].metric(t("calorie_goal"), f"{format_number(recommendation['target_macros']['Calories'])} kcal")
    if recommendation["body_fat_pct"] is not None:
        summary_columns[3].metric(t("estimated_body_fat"), f"{recommendation['body_fat_pct']:.1f}%")
    else:
        summary_columns[3].metric(t("body_fat"), t("body_fat_unused"))

    with st.expander(t("calc_details")):
        st.markdown(t("calc_base_eq"))
        st.write(t("calc_mifflin"))
        st.write(t("calc_schofield"))
        st.write(t("calc_cunningham"))
        st.markdown(t("calc_weighting"))
        st.write(t("calc_weighting_no_bf"))
        st.write(t("calc_weighting_bf"))
        st.markdown(t("calc_navy"))
        st.write(t("calc_navy_male"))
        st.write(t("calc_navy_female"))
        st.markdown(t("calc_activity"))
        st.write(t("calc_activity_text"))
        st.write(t("calc_walk_formula"))
        st.write(t("calc_run_formula"))
        st.write(t("calc_strength_formula"))
        st.markdown(t("calc_goal_macros"))
        st.write(t("calc_goal_macros_text"))
        st.markdown(t("calc_limits"))
        st.write(t("calc_limits_text"))
        for method_name, value in recommendation["ree_methods"].items():
            st.write(f"{method_name} : {format_number(value)} kcal")
        st.write(t("activity_factor_detail", value=f"{recommendation['activity_factor']:.2f}"))
        st.write(t("neat_kcal_detail", value=format_number(recommendation["neat_kcal"])))
        st.write(t("exercise_kcal_detail", walk=format_number(recommendation["exercise_kcal"]["walk"]), run=format_number(recommendation["exercise_kcal"]["run"]), strength=format_number(recommendation["exercise_kcal"]["strength"])))

    st.markdown(t("auto_reco"))
    recommendation_columns = st.columns(4)
    for column, nutrient_name in zip(recommendation_columns, MACRO_CONFIG):
        config = MACRO_CONFIG[nutrient_name]
        column.metric(nutrient_label(nutrient_name), f"{format_number(recommendation['target_macros'][nutrient_name])} {config['unit']}")

    st.caption(t("micro_adjustment_caption"))

    render_notice("targets_reco")
    if st.button(t("apply_reco")):
        apply_recommended_targets(recommendation)
        push_notice(t("applied_reco_notice"), "targets_reco")
        rerun_with_live_state()

    return recommendation


def render_targets_editor(targets: dict) -> None:
    st.subheader(t("targets_subheader"))
    st.write(t("targets_intro"))

    render_energy_calculator()

    st.markdown(t("editable_targets"))
    macro_columns = st.columns(2)
    for index, (nutrient_name, config) in enumerate(MACRO_CONFIG.items()):
        with macro_columns[index % 2]:
            st.session_state.target_inputs[nutrient_name] = st.number_input(
                f"{nutrient_label(nutrient_name)} ({config['unit']})",
                min_value=0.0,
                step=10.0,
                key=f"target_{nutrient_name}",
            )

    st.markdown(t("micros_section"))
    micro_columns = st.columns(2)
    for index, (nutrient_name, config) in enumerate(MICRO_CONFIG.items()):
        with micro_columns[index % 2]:
            step = 0.5 if config["unit"] in {"mg", "µg", "µg ÉRA"} else 1.0
            st.session_state.target_inputs[nutrient_name] = st.number_input(
                f"{nutrient_label(nutrient_name)} ({config['unit']})",
                min_value=0.0,
                step=step,
                key=f"target_{nutrient_name}",
            )

    save_col, reset_col = st.columns(2)
    save_col.button(
        t("save_targets"),
        type="primary",
        on_click=save_targets_from_inputs,
    )
    reset_col.button(
        t("reset_targets"),
        on_click=reset_targets_to_defaults,
    )
    render_notice("targets_actions")


def render_saved_meals(foods: dict) -> None:
    st.subheader(t("saved_meals_subheader"))
    st.write(t("saved_meals_intro"))

    save_name = st.text_input(t("meal_name"), value=st.session_state.meal_name, placeholder=t("meal_name_placeholder"))
    st.session_state.meal_name = save_name

    render_notice("saved_meal_save")
    if st.button(t("save_meal"), type="primary"):
        if not save_name.strip():
            st.error(t("meal_name_required"))
        elif not st.session_state.meal_items:
            st.error(t("meal_empty_current"))
        else:
            meal_path = save_meal(save_name.strip(), st.session_state.meal_items)
            push_notice(t("meal_saved", filename=meal_path.name), "saved_meal_save")
            rerun_with_live_state()

    meals, meals_error = list_saved_meals()
    if meals_error:
        st.error(meals_error)
        return

    if not meals:
        st.info(t("no_saved_meals"))
        return

    meal_options = {
        (f"{meal['name']} - {meal['created_at']}" if meal["created_at"] else meal["name"]): meal
        for meal in meals
    }
    selected_label = st.selectbox(t("saved_meals_list"), options=list(meal_options.keys()))
    selected_meal = meal_options[selected_label]

    if selected_meal["invalid"]:
        st.warning(t("invalid_meal_file"))
        return

    st.caption(t("file_caption", filename=selected_meal["path"].name))

    render_notice("saved_meal_load")
    if st.button(t("load_meal")):
        loaded_items, load_error = load_meal_file(selected_meal["path"])
        if load_error:
            st.error(load_error)
            return

        missing_foods = [food_name for food_name in loaded_items if food_name not in foods]
        st.session_state.meal_items = {
            food_name: quantity
            for food_name, quantity in loaded_items.items()
            if food_name in foods
        }
        for key in list(st.session_state.keys()):
            if key.startswith("qty_"):
                st.session_state.pop(key)
        for food_name, quantity in st.session_state.meal_items.items():
            st.session_state[f"qty_{food_name}"] = quantity

        st.session_state.meal_name = selected_meal["name"]
        if missing_foods:
            push_notice(
                t("meal_loaded_partial", name=selected_meal["name"], foods=format_food_names(missing_foods)),
                "saved_meal_load",
                kind="warning",
            )
        else:
            push_notice(t("meal_loaded", name=selected_meal["name"]), "saved_meal_load")
        rerun_with_live_state()


def initialize_state(
    targets: dict,
    favorite_foods: list[str] | None = None,
    live_state: dict | None = None,
) -> None:
    favorite_foods = favorite_foods or []
    targets = restore_targets_from_live_state(targets, live_state)
    persisted_lang = targets.get("app_settings", {}).get("language", "fr")
    if "lang" not in st.session_state:
        st.session_state.lang = persisted_lang
    if "targets" not in st.session_state:
        st.session_state.targets = deepcopy(targets)
    else:
        st.session_state.targets["app_settings"] = deepcopy(targets.get("app_settings", DEFAULT_TARGETS["app_settings"]))
    live_meal = live_state.get("meal", {}) if isinstance(live_state, dict) else {}
    live_items = live_meal.get("items", {}) if isinstance(live_meal, dict) else {}
    restored_items = {}
    if isinstance(live_items, dict):
        for food_name, quantity in live_items.items():
            if isinstance(food_name, str) and isinstance(quantity, (int, float)) and not isinstance(quantity, bool):
                if math.isfinite(float(quantity)):
                    restored_items[food_name] = float(quantity)

    if "meal_items" not in st.session_state:
        st.session_state.meal_items = restored_items
        for food_name, quantity in restored_items.items():
            st.session_state[f"qty_{food_name}"] = quantity
    if "meal_name" not in st.session_state:
        st.session_state.meal_name = live_meal.get("name", "") if isinstance(live_meal, dict) else ""
        if not isinstance(st.session_state.meal_name, str):
            st.session_state.meal_name = ""
    if "notice" not in st.session_state:
        st.session_state.notice = None
    if "favorite_foods" not in st.session_state:
        st.session_state.favorite_foods = list(favorite_foods)
    if "food_search_query" not in st.session_state:
        st.session_state.food_search_query = ""
    if "food_search_mode" not in st.session_state:
        st.session_state.food_search_mode = "simple"
    if "simple_food_picker" not in st.session_state:
        st.session_state.simple_food_picker = None
    if "simple_food_picker_reset" not in st.session_state:
        st.session_state.simple_food_picker_reset = False
    if "food_favorites_only" not in st.session_state:
        st.session_state.food_favorites_only = False
    if "food_sort_nutrient" not in st.session_state:
        st.session_state.food_sort_nutrient = next(iter(MACRO_CONFIG))
    if "food_sort_mode" not in st.session_state:
        st.session_state.food_sort_mode = "alpha"
    if "target_inputs" not in st.session_state:
        st.session_state.target_inputs = {}
        for group_name, config in NUTRIENT_GROUPS.items():
            for nutrient_name in config:
                st.session_state.target_inputs[nutrient_name] = st.session_state.targets[group_name][nutrient_name]
    for group_name, config in NUTRIENT_GROUPS.items():
        for nutrient_name in config:
            widget_key = f"target_{nutrient_name}"
            if widget_key not in st.session_state:
                st.session_state[widget_key] = st.session_state.target_inputs[nutrient_name]
    for field_name, value in st.session_state.targets["calculator_profile"].items():
        session_key = f"calc_{field_name}"
        if session_key not in st.session_state:
            st.session_state[session_key] = value
    if "language_selector" not in st.session_state:
        st.session_state.language_selector = st.session_state.lang
