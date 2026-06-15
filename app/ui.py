from copy import deepcopy

import streamlit as st

from app.calculations import (
    calculate_recommended_targets,
    calculate_totals,
    get_default_quantity,
    sync_selected_foods,
)
from app.config import (
    ACTIVITY_DESCRIPTIONS,
    ACTIVITY_FACTORS,
    ACTIVITY_LABELS,
    DEFAULT_TARGETS,
    GOAL_MODES,
    MACRO_CONFIG,
    MICRO_CONFIG,
    NUTRIENT_GROUPS,
    STRENGTH_INTENSITIES,
)
from app.storage import list_saved_meals, load_meal_file, save_meal, save_targets


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
        st.number_input("Âge", min_value=15, max_value=90, step=1, key="calc_age", help="Intervient directement dans Mifflin-St Jeor et Schofield.")
        st.number_input("Taille (cm)", min_value=120.0, max_value=230.0, step=1.0, key="calc_height_cm", help="Utilisée pour Mifflin-St Jeor et, si besoin, pour la formule U.S. Navy.")
        st.number_input("Poids (kg)", min_value=35.0, max_value=250.0, step=0.1, key="calc_weight_kg", help="Utilisé dans toutes les équations de dépense et dans les estimations de marche, course et musculation.")

        body_fat_mode = st.radio(
            "Masse grasse",
            options=["unknown", "known", "estimate_navy"],
            format_func=lambda value: {
                "unknown": "Je ne la renseigne pas",
                "known": "Je connais mon taux",
                "estimate_navy": "L'app l'estime (formule U.S. Navy)",
            }[value],
            key="calc_body_fat_mode",
            help="Si la masse grasse est connue ou estimée, l'app active Cunningham en plus de Mifflin-St Jeor et Schofield pour mieux représenter la masse maigre.",
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
            st.number_input("Tour de cou (cm)", min_value=20.0, max_value=70.0, step=0.1, key="calc_neck_cm", help="Mesure au niveau du cou, utilisée dans la formule U.S. Navy.")
            st.number_input("Tour de taille abdominale (cm)", min_value=40.0, max_value=200.0, step=0.1, key="calc_waist_cm", help="Mesure au niveau abdominal. Pour l'estimation U.S. Navy, elle doit rester supérieure au tour de cou chez l'homme.")
            if st.session_state.calc_sex == "femme":
                st.number_input("Tour de hanches (cm)", min_value=50.0, max_value=220.0, step=0.1, key="calc_hip_cm", help="Ajouté uniquement pour la version femme de la formule U.S. Navy.")
            st.caption("Estimation pratique, utile pour affiner les calories mais moins fiable chez les profils atypiques.")

    with activity_col:
        st.markdown("#### Activité et objectif")
        st.selectbox(
            "Activité quotidienne hors exercice",
            options=list(ACTIVITY_FACTORS.keys()),
            format_func=lambda value: ACTIVITY_LABELS[value],
            key="calc_lifestyle_activity",
            help="Cette valeur décrit ton mode de vie quotidien hors marche sportive, hors course et hors musculation. Elle sert à estimer ton NEAT sans double compter les activités saisies plus bas.",
        )
        st.caption(ACTIVITY_DESCRIPTIONS[st.session_state.calc_lifestyle_activity])
        st.info("Renseigne ci-dessous uniquement l'activité additionnelle non déjà représentée par ton mode de vie quotidien.")
        st.number_input("Marche additionnelle (km)", min_value=0.0, max_value=60.0, step=0.5, key="calc_walk_km", help="Exemples : balade, tapis, randonnée, long trajet à pied inhabituel. Ne pas inclure la marche déjà normale de ta journée.")
        st.number_input("Course du jour (km)", min_value=0.0, max_value=60.0, step=0.5, key="calc_run_km", help="Estimée ici à environ 1.0 kcal par kg de poids corporel et par km couru.")
        st.number_input("Musculation du jour (minutes)", min_value=0.0, max_value=300.0, step=5.0, key="calc_strength_minutes", help="Convertie en dépense via un MET d'intensité, moins 1 MET de repos déjà couvert par le métabolisme de base.")
        st.selectbox("Intensité de musculation", options=list(STRENGTH_INTENSITIES.keys()), format_func=lambda value: STRENGTH_INTENSITIES[value]["label"], key="calc_strength_intensity", help="MET utilisé : léger 3.5, modéré 5.0, intense 6.0.")
        st.selectbox("Objectif nutritionnel", options=list(GOAL_MODES.keys()), format_func=lambda value: GOAL_MODES[value]["label"], key="calc_goal_mode", help="Applique un ajustement calorique relatif au maintien, puis propose des macros cohérentes avec cet objectif.")

    update_profile_from_inputs()
    recommendation = calculate_recommended_targets(st.session_state.targets["calculator_profile"])

    if recommendation["body_fat_error"]:
        st.warning(recommendation["body_fat_error"])

    summary_columns = st.columns(4)
    summary_columns[0].metric("Métabolisme estimé", f"{format_number(recommendation['weighted_ree'])} kcal")
    summary_columns[1].metric("Maintien estimé", f"{format_number(recommendation['maintenance_kcal'])} kcal")
    summary_columns[2].metric("Objectif calories", f"{format_number(recommendation['target_macros']['Calories'])} kcal")
    if recommendation["body_fat_pct"] is not None:
        summary_columns[3].metric("Masse grasse estimée", f"{recommendation['body_fat_pct']:.1f}%")
    else:
        summary_columns[3].metric("Masse grasse", "Non utilisée")

    with st.expander("Détail des méthodes de calcul"):
        st.markdown("**Équations de base**")
        st.write("Mifflin-St Jeor : `10 x poids(kg) + 6.25 x taille(cm) - 5 x âge + s` avec `s = +5` pour un homme et `-161` pour une femme.")
        st.write("Schofield : équation par sexe et tranche d'âge, basée principalement sur le poids corporel.")
        st.write("Cunningham : `500 + 22 x masse maigre(kg)` avec `masse maigre = poids x (1 - masse grasse)`.")
        st.markdown("**Pondération utilisée**")
        st.write("Sans masse grasse : `60% Mifflin-St Jeor + 40% Schofield`.")
        st.write("Avec masse grasse connue ou estimée : `50% Cunningham + 35% Mifflin-St Jeor + 15% Schofield`.")
        st.markdown("**Formule U.S. Navy pour la masse grasse**")
        st.write("Homme : `%MG = 495 / (1.0324 - 0.19077 x log10(taille_abdo - cou) + 0.15456 x log10(taille)) - 450`.")
        st.write("Femme : `%MG = 495 / (1.29579 - 0.35004 x log10(taille_abdo + hanches - cou) + 0.22100 x log10(taille)) - 450`.")
        st.markdown("**Activité quotidienne et exercice**")
        st.write("Le facteur d'activité quotidienne représente le NEAT hors exercice structuré. L'app ajoute ensuite séparément la marche additionnelle, la course et la musculation pour limiter le double comptage.")
        st.write("Marche additionnelle : environ `0.55 kcal x poids(kg) x km`.")
        st.write("Course : environ `1.0 kcal x poids(kg) x km`.")
        st.write("Musculation : `(MET - 1) x poids(kg) x durée(h)` avec MET = 3.5, 5.0 ou 6.0 selon l'intensité.")
        st.markdown("**Objectif et macros**")
        st.write("Les modes cut / maintien / bulk appliquent un pourcentage autour du maintien, puis fixent les protéines et lipides par kg de poids corporel. Les glucides récupèrent les calories restantes.")
        st.markdown("**Limites**")
        st.write("Les résultats restent des estimations. Ils sont utiles pour cadrer une cible initiale, mais doivent idéalement être ajustés ensuite selon l'évolution du poids, des performances, de la faim et de la récupération.")
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
        column.metric(config["label"], f"{format_number(recommendation['target_macros'][nutrient_name])} {config['unit']}")

    st.caption("Les micronutriments sont conservateurs : l'app garde la base actuelle et ajuste surtout sodium, potassium et magnésium selon l'activité du jour.")

    render_notice("targets_reco")
    if st.button("Appliquer les recommandations calculées"):
        apply_recommended_targets(recommendation)
        push_notice("Les cibles calculées ont été injectées dans les objectifs ci-dessous.", "targets_reco")
        st.rerun()

    return recommendation


def render_targets_editor(targets: dict) -> None:
    st.subheader("Objectifs nutritionnels")
    st.write("Calcule une base personnalisée pour tes calories et macros, puis ajuste librement les cibles avant de les sauvegarder.")

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

    save_name = st.text_input("Nom du repas", value=st.session_state.meal_name, placeholder="Exemple : Petit dej")
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
        (f"{meal['name']} - {meal['created_at']}" if meal["created_at"] else meal["name"]): meal
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
                f"Repas '{selected_meal['name']}' chargé partiellement. Aliments absents de `food.json` : " + ", ".join(missing_foods),
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
