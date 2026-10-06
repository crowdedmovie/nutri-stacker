"""Local component gallery. Does not read or write application storage."""
import streamlit as st

import ui

st.set_page_config(page_title="Nutri Stacker · UI", page_icon="◐", layout="wide")
ui.apply_theme()

with ui.app_shell():
    ui.page_header("Une interface, un langage.", "La bibliothèque de composants Nutri Stacker. Explorez les tailles, les variantes et les états.")
    buttons, inputs, cards = ui.tabs(["Button", "Input & Select", "Card & Layout"])
    with buttons:
        with ui.card(key="gallery-buttons", title="Actions", description="Une action principale par zone. Les actions secondaires restent discrètes."):
            columns = st.columns(4)
            for column, (variant, label) in zip(columns, [("primary", "Continuer"), ("secondary", "Enregistrer"), ("ghost", "Annuler"), ("danger", "Retirer")]):
                with column:
                    if ui.button(label, key=f"gallery-{variant}", variant=variant):
                        st.toast(f"{label} · action reçue")
            for size in ("small", "medium", "large"):
                ui.button(f"Taille {size}", key=f"gallery-size-{size}", size=size)
            ui.button("Indisponible", key="gallery-disabled", disabled=True)
            ui.button("Action sur toute la largeur", key="gallery-stretch", variant="primary", width="stretch")
    with inputs:
        left, right = ui.split_layout(key="gallery-inputs", widths=(1, 1))
        with left, ui.card(key="gallery-fields", title="Input"):
            ui.input("Nom du repas", key="gallery-name", placeholder="Déjeuner", helper="Un nom court pour le retrouver facilement.")
            ui.input("Champ rempli", key="gallery-filled", value="Déjeuner du lundi", variant="solid")
            ui.input("Champ avec erreur", key="gallery-error", error="Veuillez saisir un nom.")
            ui.input("Champ désactivé", key="gallery-input-disabled", value="Lecture seule", disabled=True)
            for size in ("small", "large"):
                ui.input(f"Taille {size}", key=f"gallery-input-{size}", size=size)
            query = ui.live_input("Recherche instantanée", key="gallery-live", placeholder="Rechercher un aliment…", clear_label="Effacer la recherche", helper="Résultat actualisé pendant la saisie.")
            st.caption(f"Recherche : {query or '—'}")
        with right, ui.card(key="gallery-selects", title="Select"):
            options = ["Petit-déjeuner", "Déjeuner", "Dîner"]
            ui.select("Repas", options, key="gallery-select", index=None, placeholder="Choisir un repas")
            ui.select("Sélection désactivée", options, key="gallery-select-disabled", disabled=True)
            ui.select("Sélection avec erreur", options, key="gallery-select-error", index=None, error="Choisissez un repas.")
            for size in ("small", "large"):
                ui.select(f"Taille {size}", options, key=f"gallery-select-{size}", size=size)
            ui.number_input("Quantité (g)", key="gallery-quantity", value=100.0, min_value=0.0, step=10.0)
    with cards:
        left, right = ui.split_layout(key="gallery-cards", widths=(1, 1))
        with left, ui.card(key="gallery-card", title="Un repas à votre rythme", description="Surface neutre, bordure fine, espace pour respirer."):
            st.write("Les cartes regroupent du contenu et de vrais widgets Streamlit.")
            ui.button("Composer mon repas", key="gallery-card-action", variant="primary")
        with right:
            ui.stat_card("Calories", "640 kcal", target="Objectif : 2 000 kcal · 32 %", progress=.32, progress_label="Calories")
            with ui.card(key="gallery-compact", title="Carte compacte", compact=True):
                st.caption("Pour les aliments et les listes.")
        ui.data_table(["Nutriment", "Apport", "Objectif", "Progression"], [["Protéines", "32 g", "100 g", .32], ["Glucides", "80 g", "250 g", .32]], progress_column=3)
