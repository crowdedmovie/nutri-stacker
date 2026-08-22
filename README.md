# Nutri Stacker

Nutri Stacker est une app Streamlit pour composer un repas et visualiser rapidement ses apports en macros et micronutriments.

L'app :
- charge les aliments depuis `food.json`
- permet de definir et sauvegarder des objectifs nutritionnels
- calcule les apports du repas courant
- permet de sauvegarder et recharger des repas en fichiers JSON

## Lancer l'app

```bash
streamlit run main.py
```

## Fichiers importants

- `main.py` : interface et logique de calcul
- `food.json` : base des aliments et nutriments
- `user_targets.json` : objectifs sauvegardes localement
- `saved_meals/` : repas sauvegardes automatiquement

## Tester la PWA localement

L'app Streamlit continue de tourner sur le port 8501. Dans un second terminal,
lancer le shell PWA :

```bash
python pwa_server.py --port 5500
```

Depuis un navigateur sur le meme reseau, ouvrir :

```text
http://<adresse-ip-du-pc>:5500
```

Le shell charge l'app Streamlit depuis le port 8501.

Attention : une adresse HTTP en `192.168.x.x` n'est pas un contexte securise,
donc Chrome Android ne la considerera pas comme une PWA pleinement installable.
Pour tester l'installation PWA, utiliser HTTPS ou, avec Android connecte en USB,
faire suivre les ports vers `localhost` avec `adb reverse` :

```bash
adb reverse tcp:5500 tcp:5500
adb reverse tcp:8501 tcp:8501
```

Puis ouvrir `http://localhost:5500` sur Android.
