import math
import re
import unicodedata
from copy import deepcopy

import streamlit as st

from app.config import (
    ACTIVITY_FACTORS,
    DEFAULT_TARGETS,
    GOAL_MODES,
    MACRO_CONFIG,
    MICRO_CONFIG,
    STRENGTH_INTENSITIES,
)


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
    return 10 * profile["weight_kg"] + 6.25 * profile["height_cm"] - 5 * profile["age"] + sex_offset


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
        weighted_ree = 0.50 * ree_methods["Cunningham"] + 0.35 * ree_methods["Mifflin-St Jeor"] + 0.15 * ree_methods["Schofield"]
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
