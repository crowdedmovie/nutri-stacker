import json
import math
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
    "Zinc": {"label": "Zinc", "unit": "mg"},
    "Bore": {"label": "Bore", "unit": "mg"},
    "Cholesterol": {"label": "Cholestérol", "unit": "mg"},
    "Sodium": {"label": "Sodium", "unit": "mg"},
    "Calcium": {"label": "Calcium", "unit": "mg"},
    "Iode": {"label": "Iode", "unit": "µg"},
    "Omega3": {"label": "Oméga-3", "unit": "mg"},
    "Potassium": {"label": "Potassium", "unit": "mg"},
    "Selenium": {"label": "Sélénium", "unit": "µg"},
    "VitamineA": {"label": "Vitamine A", "unit": "µg ÉRA"},
    "VitamineE": {"label": "Vitamine E", "unit": "mg"},
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
        "Zinc": 11.0,
        "Bore": 4.5,
        "Cholesterol": 850.0,
        "Sodium": 3000.0,
        "Calcium": 1000.0,
        "Iode": 175.0,
        "Omega3": 2500.0,
        "Potassium": 4350.0,
        "Selenium": 112.5,
        "VitamineA": 900.0,
        "VitamineE": 15.0,
        "VitamineC": 350.0,
    },
    "calculator_profile": {
        "sex": "homme",
        "age": 30,
        "height_cm": 175.0,
        "weight_kg": 75.0,
        "body_fat_mode": "unknown",
        "body_fat_pct": 15.0,
        "neck_cm": 38.0,
        "waist_cm": 85.0,
        "hip_cm": 100.0,
        "lifestyle_activity": "sedentaire",
        "walk_km": 0.0,
        "run_km": 0.0,
        "strength_minutes": 0.0,
        "strength_intensity": "moderee",
        "goal_mode": "maintien",
    },
}

NUTRIENT_GROUPS = {
    "macros": MACRO_CONFIG,
    "micros": MICRO_CONFIG,
}

ACTIVITY_LABELS = {
    "sedentaire": "Sédentaire hors exercice",
    "leger": "Léger hors exercice",
    "modere": "Modéré hors exercice",
    "eleve": "Élevé hors exercice",
}

ACTIVITY_FACTORS = {
    "sedentaire": 1.2,
    "leger": 1.3,
    "modere": 1.4,
    "eleve": 1.5,
}

ACTIVITY_DESCRIPTIONS = {
    "sedentaire": "Travail assis, peu de déplacements, peu de marche quotidienne, pas de manutention.",
    "leger": "Un peu de marche et de station debout dans la journée, mais mode de vie globalement calme.",
    "modere": "Déplacements fréquents, plusieurs heures debout, activité quotidienne clairement active hors entraînement.",
    "eleve": "Métier physique ou gros volume de déplacements quotidiens, même sans compter le sport saisi plus bas.",
}

STRENGTH_INTENSITIES = {
    "legere": {"label": "Musculation légère", "met": 3.5},
    "moderee": {"label": "Musculation modérée", "met": 5.0},
    "intense": {"label": "Musculation intense", "met": 6.0},
}

GOAL_MODES = {
    "cut_leger": {"label": "Cut léger", "adjustment": -0.10, "protein_factor": 2.0, "fat_factor": 0.8},
    "cut_standard": {"label": "Cut standard", "adjustment": -0.15, "protein_factor": 2.2, "fat_factor": 0.8},
    "cut_agressif": {"label": "Cut agressif", "adjustment": -0.20, "protein_factor": 2.3, "fat_factor": 0.75},
    "maintien": {"label": "Maintien", "adjustment": 0.0, "protein_factor": 1.8, "fat_factor": 0.8},
    "bulk_lean": {"label": "Bulk lean", "adjustment": 0.05, "protein_factor": 1.8, "fat_factor": 0.85},
    "bulk_standard": {"label": "Bulk standard", "adjustment": 0.10, "protein_factor": 1.8, "fat_factor": 0.9},
}


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

    profile = raw_targets.get("calculator_profile", {})
    default_profile = DEFAULT_TARGETS["calculator_profile"]
    if isinstance(profile, dict):
        for field_name, default_value in default_profile.items():
            value = profile.get(field_name, default_value)
            if isinstance(default_value, str):
                normalized["calculator_profile"][field_name] = value if isinstance(value, str) else default_value
            elif isinstance(default_value, int):
                normalized["calculator_profile"][field_name] = int(value) if isinstance(value, (int, float)) else default_value
            elif isinstance(default_value, float):
                normalized["calculator_profile"][field_name] = float(value) if isinstance(value, (int, float)) else default_value

    if normalized["calculator_profile"]["sex"] not in {"homme", "femme"}:
        normalized["calculator_profile"]["sex"] = default_profile["sex"]
    if normalized["calculator_profile"]["body_fat_mode"] not in {"unknown", "known", "estimate_navy"}:
        normalized["calculator_profile"]["body_fat_mode"] = default_profile["body_fat_mode"]
    if normalized["calculator_profile"]["lifestyle_activity"] not in ACTIVITY_FACTORS:
        normalized["calculator_profile"]["lifestyle_activity"] = default_profile["lifestyle_activity"]
    if normalized["calculator_profile"]["strength_intensity"] not in STRENGTH_INTENSITIES:
        normalized["calculator_profile"]["strength_intensity"] = default_profile["strength_intensity"]
    if normalized["calculator_profile"]["goal_mode"] not in GOAL_MODES:
        normalized["calculator_profile"]["goal_mode"] = default_profile["goal_mode"]

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


def calculate_body_fat_navy(profile: dict) -> tuple[float | None, str | None]:
    height_cm = profile["height_cm"]
    neck_cm = profile["neck_cm"]
    waist_cm = profile["waist_cm"]
    hip_cm = profile["hip_cm"]

    if height_cm <= 0 or neck_cm <= 0 or waist_cm <= 0:
        return None, "Les mensurations de taille, cou et taille abdominale doivent être positives."

    try:
        if profile["sex"] == "homme":
            difference = waist_cm - neck_cm
            if difference <= 0:
                return None, "Le tour de taille doit être supérieur au tour de cou pour estimer la masse grasse."
            body_fat = 495 / (
                1.0324 - 0.19077 * math.log10(difference) + 0.15456 * math.log10(height_cm)
            ) - 450
        else:
            difference = waist_cm + hip_cm - neck_cm
            if hip_cm <= 0 or difference <= 0:
                return None, "Les tours de taille, hanches et cou doivent permettre une estimation valide."
            body_fat = 495 / (
                1.29579 - 0.35004 * math.log10(difference) + 0.22100 * math.log10(height_cm)
            ) - 450
    except ValueError:
        return None, "Les mensurations fournies ne permettent pas de calculer la masse grasse."

    return max(2.0, min(body_fat, 60.0)), None


def calculate_mifflin_st_jeor(profile: dict) -> float:
    sex_offset = 5 if profile["sex"] == "homme" else -161
    return (
        10 * profile["weight_kg"]
        + 6.25 * profile["height_cm"]
        - 5 * profile["age"]
        + sex_offset
    )


def calculate_schofield(profile: dict) -> float:
    age = profile["age"]
    weight = profile["weight_kg"]
    sex = profile["sex"]

    if sex == "homme":
        if age < 18:
            return 17.686 * weight + 658.2
        if age < 30:
            return 15.057 * weight + 692.2
        if age < 60:
            return 11.472 * weight + 873.1
        return 11.711 * weight + 587.7

    if age < 18:
        return 13.384 * weight + 692.6
    if age < 30:
        return 14.818 * weight + 486.6
    if age < 60:
        return 8.126 * weight + 845.6
    return 9.082 * weight + 658.5


def calculate_cunningham(profile: dict, body_fat_pct: float) -> float:
    lean_mass = profile["weight_kg"] * (1 - body_fat_pct / 100)
    return 500 + 22 * lean_mass


def round_to_step(value: float, step: int) -> float:
    return round(value / step) * step


def calculate_recommended_targets(profile: dict) -> dict:
    body_fat_pct = None
    body_fat_error = None
    if profile["body_fat_mode"] == "known":
        body_fat_pct = profile["body_fat_pct"]
    elif profile["body_fat_mode"] == "estimate_navy":
        body_fat_pct, body_fat_error = calculate_body_fat_navy(profile)

    ree_methods = {
        "Mifflin-St Jeor": calculate_mifflin_st_jeor(profile),
        "Schofield": calculate_schofield(profile),
    }
    if body_fat_pct is not None:
        ree_methods["Cunningham"] = calculate_cunningham(profile, body_fat_pct)

    if "Cunningham" in ree_methods:
        weighted_ree = (
            0.50 * ree_methods["Cunningham"]
            + 0.35 * ree_methods["Mifflin-St Jeor"]
            + 0.15 * ree_methods["Schofield"]
        )
    else:
        weighted_ree = 0.60 * ree_methods["Mifflin-St Jeor"] + 0.40 * ree_methods["Schofield"]

    activity_factor = ACTIVITY_FACTORS[profile["lifestyle_activity"]]
    neat_kcal = weighted_ree * (activity_factor - 1.0)
    base_tdee = weighted_ree + neat_kcal

    walk_kcal = profile["weight_kg"] * profile["walk_km"] * 0.55
    run_kcal = profile["weight_kg"] * profile["run_km"] * 1.0
    strength_met = STRENGTH_INTENSITIES[profile["strength_intensity"]]["met"]
    strength_hours = profile["strength_minutes"] / 60
    strength_kcal = max(strength_met - 1.0, 0.0) * profile["weight_kg"] * strength_hours
    exercise_kcal = walk_kcal + run_kcal + strength_kcal
    maintenance_kcal = base_tdee + exercise_kcal

    goal_config = GOAL_MODES[profile["goal_mode"]]
    target_calories = maintenance_kcal * (1 + goal_config["adjustment"])

    protein_g = profile["weight_kg"] * goal_config["protein_factor"]
    fat_g = profile["weight_kg"] * goal_config["fat_factor"]
    minimum_fat_g = profile["weight_kg"] * 0.6

    remaining_kcal = target_calories - protein_g * 4 - fat_g * 9
    if remaining_kcal < 0:
        fat_g = max(minimum_fat_g, (target_calories - protein_g * 4) / 9)
        remaining_kcal = target_calories - protein_g * 4 - fat_g * 9
    if remaining_kcal < 0:
        protein_g = max(profile["weight_kg"] * 1.6, (target_calories - fat_g * 9) / 4)
        remaining_kcal = target_calories - protein_g * 4 - fat_g * 9
    carbs_g = max(remaining_kcal / 4, 0.0)

    walk_hours = profile["walk_km"] / 5 if profile["walk_km"] > 0 else 0.0
    run_hours = profile["run_km"] / 9 if profile["run_km"] > 0 else 0.0
    sodium_bonus = round_to_step(100 * walk_hours + 300 * run_hours + 250 * strength_hours, 50)
    potassium_bonus = round_to_step(40 * walk_hours + 100 * run_hours + 80 * strength_hours, 10)
    magnesium_bonus = round_to_step(3 * walk_hours + 10 * run_hours + 10 * strength_hours, 1)

    recommended_micros = deepcopy(DEFAULT_TARGETS["micros"])
    recommended_micros["Sodium"] += sodium_bonus
    recommended_micros["Potassium"] += potassium_bonus
    recommended_micros["Magnesium"] += magnesium_bonus

    return {
        "body_fat_pct": body_fat_pct,
        "body_fat_error": body_fat_error,
        "ree_methods": ree_methods,
        "weighted_ree": weighted_ree,
        "activity_factor": activity_factor,
        "neat_kcal": neat_kcal,
        "base_tdee": base_tdee,
        "exercise_kcal": {
            "walk": walk_kcal,
            "run": run_kcal,
            "strength": strength_kcal,
            "total": exercise_kcal,
        },
        "maintenance_kcal": maintenance_kcal,
        "goal_adjustment": goal_config["adjustment"],
        "target_macros": {
            "Calories": target_calories,
            "Proteines": protein_g,
            "Glucides": carbs_g,
            "Lipides": fat_g,
        },
        "target_micros": recommended_micros,
    }


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


def push_notice(message: str, scope: str, kind: str = "success") -> None:
    st.session_state.notice = {"message": message, "kind": kind, "scope": scope}


def render_notice(scope: str) -> None:
    notice = st.session_state.get("notice")
    if not notice:
        return
    if notice.get("scope") != scope:
        return

    message_col, close_col = st.columns([0.95, 0.05], vertical_alignment="center")
    with message_col:
        if notice["kind"] == "success":
            st.success(notice["message"])
        elif notice["kind"] == "warning":
            st.warning(notice["message"])
        else:
            st.info(notice["message"])
    with close_col:
        if st.button("✕", key=f"close_notice_{scope}", help="Fermer ce message"):
            st.session_state.notice = None
            st.rerun()


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


def apply_recommended_targets(recommendation: dict) -> None:
    for nutrient_name, value in recommendation["target_macros"].items():
        st.session_state.target_inputs[nutrient_name] = float(value)
        st.session_state[f"target_{nutrient_name}"] = float(value)
    for nutrient_name, value in recommendation["target_micros"].items():
        st.session_state.target_inputs[nutrient_name] = float(value)
        st.session_state[f"target_{nutrient_name}"] = float(value)

    st.session_state.targets["macros"] = {
        name: float(st.session_state.target_inputs[name]) for name in MACRO_CONFIG
    }
    st.session_state.targets["micros"] = {
        name: float(st.session_state.target_inputs[name]) for name in MICRO_CONFIG
    }


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


def render_energy_calculator() -> dict:
    st.markdown("### Calculateur de besoins journaliers")
    st.caption(
        "Le calcul combine Mifflin-St Jeor et Schofield, et ajoute Cunningham si la masse grasse "
        "est connue ou estimée. Le niveau d'activité ici représente la vie quotidienne hors entraînement."
    )
    st.info(
        "Info méthodologique : utilise les bulles d'aide des champs et le panneau 'Détail des méthodes de calcul' "
        "pour voir les formules, hypothèses et limites du modèle."
    )

    profile_col, activity_col = st.columns(2, gap="large")

    with profile_col:
        st.markdown("#### Profil")
        st.radio(
            "Sexe",
            options=["homme", "femme"],
            format_func=lambda value: "Homme" if value == "homme" else "Femme",
            key="calc_sex",
            horizontal=True,
            help="Utilisé dans les équations de Mifflin-St Jeor, Schofield et dans la version homme/femme de la formule U.S. Navy.",
        )
        st.number_input(
            "Âge",
            min_value=15,
            max_value=90,
            step=1,
            key="calc_age",
            help="Intervient directement dans Mifflin-St Jeor et Schofield.",
        )
        st.number_input(
            "Taille (cm)",
            min_value=120.0,
            max_value=230.0,
            step=1.0,
            key="calc_height_cm",
            help="Utilisée pour Mifflin-St Jeor et, si besoin, pour la formule U.S. Navy.",
        )
        st.number_input(
            "Poids (kg)",
            min_value=35.0,
            max_value=250.0,
            step=0.1,
            key="calc_weight_kg",
            help="Utilisé dans toutes les équations de dépense et dans les estimations de marche, course et musculation.",
        )

        body_fat_mode = st.radio(
            "Masse grasse",
            options=["unknown", "known", "estimate_navy"],
            format_func=lambda value: {
                "unknown": "Je ne la renseigne pas",
                "known": "Je connais mon taux",
                "estimate_navy": "L'app l'estime (formule U.S. Navy)",
            }[value],
            key="calc_body_fat_mode",
            help=(
                "Si la masse grasse est connue ou estimée, l'app active Cunningham en plus de Mifflin-St Jeor "
                "et Schofield pour mieux représenter la masse maigre."
            ),
        )
        if body_fat_mode == "known":
            st.number_input(
                "Taux de masse grasse (%)",
                min_value=2.0,
                max_value=60.0,
                step=0.1,
                key="calc_body_fat_pct",
                help="Valeur saisie manuellement. Elle est utilisée pour calculer la masse maigre puis l'équation de Cunningham.",
            )
        elif body_fat_mode == "estimate_navy":
            st.number_input(
                "Tour de cou (cm)",
                min_value=20.0,
                max_value=70.0,
                step=0.1,
                key="calc_neck_cm",
                help="Mesure au niveau du cou, utilisée dans la formule U.S. Navy.",
            )
            st.number_input(
                "Tour de taille abdominale (cm)",
                min_value=40.0,
                max_value=200.0,
                step=0.1,
                key="calc_waist_cm",
                help="Mesure au niveau abdominal. Pour l'estimation U.S. Navy, elle doit rester supérieure au tour de cou chez l'homme.",
            )
            if st.session_state.calc_sex == "femme":
                st.number_input(
                    "Tour de hanches (cm)",
                    min_value=50.0,
                    max_value=220.0,
                    step=0.1,
                    key="calc_hip_cm",
                    help="Ajouté uniquement pour la version femme de la formule U.S. Navy.",
                )
            st.caption("Estimation pratique, utile pour affiner les calories mais moins fiable chez les profils atypiques.")

    with activity_col:
        st.markdown("#### Activité et objectif")
        st.selectbox(
            "Activité quotidienne hors exercice",
            options=list(ACTIVITY_FACTORS.keys()),
            format_func=lambda value: ACTIVITY_LABELS[value],
            key="calc_lifestyle_activity",
            help=(
                "Cette valeur décrit ton mode de vie quotidien hors marche sportive, hors course et hors musculation. "
                "Elle sert à estimer ton NEAT sans double compter les activités saisies plus bas."
            ),
        )
        st.caption(ACTIVITY_DESCRIPTIONS[st.session_state.calc_lifestyle_activity])
        st.info(
            "Renseigne ci-dessous uniquement l'activité additionnelle non déjà représentée par ton mode de vie quotidien."
        )
        st.number_input(
            "Marche additionnelle (km)",
            min_value=0.0,
            max_value=60.0,
            step=0.5,
            key="calc_walk_km",
            help="Exemples : balade, tapis, randonnée, long trajet à pied inhabituel. Ne pas inclure la marche déjà normale de ta journée.",
        )
        st.number_input(
            "Course du jour (km)",
            min_value=0.0,
            max_value=60.0,
            step=0.5,
            key="calc_run_km",
            help="Estimée ici à environ 1.0 kcal par kg de poids corporel et par km couru.",
        )
        st.number_input(
            "Musculation du jour (minutes)",
            min_value=0.0,
            max_value=300.0,
            step=5.0,
            key="calc_strength_minutes",
            help="Convertie en dépense via un MET d'intensité, moins 1 MET de repos déjà couvert par le métabolisme de base.",
        )
        st.selectbox(
            "Intensité de musculation",
            options=list(STRENGTH_INTENSITIES.keys()),
            format_func=lambda value: STRENGTH_INTENSITIES[value]["label"],
            key="calc_strength_intensity",
            help="MET utilisé : léger 3.5, modéré 5.0, intense 6.0.",
        )
        st.selectbox(
            "Objectif nutritionnel",
            options=list(GOAL_MODES.keys()),
            format_func=lambda value: GOAL_MODES[value]["label"],
            key="calc_goal_mode",
            help="Applique un ajustement calorique relatif au maintien, puis propose des macros cohérentes avec cet objectif.",
        )

    update_profile_from_inputs()
    recommendation = calculate_recommended_targets(st.session_state.targets["calculator_profile"])

    if recommendation["body_fat_error"]:
        st.warning(recommendation["body_fat_error"])

    summary_columns = st.columns(4)
    summary_columns[0].metric("Métabolisme estimé", f"{format_number(recommendation['weighted_ree'])} kcal")
    summary_columns[1].metric("Maintien estimé", f"{format_number(recommendation['maintenance_kcal'])} kcal")
    summary_columns[2].metric(
        "Objectif calories",
        f"{format_number(recommendation['target_macros']['Calories'])} kcal",
    )
    if recommendation["body_fat_pct"] is not None:
        summary_columns[3].metric("Masse grasse estimée", f"{recommendation['body_fat_pct']:.1f}%")
    else:
        summary_columns[3].metric("Masse grasse", "Non utilisée")

    with st.expander("Détail des méthodes de calcul"):
        st.markdown("**Équations de base**")
        st.write(
            "Mifflin-St Jeor : `10 x poids(kg) + 6.25 x taille(cm) - 5 x âge + s` "
            "avec `s = +5` pour un homme et `-161` pour une femme."
        )
        st.write("Schofield : équation par sexe et tranche d'âge, basée principalement sur le poids corporel.")
        st.write("Cunningham : `500 + 22 x masse maigre(kg)` avec `masse maigre = poids x (1 - masse grasse)`.")
        st.markdown("**Pondération utilisée**")
        st.write(
            "Sans masse grasse : `60% Mifflin-St Jeor + 40% Schofield`."
        )
        st.write(
            "Avec masse grasse connue ou estimée : `50% Cunningham + 35% Mifflin-St Jeor + 15% Schofield`."
        )
        st.markdown("**Formule U.S. Navy pour la masse grasse**")
        st.write(
            "Homme : `%MG = 495 / (1.0324 - 0.19077 x log10(taille_abdo - cou) + 0.15456 x log10(taille)) - 450`."
        )
        st.write(
            "Femme : `%MG = 495 / (1.29579 - 0.35004 x log10(taille_abdo + hanches - cou) + 0.22100 x log10(taille)) - 450`."
        )
        st.markdown("**Activité quotidienne et exercice**")
        st.write(
            "Le facteur d'activité quotidienne représente le NEAT hors exercice structuré. "
            "L'app ajoute ensuite séparément la marche additionnelle, la course et la musculation pour limiter le double comptage."
        )
        st.write(
            "Marche additionnelle : environ `0.55 kcal x poids(kg) x km`."
        )
        st.write(
            "Course : environ `1.0 kcal x poids(kg) x km`."
        )
        st.write(
            "Musculation : `(MET - 1) x poids(kg) x durée(h)` avec MET = 3.5, 5.0 ou 6.0 selon l'intensité."
        )
        st.markdown("**Objectif et macros**")
        st.write(
            "Les modes cut / maintien / bulk appliquent un pourcentage autour du maintien, puis fixent les protéines "
            "et lipides par kg de poids corporel. Les glucides récupèrent les calories restantes."
        )
        st.markdown("**Limites**")
        st.write(
            "Les résultats restent des estimations. Ils sont utiles pour cadrer une cible initiale, mais doivent idéalement "
            "être ajustés ensuite selon l'évolution du poids, des performances, de la faim et de la récupération."
        )
        for method_name, value in recommendation["ree_methods"].items():
            st.write(f"{method_name} : {format_number(value)} kcal")
        st.write(f"Facteur d'activité quotidienne hors exercice : {recommendation['activity_factor']:.2f}")
        st.write(f"Calories NEAT estimées : {format_number(recommendation['neat_kcal'])} kcal")
        st.write(
            "Calories d'exercice ajoutées : "
            f"marche {format_number(recommendation['exercise_kcal']['walk'])} kcal, "
            f"course {format_number(recommendation['exercise_kcal']['run'])} kcal, "
            f"musculation {format_number(recommendation['exercise_kcal']['strength'])} kcal."
        )

    st.markdown("#### Recommandation automatique")
    recommendation_columns = st.columns(4)
    for column, nutrient_name in zip(recommendation_columns, MACRO_CONFIG):
        config = MACRO_CONFIG[nutrient_name]
        column.metric(
            config["label"],
            f"{format_number(recommendation['target_macros'][nutrient_name])} {config['unit']}",
        )

    st.caption(
        "Les micronutriments sont conservateurs : l'app garde la base actuelle et ajuste surtout sodium, "
        "potassium et magnésium selon l'activité du jour."
    )

    render_notice("targets_reco")
    if st.button("Appliquer les recommandations calculées"):
        apply_recommended_targets(recommendation)
        push_notice("Les cibles calculées ont été injectées dans les objectifs ci-dessous.", "targets_reco")
        st.rerun()

    return recommendation


def render_targets_editor(targets: dict) -> None:
    st.subheader("Objectifs nutritionnels")
    st.write(
        "Calcule une base personnalisée pour tes calories et macros, puis ajuste librement les cibles "
        "avant de les sauvegarder."
    )

    render_energy_calculator()

    st.markdown("### Objectifs éditables")
    macro_columns = st.columns(2)
    for index, (nutrient_name, config) in enumerate(MACRO_CONFIG.items()):
        with macro_columns[index % 2]:
            st.session_state.target_inputs[nutrient_name] = st.number_input(
                f"{config['label']} ({config['unit']})",
                min_value=0.0,
                step=10.0,
                key=f"target_{nutrient_name}",
            )

    st.markdown("### Micronutriments")
    micro_columns = st.columns(2)
    for index, (nutrient_name, config) in enumerate(MICRO_CONFIG.items()):
        with micro_columns[index % 2]:
            step = 0.5 if config["unit"] in {"mg", "µg", "µg ÉRA"} else 1.0
            st.session_state.target_inputs[nutrient_name] = st.number_input(
                f"{config['label']} ({config['unit']})",
                min_value=0.0,
                step=step,
                key=f"target_{nutrient_name}",
            )

    save_col, reset_col = st.columns(2)
    render_notice("targets_actions")

    if save_col.button("Sauvegarder les objectifs", type="primary"):
        update_profile_from_inputs()
        new_targets = {
            "macros": {name: float(st.session_state.target_inputs[name]) for name in MACRO_CONFIG},
            "micros": {name: float(st.session_state.target_inputs[name]) for name in MICRO_CONFIG},
            "calculator_profile": deepcopy(st.session_state.targets["calculator_profile"]),
        }
        save_targets(new_targets)
        st.session_state.targets = deepcopy(new_targets)
        push_notice("Les objectifs ont été sauvegardés.", "targets_actions")
        st.rerun()

    if reset_col.button("Réinitialiser aux valeurs par défaut"):
        reset_targets = deepcopy(DEFAULT_TARGETS)
        save_targets(reset_targets)
        st.session_state.targets = deepcopy(reset_targets)
        for group_name, config in NUTRIENT_GROUPS.items():
            for nutrient_name in config:
                st.session_state.target_inputs[nutrient_name] = reset_targets[group_name][nutrient_name]
                st.session_state[f"target_{nutrient_name}"] = reset_targets[group_name][nutrient_name]
        for field_name, value in reset_targets["calculator_profile"].items():
            st.session_state[f"calc_{field_name}"] = value
        push_notice("Les objectifs par défaut ont été restaurés.", "targets_actions")
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

    render_notice("saved_meal_save")
    if st.button("Sauvegarder ce repas", type="primary"):
        if not save_name.strip():
            st.error("Donne un nom au repas avant de le sauvegarder.")
        elif not st.session_state.meal_items:
            st.error("Le repas courant est vide.")
        else:
            meal_path = save_meal(save_name.strip(), st.session_state.meal_items)
            push_notice(f"Repas sauvegardé dans {meal_path.name}.", "saved_meal_save")
            st.rerun()

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

    render_notice("saved_meal_load")
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
            push_notice(
                f"Repas '{selected_meal['name']}' chargé partiellement. Aliments absents de `food.json` : "
                + ", ".join(missing_foods),
                "saved_meal_load",
                kind="warning",
            )
        else:
            push_notice(f"Repas chargé : {selected_meal['name']}.", "saved_meal_load")
        st.rerun()


def initialize_state(targets: dict) -> None:
    if "targets" not in st.session_state:
        st.session_state.targets = deepcopy(targets)
    if "meal_items" not in st.session_state:
        st.session_state.meal_items = {}
    if "meal_name" not in st.session_state:
        st.session_state.meal_name = ""
    if "notice" not in st.session_state:
        st.session_state.notice = None
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


def main() -> None:
    inject_styles()
    ensure_storage()

    foods, foods_error = load_foods()
    targets, targets_error = load_targets()

    initialize_state(targets)

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
