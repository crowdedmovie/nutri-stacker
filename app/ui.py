from copy import deepcopy

import flet as ft

from app.calculations import calculate_recommended_targets, calculate_totals, sync_selected_foods
from app.config import ACTIVITY_FACTORS, DEFAULT_TARGETS, GOAL_MODES, MACRO_CONFIG, MICRO_CONFIG, NUTRIENT_GROUPS, STRENGTH_INTENSITIES
from app.i18n import LANGUAGE_OPTIONS, activity_description, activity_label, food_label, format_food_names, goal_label, nutrient_label, set_lang, strength_label, t
from app.storage import list_saved_meals, load_meal_file, save_meal, save_targets


def format_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


def initialize_state(targets: dict) -> dict:
    state = {
        "lang": targets.get("app_settings", {}).get("language", "fr"),
        "targets": deepcopy(targets),
        "meal_items": {},
        "meal_name": "",
        "target_inputs": {},
        "calculator_profile": deepcopy(targets["calculator_profile"]),
        "selected_meal_key": None,
        "nav_index": 0,
        "food_filter": "",
    }
    for group_name, config in NUTRIENT_GROUPS.items():
        for nutrient_name in config:
            state["target_inputs"][nutrient_name] = float(targets[group_name][nutrient_name])
    set_lang(state["lang"])
    return state


def _card(content: ft.Control, padding: int = 16) -> ft.Control:
    return ft.Card(content=ft.Container(content=content, padding=padding), elevation=2)


def _section_title(value: str) -> ft.Text:
    return ft.Text(value, size=20, weight=ft.FontWeight.BOLD)


class NutriStackerApp:
    """Flet presentation layer for the existing Nutri Stacker domain logic."""

    def __init__(self, page: ft.Page, foods: dict, targets: dict, foods_error: str | None, targets_error: str | None):
        self.page = page
        self.foods = foods
        self.foods_error = foods_error
        self.targets_error = targets_error
        self.state = initialize_state(targets)

    def mount(self) -> None:
        self.page.on_resize = self.handle_resize
        self.refresh()

    def is_mobile(self) -> bool:
        width = getattr(self.page, "width", None)
        return width is not None and width > 0 and width < 700

    def handle_resize(self, _e) -> None:
        mobile = self.is_mobile()
        if mobile != getattr(self, "_last_mobile_layout", None):
            self.refresh()

    def refresh(self, *_args) -> None:
        set_lang(self.state["lang"])
        self._last_mobile_layout = self.is_mobile()
        self.page.controls.clear()
        self.page.add(ft.SafeArea(expand=True, content=self.build()))

    def notice(self, message: str, kind: str = "success") -> None:
        color = {"success": ft.Colors.GREEN_700, "warning": ft.Colors.ORANGE_800, "error": ft.Colors.RED_700}.get(kind, ft.Colors.BLUE_700)
        self.page.show_dialog(ft.SnackBar(ft.Text(message), bgcolor=color))

    def build(self) -> ft.Control:
        language = ft.Dropdown(
            label=t("language"),
            value=self.state["lang"],
            options=[ft.DropdownOption(key=code, text=label) for code, label in LANGUAGE_OPTIONS.items()],
            width=180,
            on_select=self.change_language,
            helper_text=t("language_help"),
        )
        title_block = ft.Column([ft.Text(t("app_title"), size=32 if not self.is_mobile() else 26, weight=ft.FontWeight.BOLD), ft.Text(t("app_intro"), size=16)], spacing=4, expand=True)
        if self.is_mobile():
            header = ft.Column([title_block, language], spacing=10)
        else:
            header = ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, vertical_alignment=ft.CrossAxisAlignment.START, controls=[title_block, language])
        messages = []
        if self.foods_error:
            messages.append(ft.Text(self.foods_error, color=ft.Colors.RED_700))
        if self.targets_error:
            messages.append(ft.Text(self.targets_error, color=ft.Colors.ORANGE_800))

        destinations = [
            (ft.Icons.RESTAURANT, ft.Icons.FASTFOOD, t("tab_meal")),
            (ft.Icons.TUNE, ft.Icons.TUNE, t("tab_targets")),
            (ft.Icons.FOLDER_SPECIAL, ft.Icons.FOLDER_SPECIAL, t("tab_saved_meals")),
        ]
        body = ft.Column([header, *messages, self.current_view()], expand=True, spacing=14 if self.is_mobile() else 18, scroll=ft.ScrollMode.AUTO)
        if self.is_mobile():
            navigation = ft.NavigationBar(
                selected_index=self.state["nav_index"],
                label_behavior=ft.NavigationBarLabelBehavior.ALWAYS_SHOW,
                on_change=self.navigation_changed,
                destinations=[ft.NavigationBarDestination(icon=icon, selected_icon=selected_icon, label=label) for icon, selected_icon, label in destinations],
            )
            workspace = ft.Column([body, navigation], expand=True, spacing=0)
            return ft.Container(content=workspace, padding=12, expand=True)
        navigation = ft.NavigationRail(
            selected_index=self.state["nav_index"],
            extended=True,
            label_type=ft.NavigationRailLabelType.ALL,
            min_width=72,
            min_extended_width=190,
            on_change=self.navigation_changed,
            destinations=[ft.NavigationRailDestination(icon=icon, selected_icon=selected_icon, label=label) for icon, selected_icon, label in destinations],
        )
        workspace = ft.Row([navigation, ft.VerticalDivider(width=1), body], expand=True, vertical_alignment=ft.CrossAxisAlignment.START)
        return ft.Container(content=workspace, padding=24, expand=True)

    def change_language(self, e: ft.Event[ft.Dropdown]) -> None:
        self.state["lang"] = e.control.value or "fr"
        self.state["targets"]["app_settings"]["language"] = self.state["lang"]
        save_targets(self.state["targets"])
        self.refresh()

    def navigation_changed(self, e) -> None:
        self.state["nav_index"] = e.control.selected_index
        self.refresh()

    def current_view(self) -> ft.Control:
        return [self.meal_view, self.targets_view, self.saved_meals_view][self.state["nav_index"]]()

    def meal_view(self) -> ft.Control:
        selected = set(self.state["meal_items"])
        filter_field = ft.TextField(
            label=t("foods_label"),
            hint_text=t("foods_placeholder"),
            value=self.state["food_filter"],
            on_change=self.food_filter_changed,
        )
        filter_value = self.state["food_filter"].casefold().strip()
        food_checks = [
            ft.Checkbox(label=food_label(name), value=name in selected, data=name, on_change=self.food_selection_changed)
            for name in sorted(self.foods, key=food_label)
            if not filter_value or filter_value in food_label(name).casefold() or filter_value in name.casefold()
        ]
        picker = ft.ListView(food_checks, expand=True, spacing=2)
        picker_card = ft.Container(content=picker, height=310, padding=10, border=ft.Border.all(1, "#D9DEE8"), border_radius=12)
        input_panel = ft.Column([filter_field, picker_card, self.selected_foods_view()], expand=True, spacing=12)
        totals = calculate_totals(self.state["meal_items"], self.foods)
        result_panel = self.nutrition_view(*totals)
        return ft.Column([_section_title(t("meal_subheader")), ft.Text(t("meal_intro")), ft.ResponsiveRow([ft.Container(input_panel, col={"sm": 12, "md": 5}), ft.Container(result_panel, col={"sm": 12, "md": 7})], spacing=20)], spacing=10)

    def food_selection_changed(self, e: ft.Event[ft.Checkbox]) -> None:
        selected = set(self.state["meal_items"])
        if e.control.value:
            selected.add(e.control.data)
        else:
            selected.discard(e.control.data)
        sync_selected_foods(list(selected), self.foods, self.state)
        self.refresh()

    def food_filter_changed(self, e: ft.Event[ft.TextField]) -> None:
        self.state["food_filter"] = e.control.value or ""
        self.refresh()

    def selected_foods_view(self) -> ft.Control:
        if not self.state["meal_items"]:
            return ft.Container(content=ft.Text(t("meal_empty"), color=ft.Colors.BLUE_700), padding=8)
        controls = [ft.Text(t("selected_foods"), size=18, weight=ft.FontWeight.BOLD)]
        for food_name, quantity in self.state["meal_items"].items():
            food = self.foods.get(food_name)
            if not food:
                continue
            reference_quantity = food.get("Ref_Qte", 1)
            reference_unit = food.get("Unite", "")
            quantity_field = ft.TextField(
                label=t("quantity_label"), value=str(quantity), width=150,
                keyboard_type=ft.KeyboardType.NUMBER, tooltip=t("quantity_help", unit=reference_unit),
                data=food_name, on_change=self.quantity_changed, on_blur=self.commit_quantity, on_submit=self.commit_quantity,
            )
            detail = calculate_totals({food_name: float(quantity)}, self.foods)[2]
            detail_control = self.food_breakdown(detail[0]) if detail else ft.Container()
            controls.append(_card(ft.Column([
                ft.Row([ft.Column([ft.Text(food_label(food_name), weight=ft.FontWeight.BOLD), ft.Text(f"{t('reference_label')} : {reference_quantity} {reference_unit}")], expand=True), quantity_field], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.ExpansionTile(title=t("food_detail"), controls=[detail_control]),
            ], spacing=8)))
        return ft.Column(controls, spacing=8)

    def quantity_changed(self, e: ft.Event[ft.TextField]) -> None:
        try:
            value = max(float(e.control.value or 0), 0.0)
        except ValueError:
            return
        self.state["meal_items"][e.control.data] = value
        self.state[f"qty_{e.control.data}"] = value

    def commit_quantity(self, _e) -> None:
        self.refresh()

    def nutrition_view(self, macro_totals: dict, micro_totals: dict, details: list[dict], missing_foods: list[str]) -> ft.Control:
        controls = [_section_title(t("nutrition_analysis"))]
        if missing_foods:
            controls.append(ft.Text(t("missing_saved_foods", foods=format_food_names(missing_foods)), color=ft.Colors.ORANGE_800))
        if not details:
            controls.append(ft.Container(content=ft.Text(t("results_waiting")), padding=20))
            return ft.Column(controls, spacing=12)
        macro_cards = []
        targets = self.state["targets"]
        for name, config in MACRO_CONFIG.items():
            current = macro_totals[name]
            target = targets["macros"][name]
            percent = 0 if target <= 0 else current / target * 100
            macro_cards.append(_card(ft.Column([ft.Text(nutrient_label(name)), ft.Text(f"{format_number(current)} {config['unit']}", size=24, weight=ft.FontWeight.BOLD), ft.Text(f"{t('target_word')}: {format_number(target)} {config['unit']} ({percent:.0f}%)"), ft.ProgressBar(value=0 if target <= 0 else min(current / target, 1), bar_height=8)], spacing=6)))
        controls.append(ft.ResponsiveRow([ft.Container(card, col={"sm": 12, "md": 6, "lg": 3}) for card in macro_cards], spacing=10))
        columns = [ft.DataColumn(ft.Text(t("micro_header_nutrient"))), ft.DataColumn(ft.Text(t("micro_header_current")), numeric=True), ft.DataColumn(ft.Text(t("micro_header_target")), numeric=True), ft.DataColumn(ft.Text(t("micro_header_percent")), numeric=True), ft.DataColumn(ft.Text(t("micro_header_gap"))), ft.DataColumn(ft.Text(t("micro_header_progress")))]
        rows = []
        mobile_rows = []
        for name, config in MICRO_CONFIG.items():
            current = micro_totals[name]
            target = targets["micros"][name]
            percent = 0 if target <= 0 else current / target * 100
            difference = current - target
            status = t("status_excess", value=format_number(difference), unit=config["unit"]) if difference >= 0 else t("status_remaining", value=format_number(abs(difference)), unit=config["unit"])
            rows.append(ft.DataRow(cells=[ft.DataCell(ft.Text(nutrient_label(name))), ft.DataCell(ft.Text(f"{format_number(current)} {config['unit']}")), ft.DataCell(ft.Text(f"{format_number(target)} {config['unit']}")), ft.DataCell(ft.Text(f"{percent:.0f}%")), ft.DataCell(ft.Text(status)), ft.DataCell(ft.ProgressBar(value=0 if target <= 0 else min(current / target, 1), width=90))]))
            mobile_rows.append(_card(ft.Column([
                ft.Row([ft.Text(nutrient_label(name), weight=ft.FontWeight.BOLD, expand=True), ft.Text(f"{percent:.0f}%", weight=ft.FontWeight.BOLD)]),
                ft.Text(f"{format_number(current)} {config['unit']} / {format_number(target)} {config['unit']}"),
                ft.Text(status),
                ft.ProgressBar(value=0 if target <= 0 else min(current / target, 1), bar_height=8),
            ], spacing=5), padding=12))
        if self.is_mobile():
            micro_content = ft.ListView(mobile_rows, spacing=8, expand=True)
        else:
            micro_content = ft.Row([ft.DataTable(columns=columns, rows=rows, column_spacing=14)], scroll=ft.ScrollMode.AUTO)
        controls.extend([ft.Text(t("micronutrients_title"), size=20, weight=ft.FontWeight.BOLD), ft.Container(content=micro_content, padding=8, expand=True)])
        return ft.Column(controls, spacing=12)

    def food_breakdown(self, detail: dict) -> ft.Control:
        macros = [ft.Text(f"{nutrient_label(name)}: {format_number(detail['macros'][name])} {config['unit']}") for name, config in MACRO_CONFIG.items()]
        micros = [ft.Text(f"{nutrient_label(name)}: {format_number(detail['micros'][name])} {config['unit']}") for name, config in MICRO_CONFIG.items()]
        return ft.Column([ft.Text(t("food_macros_title"), weight=ft.FontWeight.BOLD), ft.Row(macros, wrap=True), ft.Text(t("food_micros_title"), weight=ft.FontWeight.BOLD), ft.Row(micros, wrap=True)], spacing=6)

    def targets_view(self) -> ft.Control:
        profile = self.state["calculator_profile"]
        recommendation = calculate_recommended_targets(profile)
        profile_fields = self.profile_fields(profile)
        summary = ft.ResponsiveRow([ft.Container(_card(ft.Column([ft.Text(label), ft.Text(value, size=20, weight=ft.FontWeight.BOLD)])), col={"sm": 12, "md": 3}) for label, value in [
            (t("estimated_metabolism"), f"{format_number(recommendation['weighted_ree'])} kcal"),
            (t("estimated_maintenance"), f"{format_number(recommendation['maintenance_kcal'])} kcal"),
            (t("calorie_goal"), f"{format_number(recommendation['target_macros']['Calories'])} kcal"),
            (t("estimated_body_fat"), f"{recommendation['body_fat_pct']:.1f}%" if recommendation["body_fat_pct"] is not None else t("body_fat_unused")),
        ]], spacing=10)
        if recommendation["body_fat_error"]:
            profile_fields.insert(0, ft.Text(recommendation["body_fat_error"], color=ft.Colors.ORANGE_800))
        macro_reco = ft.Row([ft.Text(f"{nutrient_label(name)}: {format_number(value)} {MACRO_CONFIG[name]['unit']}") for name, value in recommendation["target_macros"].items()], wrap=True)
        return ft.Column([
            _section_title(t("targets_subheader")), ft.Text(t("targets_intro")),
            _card(ft.Column([
                ft.Text(t("energy_calculator_title"), size=20, weight=ft.FontWeight.BOLD), ft.Text(t("energy_calculator_intro")),
                ft.ResponsiveRow([ft.Container(ft.Column(profile_fields, spacing=10), col={"sm": 12, "md": 6}), ft.Container(ft.Column(self.activity_fields(profile), spacing=10), col={"sm": 12, "md": 6})], spacing=20),
                ft.FilledButton(t("apply_reco"), on_click=self.apply_recommendation),
            ], spacing=12)),
            summary, ft.Text(t("auto_reco"), size=18, weight=ft.FontWeight.BOLD), macro_reco,
            self.target_editor(), ft.Row([ft.FilledButton(t("save_targets"), on_click=self.save_targets_clicked), ft.OutlinedButton(t("reset_targets"), on_click=self.reset_targets_clicked)], spacing=10),
        ], spacing=14)

    def profile_fields(self, profile: dict) -> list[ft.Control]:
        fields = [ft.Text(t("profile_section"), size=16, weight=ft.FontWeight.BOLD)]
        fields += [self.dropdown(t("sex"), profile["sex"], ["homme", "femme"], lambda value: self.profile_changed("sex", value), lambda value: t("male") if value == "homme" else t("female"))]
        fields += [self.number_field(t("age"), profile["age"], "age", 15, 90), self.number_field(t("height_cm"), profile["height_cm"], "height_cm", 120, 230), self.number_field(t("weight_kg"), profile["weight_kg"], "weight_kg", 35, 250)]
        body_options = ["unknown", "known", "estimate_navy"]
        fields.append(self.dropdown(t("body_fat"), profile["body_fat_mode"], body_options, lambda value: self.profile_changed("body_fat_mode", value), lambda value: {"unknown": t("body_fat_unknown"), "known": t("body_fat_known"), "estimate_navy": t("body_fat_estimate")}[value]))
        if profile["body_fat_mode"] == "known":
            fields.append(self.number_field(t("body_fat_pct"), profile["body_fat_pct"], "body_fat_pct", 2, 60))
        elif profile["body_fat_mode"] == "estimate_navy":
            fields.extend([self.number_field(t("neck_cm"), profile["neck_cm"], "neck_cm", 20, 70), self.number_field(t("waist_cm"), profile["waist_cm"], "waist_cm", 40, 200)])
            if profile["sex"] == "femme":
                fields.append(self.number_field(t("hip_cm"), profile["hip_cm"], "hip_cm", 50, 220))
        return fields

    def activity_fields(self, profile: dict) -> list[ft.Control]:
        return [ft.Text(t("activity_goal_section"), size=16, weight=ft.FontWeight.BOLD), self.dropdown(t("activity_daily"), profile["lifestyle_activity"], list(ACTIVITY_FACTORS), lambda value: self.profile_changed("lifestyle_activity", value), activity_label), ft.Text(activity_description(profile["lifestyle_activity"])), self.number_field(t("walk_km"), profile["walk_km"], "walk_km", 0, 60), self.number_field(t("run_km"), profile["run_km"], "run_km", 0, 60), self.number_field(t("strength_minutes"), profile["strength_minutes"], "strength_minutes", 0, 300), self.dropdown(t("strength_intensity"), profile["strength_intensity"], list(STRENGTH_INTENSITIES), lambda value: self.profile_changed("strength_intensity", value), strength_label), self.dropdown(t("goal_nutrition"), profile["goal_mode"], list(GOAL_MODES), lambda value: self.profile_changed("goal_mode", value), goal_label)]

    def dropdown(self, label: str, value: str, options: list[str], callback, formatter=lambda value: value) -> ft.Control:
        return ft.Dropdown(label=label, value=value, options=[ft.DropdownOption(key=option, text=formatter(option)) for option in options], on_select=lambda e: callback(e.control.value), expand=True)

    def number_field(self, label: str, value, key: str, minimum: float, maximum: float) -> ft.Control:
        return ft.TextField(label=label, value=str(value), data=key, keyboard_type=ft.KeyboardType.NUMBER, on_change=self.number_changed, on_blur=self.commit_profile, on_submit=self.commit_profile, expand=True)

    def number_changed(self, e: ft.Event[ft.TextField]) -> None:
        try:
            value = float(e.control.value)
        except (TypeError, ValueError):
            return
        if e.control.data == "age":
            value = int(value)
        self.state["calculator_profile"][e.control.data] = value

    def commit_profile(self, _e) -> None:
        self.refresh()

    def profile_changed(self, key: str, value: str) -> None:
        self.state["calculator_profile"][key] = value
        self.refresh()

    def target_editor(self) -> ft.Control:
        fields = []
        for group_name, config in NUTRIENT_GROUPS.items():
            fields.append(ft.Text(t("editable_targets") if group_name == "macros" else t("micros_section"), size=18, weight=ft.FontWeight.BOLD))
            fields.extend(ft.TextField(label=f"{nutrient_label(name)} ({item['unit']})", value=str(self.state["target_inputs"][name]), data=name, keyboard_type=ft.KeyboardType.NUMBER, on_change=self.target_changed, on_blur=self.commit_targets, on_submit=self.commit_targets, expand=True) for name, item in config.items())
        return ft.ResponsiveRow([ft.Container(field, col={"sm": 12, "md": 6}) for field in fields], spacing=8)

    def target_changed(self, e: ft.Event[ft.TextField]) -> None:
        try:
            self.state["target_inputs"][e.control.data] = max(float(e.control.value), 0.0)
        except (TypeError, ValueError):
            pass

    def commit_targets(self, _e) -> None:
        self.refresh()

    def apply_recommendation(self, _e) -> None:
        recommendation = calculate_recommended_targets(self.state["calculator_profile"])
        for group_name, key in (("macros", "target_macros"), ("micros", "target_micros")):
            for name, value in recommendation[key].items():
                self.state["target_inputs"][name] = float(value)
        self.state["targets"]["macros"] = {name: self.state["target_inputs"][name] for name in MACRO_CONFIG}
        self.state["targets"]["micros"] = {name: self.state["target_inputs"][name] for name in MICRO_CONFIG}
        self.notice(t("applied_reco_notice"))
        self.refresh()

    def save_targets_clicked(self, _e) -> None:
        targets = deepcopy(self.state["targets"])
        targets["macros"] = {name: float(self.state["target_inputs"][name]) for name in MACRO_CONFIG}
        targets["micros"] = {name: float(self.state["target_inputs"][name]) for name in MICRO_CONFIG}
        targets["calculator_profile"] = deepcopy(self.state["calculator_profile"])
        save_targets(targets)
        self.state["targets"] = targets
        self.notice(t("targets_saved"))

    def reset_targets_clicked(self, _e) -> None:
        self.state["targets"] = deepcopy(DEFAULT_TARGETS)
        self.state["calculator_profile"] = deepcopy(DEFAULT_TARGETS["calculator_profile"])
        self.state["target_inputs"] = {name: float(DEFAULT_TARGETS[group][name]) for group, config in NUTRIENT_GROUPS.items() for name in config}
        save_targets(self.state["targets"])
        self.notice(t("targets_reset"))
        self.refresh()

    def saved_meals_view(self) -> ft.Control:
        name_field = ft.TextField(label=t("meal_name"), value=self.state["meal_name"], hint_text=t("meal_name_placeholder"), on_change=lambda e: self.state.__setitem__("meal_name", e.control.value))
        controls = [_section_title(t("saved_meals_subheader")), ft.Text(t("saved_meals_intro")), name_field, ft.FilledButton(t("save_meal"), on_click=self.save_meal_clicked)]
        meals, meals_error = list_saved_meals()
        if meals_error:
            controls.append(ft.Text(meals_error, color=ft.Colors.RED_700))
            return ft.Column(controls, spacing=12)
        if not meals:
            controls.append(ft.Text(t("no_saved_meals"), color=ft.Colors.BLUE_700))
            return ft.Column(controls, spacing=12)
        options = [(f"{meal['name']} - {meal['created_at']}" if meal["created_at"] else meal["name"], meal) for meal in meals]
        option_map = dict(options)
        selected_key = self.state["selected_meal_key"] if self.state["selected_meal_key"] in option_map else options[0][0]
        selected = option_map[selected_key]
        selector = ft.Dropdown(label=t("saved_meals_list"), value=selected_key, options=[ft.DropdownOption(key=label, text=label) for label, _ in options], on_select=self.saved_meal_selected)
        controls.extend([selector, ft.Text(t("file_caption", filename=selected["path"].name)), ft.FilledButton(t("load_meal"), data=selected, on_click=self.load_meal_clicked)])
        if selected["invalid"]:
            controls.append(ft.Text(t("invalid_meal_file"), color=ft.Colors.ORANGE_800))
        return ft.Column(controls, spacing=12)

    def saved_meal_selected(self, e) -> None:
        self.state["selected_meal_key"] = e.control.value
        self.refresh()

    def save_meal_clicked(self, _e) -> None:
        name = self.state["meal_name"].strip()
        if not name:
            self.notice(t("meal_name_required"), "error")
        elif not self.state["meal_items"]:
            self.notice(t("meal_empty_current"), "error")
        else:
            path = save_meal(name, self.state["meal_items"])
            self.notice(t("meal_saved", filename=path.name))

    def load_meal_clicked(self, e) -> None:
        selected = e.control.data
        loaded, error = load_meal_file(selected["path"])
        if error:
            self.notice(error, "error")
            return
        missing = [name for name in loaded if name not in self.foods]
        self.state["meal_items"] = {name: quantity for name, quantity in loaded.items() if name in self.foods}
        self.state["meal_name"] = selected["name"]
        self.refresh()
        if missing:
            self.notice(t("meal_loaded_partial", name=selected["name"], foods=format_food_names(missing)), "warning")
        else:
            self.notice(t("meal_loaded", name=selected["name"]))
