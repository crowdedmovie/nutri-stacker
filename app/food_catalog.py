"""Pure helpers for searching and sorting the food catalogue."""

from difflib import SequenceMatcher
import math
import re
import unicodedata


SORT_MODES = ("alpha", "asc", "desc")


def normalize_search_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value.casefold())
    without_accents = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", without_accents).strip()


def get_nutrient_value(food_data: dict, nutrient_name: str) -> float | None:
    value = food_data.get(nutrient_name)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    numeric_value = float(value)
    return numeric_value if math.isfinite(numeric_value) else None


def _token_similarity(query_token: str, candidate_tokens: list[str]) -> float:
    best_score = 0.0
    for candidate_token in candidate_tokens:
        if query_token == candidate_token:
            score = 1.0
        elif candidate_token.startswith(query_token):
            score = 0.94
        elif query_token in candidate_token:
            score = 0.86
        else:
            score = SequenceMatcher(None, query_token, candidate_token).ratio()
        best_score = max(best_score, score)
    return best_score


def search_score(query: str, *candidate_names: str) -> float | None:
    normalized_query = normalize_search_text(query)
    if not normalized_query:
        return 1.0

    query_tokens = normalized_query.split()
    best_score = 0.0
    for candidate_name in candidate_names:
        normalized_candidate = normalize_search_text(candidate_name)
        candidate_tokens = normalized_candidate.split()
        if not candidate_tokens:
            continue

        token_scores = [_token_similarity(token, candidate_tokens) for token in query_tokens]
        minimum_score = 0.72 if any(len(token) >= 4 for token in query_tokens) else 0.86
        if all(score >= minimum_score for score in token_scores):
            best_score = max(best_score, sum(token_scores) / len(token_scores))

    return best_score if best_score > 0 else None


def filter_and_sort_foods(
    foods: dict,
    display_names: dict[str, str],
    query: str,
    favorite_foods: set[str],
    favorites_only: bool,
    nutrient_name: str,
    sort_mode: str,
    excluded_foods: set[str] | None = None,
) -> list[str]:
    excluded_foods = excluded_foods or set()
    candidates = []
    for food_name, food_data in foods.items():
        if food_name in excluded_foods:
            continue
        if favorites_only and food_name not in favorite_foods:
            continue

        nutrient_value = get_nutrient_value(food_data, nutrient_name)
        if nutrient_value is None:
            continue

        score = search_score(query, display_names.get(food_name, food_name), food_name)
        if score is None:
            continue

        candidates.append((food_name, nutrient_value, score))

    mode = sort_mode if sort_mode in SORT_MODES else "alpha"
    if mode == "asc":
        candidates.sort(key=lambda item: (item[1], normalize_search_text(display_names.get(item[0], item[0]))))
    elif mode == "desc":
        candidates.sort(key=lambda item: (-item[1], normalize_search_text(display_names.get(item[0], item[0]))))
    else:
        candidates.sort(key=lambda item: normalize_search_text(display_names.get(item[0], item[0])))

    return [food_name for food_name, _, _ in candidates]
