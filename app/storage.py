import json
from copy import deepcopy
from datetime import UTC, datetime
from pathlib import Path

from app.config import (
    ACTIVITY_FACTORS,
    DEFAULT_TARGETS,
    FOOD_FILE,
    GOAL_MODES,
    MACRO_CONFIG,
    MEALS_DIR,
    MICRO_CONFIG,
    NUTRIENT_GROUPS,
    STRENGTH_INTENSITIES,
    TARGETS_FILE,
)
from app.calculations import slugify
from app.i18n import t


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

    app_settings = raw_targets.get("app_settings", {})
    default_settings = DEFAULT_TARGETS["app_settings"]
    if isinstance(app_settings, dict) and app_settings.get("language") in {"fr", "en"}:
        normalized["app_settings"]["language"] = app_settings["language"]
    else:
        normalized["app_settings"]["language"] = default_settings["language"]

    return normalized


def load_foods() -> tuple[dict, str | None]:
    try:
        foods = read_json_file(FOOD_FILE)
    except FileNotFoundError:
        return {}, t("error_food_missing")
    except json.JSONDecodeError as error:
        return {}, t("error_food_invalid", error=error)

    if not isinstance(foods, dict):
        return {}, t("error_food_shape")

    required_fields = {"Ref_Qte", "Unite", *MACRO_CONFIG.keys()}
    normalized_foods = {}

    for food_name, values in foods.items():
        if not isinstance(values, dict):
            continue
        missing_fields = required_fields.difference(values.keys())
        if missing_fields:
            return {}, t("error_food_required", food=food_name, fields=", ".join(sorted(missing_fields)))
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
        return normalized, t("targets_invalid_reset", error=error)

    normalized = normalize_targets(raw_targets)
    if normalized != raw_targets:
        write_json_file(TARGETS_FILE, normalized)
        return normalized, t("targets_incomplete_completed")
    return normalized, None


def list_saved_meals() -> tuple[list[dict], str | None]:
    meals = []
    try:
        files = sorted(MEALS_DIR.glob("*.json"))
    except OSError as error:
        return [], t("saved_meals_read_error", error=error)

    for path in files:
        try:
            meal = read_json_file(path)
        except (OSError, json.JSONDecodeError):
            meals.append(
                {
                    "path": path,
                    "name": f"{path.stem} ({t('invalid_file_suffix')})",
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
        return {}, t("meal_missing")
    except json.JSONDecodeError as error:
        return {}, t("meal_invalid", error=error)

    items = meal.get("items", [])
    if not isinstance(items, list):
        return {}, t("meal_items_invalid")

    loaded_items = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        food_name = item.get("food")
        quantity = item.get("quantity")
        if isinstance(food_name, str) and isinstance(quantity, (int, float)):
            loaded_items[food_name] = float(quantity)
    return loaded_items, None
