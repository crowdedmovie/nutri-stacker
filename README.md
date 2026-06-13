# Nutri Stacker

Nutri Stacker est une app Streamlit pour composer un repas et visualiser rapidement ses apports en macros et micronutriments.

L'app :
- charge les aliments depuis `food.json`
- permet de définir et sauvegarder des objectifs nutritionnels
- calcule les apports du repas courant
- permet de sauvegarder et recharger des repas en fichiers JSON

## Lancer l'app

1. Installer les dépendances Python nécessaires.
2. Lancer Streamlit :

```bash
streamlit run main.py
```

3. Ouvrir l'URL affichée par Streamlit dans le navigateur.

## Fichiers importants

- `main.py` : interface et logique de calcul
- `food.json` : base des aliments et nutriments
- `user_targets.json` : objectifs sauvegardés localement, généré automatiquement
- `saved_meals/` : repas sauvegardés, généré automatiquement
