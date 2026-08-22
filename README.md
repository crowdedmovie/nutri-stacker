# Nutri Stacker

Nutri Stacker est une app Flet pour composer un repas et visualiser rapidement ses apports en macros et micronutriments.

L'app :
- charge les aliments depuis `food.json`
- permet de definir et sauvegarder des objectifs nutritionnels
- calcule les apports du repas courant
- permet de sauvegarder et recharger des repas en fichiers JSON

## Lancer l'app

1. Installer les dependances Python necessaires :

```bash
pip install -r requirements.txt
```

2. Lancer Flet :

```bash
flet run main.py
```

Pour lancer l'app dans un navigateur, utiliser `flet run --web main.py`.

## Fichiers importants

- `main.py` : point d'entree Flet
- `app/ui.py` : interface Flet et gestion des evenements
- `app/calculations.py` : logique de calcul nutritionnel
- `food.json` : base des aliments et nutriments
- `user_targets.json` : objectifs sauvegardes localement
- `saved_meals/` : repas sauvegardes automatiquement
