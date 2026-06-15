from pathlib import Path


APP_DIR = Path(__file__).resolve().parent.parent
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
