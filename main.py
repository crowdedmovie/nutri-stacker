import json
import re
import unicodedata
from copy import deepcopy
from datetime import datetime, UTC
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="Nutri Stacker",
    page_icon="🥗",
    layout="wide",
)


APP_DIR = Path(__file__).parent
FOOD_FILE = APP_DIR / "food.json"
TARGETS_FILE = APP_DIR / "user_targets.json"
MEALS_DIR = APP_DIR / "saved_meals"

MACRO_CONFIG = {
    "Calories": {"label": "Calories", "unit": "kcal"},
    "Proteines": {"label": "Protéines", "unit": "g"},
    "Glucides": {"label": "Glucides", "unit": "g"},
    "Lipides": {"label": "Lipides", "unit": "g"},
}

MICRO_CONFIG = {
    "Magnesium": {"label": "Magnésium", "unit": "mg"},
    "Bore": {"label": "Bore", "unit": "mg"},
    "Cholesterol": {"label": "Cholestérol", "unit": "mg"},
    "Sodium": {"label": "Sodium", "unit": "mg"},
    "Calcium": {"label": "Calcium", "unit": "mg"},
    "Iode": {"label": "Iode", "unit": "µg"},
    "Omega3": {"label": "Oméga-3", "unit": "mg"},
    "Potassium": {"label": "Potassium", "unit": "mg"},
    "Selenium": {"label": "Sélénium", "unit": "µg"},
    "VitamineA": {"label": "Vitamine A", "unit": "µg ÉRA"},
    "VitamineC": {"label": "Vitamine C", "unit": "mg"},
}

DEFAULT_TARGETS = {
    "macros": {
        "Calories": 2000.0,
        "Proteines": 150.0,
        "Glucides": 250.0,
        "Lipides": 70.0,
    },
    "micros": {
        "Magnesium": 450.0,
        "Bore": 4.5,
        "Cholesterol": 850.0,
        "Sodium": 3000.0,
        "Calcium": 1000.0,
        "Iode": 175.0,
        "Omega3": 2500.0,
        "Potassium": 4350.0,
        "Selenium": 112.5,
        "VitamineA": 900.0,
        "VitamineC": 350.0,
    },
}

NUTRIENT_GROUPS = {
    "macros": MACRO_CONFIG,
    "micros": MICRO_CONFIG,
}


def inject_styles() -> None:
    st.markdown(
        """
        <style>
        .macro-card {
            border: 1px solid #d6dde5;
            border-radius: 14px;
            padding: 1rem;
            background: linear-gradient(180deg, #ffffff 0%, #f7fafc 100%);
            min-height: 150px;
        }
        .macro-label {
            color: #51606f;
            font-size: 0.95rem;
            margin-bottom: 0.3rem;
        }
        .macro-value {
            font-size: 1.55rem;
            font-weight: 700;
            color: #132238;
            margin-bottom: 0.15rem;
        }
        .macro-target {
            color: #51606f;
            font-size: 0.9rem;
            margin-bottom: 0.8rem;
        }
        .table-header {
            font-weight: 700;
            color: #132238;
            border-bottom: 1px solid #d6dde5;
            padding-bottom: 0.45rem;
            margin-bottom: 0.5rem;
        }
        .food-summary {
            border: 1px solid #dfe6ee;
            border-radius: 12px;
            padding: 0.75rem 1rem;
            background: #fafcfe;
            margin-bottom: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def read_json_file(path: Path):
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def write_json_file(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        json.dump(payload, file, indent=2, ensure_ascii=False)


def ensure_storage() -> None:
    MEALS_DIR.mkdir(parents=True, exist_ok=True)
    if not TARGETS_FILE.exists():
        write_json_file(TARGETS_FILE, DEFAULT_TARGETS)


def normalize_targets(raw_targets) -> dict:
    normalized = deepcopy(DEFAULT_TARGETS)
    if not isinstance(raw_targets, dict):
        return normalized

    for group_name, config in NUTRIENT_GROUPS.items():
        candidate_group = raw_targets.get(group_name, {})
        if not isinstance(candidate_group, dict):
            continue
        for nutrient_name in config:
            value = candidate_group.get(nutrient_name)
            if isinstance(value, (int, float)):
                normalized[group_name][nutrient_name] = float(value)
    return normalized


def load_foods() -> tuple[dict, str | None]:
    try:
        foods = read_json_file(FOOD_FILE)
    except FileNotFoundError:
        return {}, "Le fichier `food.json` est introuvable."
    except json.JSONDecodeError as error:
        return {}, f"Le fichier `food.json` est invalide : {error}"

    if not isinstance(foods, dict):
        return {}, "Le fichier `food.json` doit contenir un objet JSON indexé par nom d'aliment."

    required_fields = {"Ref_Qte", "Unite", *MACRO_CONFIG.keys()}
    normalized_foods = {}

    for food_name, values in foods.items():
        if not isinstance(values, dict):
            continue
        missing_fields = required_fields.difference(values.keys())
        if missing_fields:
            return {}, (
                f"L'aliment '{food_name}' ne contient pas tous les champs requis : "
                f"{', '.join(sorted(missing_fields))}."
            )
        normalized_foods[food_name] = values

    return normalized_foods, None


def load_targets() -> tuple[dict, str | None]:
    try:
        raw_targets = read_json_file(TARGETS_FILE)
    except FileNotFoundError:
        normalized = deepcopy(DEFAULT_TARGETS)
        write_json_file(TARGETS_FILE, normalized)
        return normalized, None
    except json.JSONDecodeError as error:
        normalized = deepcopy(DEFAULT_TARGETS)
        write_json_file(TARGETS_FILE, normalized)
        return normalized, f"Le fichier `user_targets.json` était invalide et a été réinitialisé : {error}"

    normalized = normalize_targets(raw_targets)
    if normalized != raw_targets:
        write_json_file(TARGETS_FILE, normalized)
        return normalized, "Le fichier `user_targets.json` était incomplet. Les valeurs manquantes ont été complétées."
    return normalized, None


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", normalized.lower()).strip("-")
    return cleaned or "repas"


def list_saved_meals() -> tuple[list[dict], str | None]:
    meals = []
    try:
        files = sorted(MEALS_DIR.glob("*.json"))
    except OSError as error:
        return [], f"Impossible de lire le dossier `saved_meals` : {error}"

    for path in files:
        try:
            meal = read_json_file(path)
        except (OSError, json.JSONDecodeError):
            meals.append(
                {
                    "path": path,
                    "name": f"{path.stem} (fichier invalide)",
                    "created_at": "",
                    "items": [],
                    "invalid": True,
                }
            )
            continue

        meals.append(
            {
                "path": path,
                "name": meal.get("name", path.stem),
                "created_at": meal.get("created_at", ""),
                "items": meal.get("items", []),
                "invalid": False,
            }
        )
    return meals, None


def save_targets(targets: dict) -> None:
    write_json_file(TARGETS_FILE, targets)


def save_meal(name: str, items: dict[str, float]) -> Path:
    meal_payload = {
        "name": name,
        "created_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "items": [{"food": food_name, "quantity": quantity} for food_name, quantity in items.items()],
    }
    meal_path = MEALS_DIR / f"{slugify(name)}.json"
    write_json_file(meal_path, meal_payload)
    return meal_path


def load_meal_file(path: Path) -> tuple[dict, str | None]:
    try:
        meal = read_json_file(path)
    except FileNotFoundError:
        return {}, "Le fichier de repas n'existe plus."
    except json.JSONDecodeError as error:
        return {}, f"Le fichier de repas est invalide : {error}"

    items = meal.get("items", [])
    if not isinstance(items, list):
        return {}, "Le fichier de repas ne contient pas une liste `items` valide."

    loaded_items = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        food_name = item.get("food")
        quantity = item.get("quantity")
        if isinstance(food_name, str) and isinstance(quantity, (int, float)):
            loaded_items[food_name] = float(quantity)
    return loaded_items, None


def get_default_quantity(food_name: str, foods: dict) -> float:
    reference_quantity = foods[food_name].get("Ref_Qte", 1)
    if isinstance(reference_quantity, (int, float)) and reference_quantity > 0:
        return float(reference_quantity)
    return 1.0


def sync_selected_foods(selected_foods: list[str], foods: dict) -> None:
    current_items = st.session_state.meal_items

    for food_name in list(current_items):
        if food_name not in selected_foods:
            current_items.pop(food_name, None)
            st.session_state.pop(f"qty_{food_name}", None)

    for food_name in selected_foods:
        if food_name not in current_items:
            default_quantity = get_default_quantity(food_name, foods)
            current_items[food_name] = default_quantity
            st.session_state[f"qty_{food_name}"] = default_quantity


def calculate_totals(selected_items: dict[str, float], foods: dict) -> tuple[dict, dict, list[dict], list[str]]:
    macro_totals = {name: 0.0 for name in MACRO_CONFIG}
    micro_totals = {name: 0.0 for name in MICRO_CONFIG}
    details = []
    missing_foods = []

    for food_name, quantity in selected_items.items():
        food_data = foods.get(food_name)
        if not food_data:
            missing_foods.append(food_name)
            continue

        reference_quantity = food_data.get("Ref_Qte", 1) or 1
        multiplier = float(quantity) / float(reference_quantity)

        detail_row = {
            "food": food_name,
            "quantity": float(quantity),
            "unit": food_data.get("Unite", ""),
            "macros": {},
            "micros": {},
        }

        for nutrient_name in MACRO_CONFIG:
            amount = float(food_data.get(nutrient_name, 0.0)) * multiplier
            macro_totals[nutrient_name] += amount
            detail_row["macros"][nutrient_name] = amount

        for nutrient_name in MICRO_CONFIG:
            amount = float(food_data.get(nutrient_name, 0.0)) * multiplier
            micro_totals[nutrient_name] += amount
            detail_row["micros"][nutrient_name] = amount

        details.append(detail_row)

    return macro_totals, micro_totals, details, missing_foods


def format_number(value: float) -> str:
    if abs(value) >= 100:
        return f"{value:.0f}"
    if abs(value) >= 10:
        return f"{value:.1f}"
    return f"{value:.2f}"


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
                    f"<div class='macro-label'>{config['label']}</div>"
                    f"<div class='macro-value'>{format_number(current_value)} {config['unit']}</div>"
                    f"<div class='macro-target'>Cible: {format_number(target_value)} {config['unit']} "
                    f"({percent:.0f}%)</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
            st.progress(progress)


def render_micro_table(micro_totals: dict, targets: dict) -> None:
    header_columns = st.columns([2.3, 1.1, 1.1, 1.0, 1.3, 1.4])
    headers = ["Nutriment", "Actuel", "Cible", "% atteint", "Reste/Excès", "Progression"]
    for column, header in zip(header_columns, headers):
        with column:
            st.markdown(f"<div class='table-header'>{header}</div>", unsafe_allow_html=True)

    for nutrient_name, config in MICRO_CONFIG.items():
        current_value = micro_totals[nutrient_name]
        target_value = targets["micros"][nutrient_name]
        percent = 0.0 if target_value <= 0 else (current_value / target_value) * 100
        difference = current_value - target_value
        status = (
            f"Excès: +{format_number(difference)} {config['unit']}"
            if difference >= 0
            else f"Reste: {format_number(abs(difference))} {config['unit']}"
        )

        row_columns = st.columns([2.3, 1.1, 1.1, 1.0, 1.3, 1.4])
        row_columns[0].write(config["label"])
        row_columns[1].write(f"{format_number(current_value)} {config['unit']}")
        row_columns[2].write(f"{format_number(target_value)} {config['unit']}")
        row_columns[3].write(f"{percent:.0f}%")
        row_columns[4].write(status)
        with row_columns[5]:
            st.progress(0.0 if target_value <= 0 else min(current_value / target_value, 1.0))


def render_meal_builder(foods: dict, targets: dict) -> None:
    st.subheader("Repas")
    col_input, col_results = st.columns([1.05, 1.35], gap="large")

    with col_input:
        st.write("Sélectionne tes aliments puis ajuste les quantités dans leur unité de référence.")
        selected_foods = st.multiselect(
            "Aliments",
            options=sorted(foods.keys()),
            default=list(st.session_state.meal_items.keys()),
            placeholder="Rechercher un aliment...",
        )
        sync_selected_foods(selected_foods, foods)

        if not selected_foods:
            st.info("Ajoute au moins un aliment pour construire un repas.")
        else:
            for food_name in selected_foods:
                food_data = foods[food_name]
                reference_quantity = food_data["Ref_Qte"]
                reference_unit = food_data["Unite"]
                st.markdown(
                    (
                        "<div class='food-summary'>"
                        f"<strong>{food_name}</strong><br>"
                        f"Référence : {reference_quantity} {reference_unit}"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )
                quantity_key = f"qty_{food_name}"
                if quantity_key not in st.session_state:
                    st.session_state[quantity_key] = st.session_state.meal_items.get(
                        food_name,
                        get_default_quantity(food_name, foods),
                    )

                quantity = st.number_input(
                    f"Quantité pour {food_name}",
                    min_value=0.0,
                    value=float(st.session_state[quantity_key]),
                    step=1.0 if float(reference_quantity) == 1 else 10.0,
                    key=quantity_key,
                    help=f"Saisie dans l'unité '{reference_unit}'.",
                )
                st.session_state.meal_items[food_name] = float(quantity)

    macro_totals, micro_totals, details, missing_foods = calculate_totals(st.session_state.meal_items, foods)

    with col_results:
        st.subheader("Analyse nutritionnelle")
        if missing_foods:
            st.warning(
                "Certains aliments chargés depuis un repas sauvegardé sont introuvables dans `food.json` : "
                + ", ".join(missing_foods)
            )

        if details:
            render_macro_cards(macro_totals, targets)
            st.markdown("### Micronutriments")
            render_micro_table(micro_totals, targets)

            with st.expander("Voir le détail par aliment"):
                for detail in details:
                    st.write(
                        f"{detail['food']} - {format_number(detail['quantity'])} {detail['unit']} - "
                        f"{format_number(detail['macros']['Calories'])} kcal"
                    )
        else:
            st.info("Les résultats s'afficheront ici dès que tu ajoutes des aliments au repas.")


def render_targets_editor(targets: dict) -> None:
    st.subheader("Objectifs nutritionnels")
    st.write("Modifie tes cibles puis sauvegarde-les pour les retrouver automatiquement au prochain lancement.")

    with st.form("targets_form"):
        st.markdown("### Macros")
        macro_columns = st.columns(2)
        for index, (nutrient_name, config) in enumerate(MACRO_CONFIG.items()):
            with macro_columns[index % 2]:
                st.session_state.target_inputs[nutrient_name] = st.number_input(
                    f"{config['label']} ({config['unit']})",
                    min_value=0.0,
                    value=float(st.session_state.target_inputs[nutrient_name]),
                    step=10.0,
                )

        st.markdown("### Micros")
        micro_columns = st.columns(2)
        for index, (nutrient_name, config) in enumerate(MICRO_CONFIG.items()):
            with micro_columns[index % 2]:
                step = 0.5 if config["unit"] in {"mg", "µg", "µg ÉRA"} else 1.0
                st.session_state.target_inputs[nutrient_name] = st.number_input(
                    f"{config['label']} ({config['unit']})",
                    min_value=0.0,
                    value=float(st.session_state.target_inputs[nutrient_name]),
                    step=step,
                )

        save_col, reset_col = st.columns(2)
        save_submitted = save_col.form_submit_button("Sauvegarder les objectifs", type="primary")
        reset_submitted = reset_col.form_submit_button("Réinitialiser aux valeurs par défaut")

    if save_submitted:
        new_targets = {
            "macros": {name: float(st.session_state.target_inputs[name]) for name in MACRO_CONFIG},
            "micros": {name: float(st.session_state.target_inputs[name]) for name in MICRO_CONFIG},
        }
        save_targets(new_targets)
        st.session_state.targets = new_targets
        st.success("Les objectifs ont été sauvegardés.")

    if reset_submitted:
        reset_targets = deepcopy(DEFAULT_TARGETS)
        save_targets(reset_targets)
        st.session_state.targets = reset_targets
        for group_name, config in NUTRIENT_GROUPS.items():
            for nutrient_name in config:
                st.session_state.target_inputs[nutrient_name] = reset_targets[group_name][nutrient_name]
        st.success("Les objectifs par défaut ont été restaurés.")
        st.rerun()


def render_saved_meals(foods: dict) -> None:
    st.subheader("Repas sauvegardés")
    st.write("Sauvegarde le repas courant dans un fichier JSON ou recharge un repas existant.")

    save_name = st.text_input(
        "Nom du repas",
        value=st.session_state.meal_name,
        placeholder="Exemple : Petit dej",
    )
    st.session_state.meal_name = save_name

    if st.button("Sauvegarder ce repas", type="primary"):
        if not save_name.strip():
            st.error("Donne un nom au repas avant de le sauvegarder.")
        elif not st.session_state.meal_items:
            st.error("Le repas courant est vide.")
        else:
            meal_path = save_meal(save_name.strip(), st.session_state.meal_items)
            st.success(f"Repas sauvegardé dans {meal_path.name}.")

    meals, meals_error = list_saved_meals()
    if meals_error:
        st.error(meals_error)
        return

    if not meals:
        st.info("Aucun repas sauvegardé pour le moment.")
        return

    meal_options = {
        (
            f"{meal['name']} - {meal['created_at']}"
            if meal["created_at"]
            else meal["name"]
        ): meal
        for meal in meals
    }
    selected_label = st.selectbox("Repas disponibles", options=list(meal_options.keys()))
    selected_meal = meal_options[selected_label]

    if selected_meal["invalid"]:
        st.warning("Ce fichier de repas est invalide et ne peut pas être chargé.")
        return

    st.caption(f"Fichier : {selected_meal['path'].name}")

    if st.button("Charger ce repas"):
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
            st.warning(
                "Le repas a été chargé partiellement. Aliments absents de `food.json` : "
                + ", ".join(missing_foods)
            )
        else:
            st.success("Repas chargé dans l'éditeur.")
        st.rerun()


def initialize_state(targets: dict) -> None:
    if "targets" not in st.session_state:
        st.session_state.targets = deepcopy(targets)
    if "meal_items" not in st.session_state:
        st.session_state.meal_items = {}
    if "meal_name" not in st.session_state:
        st.session_state.meal_name = ""
    if "target_inputs" not in st.session_state:
        st.session_state.target_inputs = {}
        for group_name, config in NUTRIENT_GROUPS.items():
            for nutrient_name in config:
                st.session_state.target_inputs[nutrient_name] = st.session_state.targets[group_name][nutrient_name]


def main() -> None:
    inject_styles()
    ensure_storage()

    foods, foods_error = load_foods()
    targets, targets_error = load_targets()

    initialize_state(targets)
    st.session_state.targets = deepcopy(targets)

    st.title("Nutri Stacker")
    st.write(
        "Construis un repas, compare tes apports à tes objectifs et sauvegarde facilement "
        "tes cibles comme tes repas."
    )

    if foods_error:
        st.error(foods_error)
        st.stop()
    if targets_error:
        st.warning(targets_error)

    tab_meal, tab_targets, tab_saved_meals = st.tabs(["Repas", "Objectifs", "Repas sauvegardés"])

    with tab_meal:
        render_meal_builder(foods, st.session_state.targets)

    with tab_targets:
        render_targets_editor(st.session_state.targets)

    with tab_saved_meals:
        render_saved_meals(foods)


if __name__ == "__main__":
    main()
