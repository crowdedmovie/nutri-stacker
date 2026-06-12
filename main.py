import streamlit as st
import pandas as pd

# Configuration de la page
st.set_page_config(page_title="Mon Optimisateur de Micronutriments", page_icon="🥦", layout="wide")

# ==========================================
# 1. BASE DE DONNÉES UNIFIÉE (Pour 100g ou 100mL)
# ==========================================
DATA_MICROS = {
    "Abricots secs": {"Magnesium": 55, "Bore": 2.75, "Cholesterol": 0, "Sodium": 10, "Calcium": 15, "Iode": 0, "Omega3": 0, "Potassium": 900, "Selenium": 0, "VitamineA": 300, "VitamineC": 30},
    "Algues marines (kombu, nori...)": {"Magnesium": 80, "Bore": 0.3, "Cholesterol": 0, "Sodium": 300, "Calcium": 70, "Iode": 1050, "Omega3": 0, "Potassium": 200, "Selenium": 2, "VitamineA": 0, "VitamineC": 5},
    "Amandes": {"Magnesium": 260, "Bore": 2.0, "Cholesterol": 0, "Sodium": 10, "Calcium": 250, "Iode": 0, "Omega3": 0, "Potassium": 700, "Selenium": 3, "VitamineA": 0, "VitamineC": 0},
    "Avocat": {"Magnesium": 35, "Bore": 1.5, "Cholesterol": 0, "Sodium": 7, "Calcium": 12.5, "Iode": 2.5, "Omega3": 0, "Potassium": 490, "Selenium": 3, "VitamineA": 150, "VitamineC": 10},
    "Avoine / riz complet": {"Magnesium": 120, "Bore": 0.2, "Cholesterol": 0, "Sodium": 5, "Calcium": 30, "Iode": 0, "Omega3": 0, "Potassium": 350, "Selenium": 12.5, "VitamineA": 0, "VitamineC": 0},
    "Banane": {"Magnesium": 27, "Bore": 0.1, "Cholesterol": 0, "Sodium": 1, "Calcium": 5, "Iode": 0, "Omega3": 0, "Potassium": 375, "Selenium": 1, "VitamineA": 30, "VitamineC": 8},
    "Beurre doux / Fromages gras": {"Magnesium": 10, "Bore": 0.01, "Cholesterol": 225, "Sodium": 10, "Calcium": 20, "Iode": 35, "Omega3": 0, "Potassium": 30, "Selenium": 2, "VitamineA": 300, "VitamineC": 0},
    "Bœuf / agneau / veau": {"Magnesium": 22.5, "Bore": 0.035, "Cholesterol": 75, "Sodium": 70, "Calcium": 15, "Iode": 7.5, "Omega3": 0, "Potassium": 350, "Selenium": 20, "VitamineA": 0, "VitamineC": 0},
    "Brocolis / choux": {"Magnesium": 25, "Bore": 0.2, "Cholesterol": 0, "Sodium": 15, "Calcium": 60, "Iode": 1, "Omega3": 0, "Potassium": 300, "Selenium": 2, "VitamineA": 100, "VitamineC": 60},
    "Cabillaud / colin / morue": {"Magnesium": 30, "Bore": 0.03, "Cholesterol": 60, "Sodium": 80, "Calcium": 15, "Iode": 200, "Omega3": 200, "Potassium": 350, "Selenium": 35, "VitamineA": 10, "VitamineC": 0},
    "Cacao cru": {"Magnesium": 425, "Bore": 0.3, "Cholesterol": 0, "Sodium": 15, "Calcium": 100, "Iode": 0, "Omega3": 0, "Potassium": 1500, "Selenium": 4, "VitamineA": 0, "VitamineC": 12.5},
    "Carottes": {"Magnesium": 15, "Bore": 0.3, "Cholesterol": 0, "Sodium": 60, "Calcium": 30, "Iode": 2.0, "Omega3": 0, "Potassium": 310, "Selenium": 1, "VitamineA": 1400, "VitamineC": 25},
    "Charcuterie (jambon blanc, poulet tranché)": {"Magnesium": 15, "Bore": 0, "Cholesterol": 60, "Sodium": 950, "Calcium": 10, "Iode": 10, "Omega3": 0, "Potassium": 250, "Selenium": 15, "VitamineA": 0, "VitamineC": 0},
    "Charcuterie sèche (jambon cru, bacon)": {"Magnesium": 20, "Bore": 0, "Cholesterol": 80, "Sodium": 1800, "Calcium": 10, "Iode": 15, "Omega3": 0, "Potassium": 350, "Selenium": 20, "VitamineA": 0, "VitamineC": 0},
    "Chocolat noir 90 %": {"Magnesium": 215, "Bore": 0.2, "Cholesterol": 0, "Sodium": 15, "Calcium": 60, "Iode": 0, "Omega3": 0, "Potassium": 800, "Selenium": 3, "VitamineA": 0, "VitamineC": 12.5},
    "Comté / Gruyère / Emmental": {"Magnesium": 30, "Bore": 0.03, "Cholesterol": 90, "Sodium": 400, "Calcium": 900, "Iode": 40, "Omega3": 0, "Potassium": 110, "Selenium": 7.5, "VitamineA": 275, "VitamineC": 0},
    "Crevettes / fruits de mer / huîtres": {"Magnesium": 40, "Bore": 0.035, "Cholesterol": 175, "Sodium": 250, "Calcium": 80, "Iode": 150, "Omega3": 500, "Potassium": 250, "Selenium": 47.5, "VitamineA": 30, "VitamineC": 0},
    "Dattes": {"Magnesium": 50, "Bore": 1.0, "Cholesterol": 0, "Sodium": 5, "Calcium": 40, "Iode": 0, "Omega3": 0, "Potassium": 650, "Selenium": 2, "VitamineA": 400, "VitamineC": 15},
    "Eau de coco": {"Magnesium": 27.5, "Bore": 0.1, "Cholesterol": 0, "Sodium": 125, "Calcium": 25, "Iode": 15, "Omega3": 0, "Potassium": 275, "Selenium": 0, "VitamineA": 0, "VitamineC": 22.5},
    "Eaux minérales riches (Hépar, Contrex)": {"Magnesium": 90, "Bore": 0, "Cholesterol": 0, "Sodium": 10, "Calcium": 500, "Iode": 0, "Omega3": 0, "Potassium": 5, "Selenium": 0, "VitamineA": 0, "VitamineC": 0},
    "Feta": {"Magnesium": 20, "Bore": 0.03, "Cholesterol": 90, "Sodium": 1200, "Calcium": 505, "Iode": 40, "Omega3": 0, "Potassium": 120, "Selenium": 7.5, "VitamineA": 180, "VitamineC": 0},
    "Foie (bœuf, poulet, morue)": {"Magnesium": 20, "Bore": 0.02, "Cholesterol": 375, "Sodium": 80, "Calcium": 10, "Iode": 15, "Omega3": 300, "Potassium": 300, "Selenium": 45, "VitamineA": 7500, "VitamineC": 20},
    "Fromages / produits laitiers (moyens)": {"Magnesium": 20, "Bore": 0.03, "Cholesterol": 70, "Sodium": 200, "Calcium": 140, "Iode": 40, "Omega3": 0, "Potassium": 125, "Selenium": 7.5, "VitamineA": 150, "VitamineC": 0},
    "Fruits secs (abricots, raisins, pruneaux)": {"Magnesium": 55, "Bore": 2.75, "Cholesterol": 0, "Sodium": 10, "Calcium": 50, "Iode": 0, "Omega3": 0, "Potassium": 900, "Selenium": 0, "VitamineA": 300, "VitamineC": 30},
    "Graines de courge": {"Magnesium": 530, "Bore": 0.5, "Cholesterol": 0, "Sodium": 10, "Calcium": 50, "Iode": 0, "Omega3": 0, "Potassium": 800, "Selenium": 10, "VitamineA": 0, "VitamineC": 0},
    "Graines de tournesol / sésame": {"Magnesium": 350, "Bore": 0.5, "Cholesterol": 0, "Sodium": 10, "Calcium": 100, "Iode": 0, "Omega3": 0, "Potassium": 650, "Selenium": 65, "VitamineA": 0, "VitamineC": 0},
    "Huile de foie de morue": {"Magnesium": 0, "Bore": 0, "Cholesterol": 500, "Sodium": 0, "Calcium": 0, "Iode": 0, "Omega3": 27500, "Potassium": 0, "Selenium": 0, "VitamineA": 30000, "VitamineC": 0}, # Estimations pour 100g
    "Jus de raisin / vin rouge (modéré)": {"Magnesium": 12, "Bore": 0.9, "Cholesterol": 0, "Sodium": 5, "Calcium": 10, "Iode": 1, "Omega3": 0, "Potassium": 150, "Selenium": 0, "VitamineA": 0, "VitamineC": 15},
    "Kiwi": {"Magnesium": 17, "Bore": 0.15, "Cholesterol": 0, "Sodium": 3, "Calcium": 34, "Iode": 1, "Omega3": 0, "Potassium": 312, "Selenium": 0, "VitamineA": 50, "VitamineC": 85},
    "Lait entier": {"Magnesium": 11, "Bore": 0.03, "Cholesterol": 12, "Sodium": 50, "Calcium": 125, "Iode": 40, "Omega3": 0, "Potassium": 150, "Selenium": 2, "VitamineA": 40, "VitamineC": 0},
    "Légumes verts (épinards, blettes)": {"Magnesium": 90, "Bore": 0.3, "Cholesterol": 0, "Sodium": 70, "Calcium": 90, "Iode": 2, "Omega3": 0, "Potassium": 450, "Selenium": 1, "VitamineA": 500, "VitamineC": 25},
    "Légumineuses (lentilles, haricots blancs...)": {"Magnesium": 37.5, "Bore": 0.4, "Cholesterol": 0, "Sodium": 50, "Calcium": 50, "Iode": 0, "Omega3": 0, "Potassium": 350, "Selenium": 6.5, "VitamineA": 0, "VitamineC": 0},
    "Maquereau": {"Magnesium": 35, "Bore": 0.03, "Cholesterol": 70, "Sodium": 400, "Calcium": 15, "Iode": 40, "Omega3": 3000, "Potassium": 425, "Selenium": 42.5, "VitamineA": 60, "VitamineC": 0},
    "Miel brut": {"Magnesium": 2, "Bore": 0.75, "Cholesterol": 0, "Sodium": 5, "Calcium": 10, "Iode": 1.5, "Omega3": 0, "Potassium": 50, "Selenium": 1.5, "VitamineA": 0, "VitamineC": 7.5},
    "Mozzarella / Ricotta": {"Magnesium": 15, "Bore": 0.03, "Cholesterol": 60, "Sodium": 100, "Calcium": 300, "Iode": 30, "Omega3": 0, "Potassium": 100, "Selenium": 5, "VitamineA": 200, "VitamineC": 0},
    "Noix du Brésil": {"Magnesium": 350, "Bore": 1.5, "Cholesterol": 0, "Sodium": 3, "Calcium": 160, "Iode": 0, "Omega3": 0, "Potassium": 600, "Selenium": 1450, "VitamineA": 0, "VitamineC": 0},
    "Œufs entiers (valeurs pour 100g)": {"Magnesium": 11, "Bore": 0.05, "Cholesterol": 333, "Sodium": 140, "Calcium": 55, "Iode": 27.5, "Omega3": 50, "Potassium": 120, "Selenium": 20, "VitamineA": 175, "VitamineC": 0}, # 333mg cholestérol converti aux 100g depuis l'indication d'un œuf de 60g
    "Parmesan / Grana Padano": {"Magnesium": 40, "Bore": 0.03, "Cholesterol": 90, "Sodium": 1350, "Calcium": 1150, "Iode": 45, "Omega3": 0, "Potassium": 125, "Selenium": 10, "VitamineA": 280, "VitamineC": 0},
    "Patates douces": {"Magnesium": 25, "Bore": 0.4, "Cholesterol": 0, "Sodium": 30, "Calcium": 30, "Iode": 2.0, "Omega3": 0, "Potassium": 350, "Selenium": 1, "VitamineA": 1800, "VitamineC": 25},
    "Poivrons rouges": {"Magnesium": 12, "Bore": 0.3, "Cholesterol": 0, "Sodium": 4, "Calcium": 10, "Iode": 2.0, "Omega3": 0, "Potassium": 250, "Selenium": 1, "VitamineA": 600, "VitamineC": 135},
    "Pollen de fleur": {"Magnesium": 25, "Bore": 0.75, "Cholesterol": 0, "Sodium": 20, "Calcium": 30, "Iode": 1.5, "Omega3": 0, "Potassium": 175, "Selenium": 7.5, "VitamineA": 450, "VitamineC": 35},
    "Pommes de terre cuites (avec peau)": {"Magnesium": 23, "Bore": 0.2, "Cholesterol": 0, "Sodium": 5, "Calcium": 12, "Iode": 1, "Omega3": 0, "Potassium": 425, "Selenium": 1, "VitamineA": 0, "VitamineC": 15},
    "Poulet / dinde": {"Magnesium": 20, "Bore": 0.035, "Cholesterol": 80, "Sodium": 70, "Calcium": 15, "Iode": 7.5, "Omega3": 0, "Potassium": 300, "Selenium": 25, "VitamineA": 30, "VitamineC": 0},
    "Pruneaux": {"Magnesium": 40, "Bore": 2.25, "Cholesterol": 0, "Sodium": 2, "Calcium": 43, "Iode": 0, "Omega3": 0, "Potassium": 900, "Selenium": 0, "VitamineA": 400, "VitamineC": 30},
    "Raisins secs": {"Magnesium": 35, "Bore": 3.5, "Cholesterol": 0, "Sodium": 11, "Calcium": 50, "Iode": 0, "Omega3": 0, "Potassium": 900, "Selenium": 0, "VitamineA": 400, "VitamineC": 30},
    "Sardines (en conserve avec arêtes)": {"Magnesium": 37.5, "Bore": 0.035, "Cholesterol": 70, "Sodium": 400, "Calcium": 375, "Iode": 40, "Omega3": 2150, "Potassium": 425, "Selenium": 55, "VitamineA": 60, "VitamineC": 0},
    "Saumon (sauvage)": {"Magnesium": 30, "Bore": 0.03, "Cholesterol": 70, "Sodium": 60, "Calcium": 15, "Iode": 40, "Omega3": 1600, "Potassium": 425, "Selenium": 42.5, "VitamineA": 50, "VitamineC": 0},
    "Skyr nature": {"Magnesium": 11, "Bore": 0.03, "Cholesterol": 15, "Sodium": 100, "Calcium": 165, "Iode": 40, "Omega3": 0, "Potassium": 150, "Selenium": 7.5, "VitamineA": 0, "VitamineC": 0},
    "Tomates / purée de tomate": {"Magnesium": 11, "Bore": 0.1, "Cholesterol": 0, "Sodium": 10, "Calcium": 10, "Iode": 1, "Omega3": 0, "Potassium": 230, "Selenium": 0, "VitamineA": 40, "VitamineC": 20},
}

# Objectifs optimaux et unités de mesure
MICROS_CONFIG = {
    "Magnesium": {"label": "Magnésium", "cible": 450.0, "unite": "mg"},
    "Bore": {"label": "Bore", "cible": 4.5, "unite": "mg"},
    "Cholesterol": {"label": "Cholestérol", "cible": 850.0, "unite": "mg"},
    "Sodium": {"label": "Sodium", "cible": 3000.0, "unite": "mg"},
    "Calcium": {"label": "Calcium", "cible": 1000.0, "unite": "mg"},
    "Iode": {"label": "Iode", "cible": 175.0, "unite": "µg"},
    "Omega3": {"label": "Oméga-3 (EPA+DHA)", "cible": 2500.0, "unite": "mg"},
    "Potassium": {"label": "Potassium", "cible": 4350.0, "unite": "mg"},
    "Selenium": {"label": "Sélénium", "cible": 112.5, "unite": "µg"},
    "VitamineA": {"label": "Vitamine A", "cible": 900.0, "unite": "µg ÉRA"},
    "VitamineC": {"label": "Vitamine C", "cible": 350.0, "unite": "mg"},
}

# ==========================================
# 2. INTERFACE UTILISATEUR
# ==========================================

st.title("🥦 Mon Optimisateur de Micronutriments Évolué")
st.write("Sélectionne tes aliments, saisis les quantités exactes et observe l'impact immédiat sur tes **11 indicateurs micro**.")

st.divider()

# Création des deux zones principales (gauche : saisie, droite : résultats)
col_saisie, col_resultats = st.columns([1, 1], gap="large")

with col_saisie:
    st.subheader("🛒 Composition du repas")
    liste_aliments = sorted(list(DATA_MICROS.keys()))
    
    aliments_choisis = st.multiselect(
        "Ajoute des aliments à ton repas :",
        options=liste_aliments,
        placeholder="Rechercher ou sélectionner un aliment..."
    )

    # Initialisation de notre dictionnaire de totaux pour le repas
    totaux_repas = {key: 0.0 for key in MICROS_CONFIG.keys()}

    if aliments_choisis:
        st.write("---")
        st.markdown("**⚖️ Quantités de chaque aliment (en g ou mL)**")
        
        for aliment in aliments_choisis:
            c_nom, c_input = st.columns([2, 1])
            with c_nom:
                st.markdown(f"<div style='padding-top: 5px;'><strong>{aliment}</strong></div>", unsafe_allow_html=True)
            with c_input:
                quantite = st.number_input(
                    label=f"Qté {aliment}",
                    min_value=0,
                    max_value=2000,
                    value=100, # Initialisation par défaut à 100g pour faciliter la lecture directe du profil
                    step=10,
                    key=f"in_{aliment}",
                    label_visibility="collapsed"
                )
            
            # Calcul cumulatif de tous les micros en direct pour cet aliment
            for micro in MICROS_CONFIG.keys():
                valeur_100g = DATA_MICROS[aliment].get(micro, 0.0)
                totaux_repas[micro] += (valeur_100g * quantite) / 100
    else:
        st.info("👋 Sélectionne un ou plusieurs aliments pour afficher les options de réglage des quantités.")

with col_resultats:
    st.subheader("📊 Analyse Nutritionnelle en Direct")
    
    if aliments_choisis:
        # Parcours propre de chaque micro pour fabriquer les jauges et les scores
        for micro, config in MICROS_CONFIG.items():
            total_calculé = totaux_repas[micro]
            cible = config["cible"]
            pourcentage = (total_calculé / cible) * 100
            
            # Message textuel simple de statut
            st.markdown(
                f"**{config['label']}** : `{total_calculé:.1f} {config['unite']}` / {int(cible)} {config['unite']} (*{pourcentage:.1f}%*)"
            )
            
            # Rendu d'une barre de progression propre (bridée à 100% max sur l'élément visuel)
            st.progress(min(total_calculé / cible, 1.0))
            
            # Alerte visuelle discrète si l'objectif d'un micro clé est parfaitement atteint ou dépassé
            if total_calculé >= cible and micro in ["Magnesium", "Omega3", "Bore"]:
                st.caption(f"✨ Objectif optimal en {config['label']} validé !")
                
    else:
        st.info("Sélectionne des aliments sur la gauche pour voir l'analyse micro s'afficher ici.")