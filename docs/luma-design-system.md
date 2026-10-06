# Design system Nutri Stacker, inspiré de Luma

Analyse du guide public le 6 octobre 2026. Implémentation pour Streamlit **1.62.0**, version déjà fixée dans le projet.

## Projet et fonctionnement initial

`main.py` charge le catalogue, les objectifs, les favoris et le repas en cours, initialise `st.session_state`, puis affiche trois onglets. `app/ui.py` orchestre les interactions ; `app/calculations.py` calcule les apports et les recommandations ; `app/food_catalog.py` filtre et trie les aliments ; `app/storage.py` lit et écrit les JSON. `app/i18n.py` fournit les textes français et anglais.

Le parcours Repas possède un sélecteur simple et un catalogue avancé avec recherche tolérante aux fautes, favoris et tri par nutriment. Ajouter un aliment crée une quantité initiale ; modifier sa quantité recalcule ses apports ; retirer un aliment relance l'écran. Les objectifs combinent un calculateur énergétique et des champs éditables. Les repas nommés se sauvegardent et se rechargent depuis `saved_meals/`. Le repas et les cibles en cours persistent après les interactions.

La présentation initiale réunissait un grand bloc CSS dans `app/ui.py`, des cartes HTML spécifiques et des widgets natifs. Un iframe `components.v1.html` installait un observateur sur le document parent et simulait Entrée sur les champs de recherche. Il dépendait du DOM interne de Streamlit et de l'accès au parent.

La coque PWA reste un service distinct : elle embarque l'application à `/streamlit/`, et exige une connexion au serveur. Cette architecture et les formats JSON restent compatibles.

## Sources et méthode

| Source publique | Éléments étudiés | Transposition |
| --- | --- | --- |
| [Input](https://luma.com/style-guide/input) | Tailles, labels, contours, fond plein, accessoires, erreurs, désactivation, sélecteurs | Input natif, Number Input, Select et recherche personnalisée |
| [Button](https://luma.com/style-guide/button) | Actions pleines, contours, actions discrètes, icônes, variantes de taille et largeur | Primary, Secondary, Ghost et Danger |
| [Text](https://luma.com/style-guide/text) | Hiérarchie, titres de sections, sous-titres, texte secondaire, pills | Typographie sobre, poids 400/500/600 |
| [Color](https://luma.com/style-guide/color) | Neutres, textes primaire/secondaire/tertiaire, variantes sémantiques, thèmes | Tokens sémantiques clairs et sombres |
| [Controls](https://luma.com/style-guide/controls) | Sélection, toggles, switchers, états désactivés | Conservation des contrôles Streamlit pour les préférences |
| [Overlay](https://luma.com/style-guide/overlay) | Menus, panneaux, tooltips, notifications | Select natif, bordures fines et ombres limitées aux surfaces flottantes |
| [Events](https://luma.com/style-guide/events) | Groupement du contenu et métadonnées | Cartes de contenu compactes |

Le HTML et la feuille CSS publique référencée par le guide ont été inspectés. Les faits mesurés ci-dessous viennent de ces règles CSS, et non d'une estimation à partir du texte des pages. Aucun navigateur contrôlable n'était disponible dans cette session : les états interactifs et la composition à différentes largeurs n'ont pas été comparés par captures. La section Collapse n'a pas pu être chargée par l'outil web ; elle ne sert pas de preuve à l'analyse.

Le dépôt ne contient aucun CSS, script, logo, photographie ni fichier de police téléchargé de Luma. Les règles de l'implémentation sont originales. La marque, le monogramme `n.` et les données restent ceux de Nutri Stacker.

## Langage visuel et mesures

Les règles publiques utilisent des contrôles de **30 / 38 / 44 px**, un rayon de contrôle de **8 px**, un rayon de carte de **12 px**, un corps de **16 px**, un label moyen de **14 px** et un écart label/champ de **6 px**. Le champ moyen utilise **14 px** de padding horizontal. Les transitions rapides et normales durent **200 / 300 ms** avec une courbe `cubic-bezier(.4, 0, .2, 1)`. Les textes distinguent les poids **400, 500 et 600**. Le focus de l'input renforce le contour avec la couleur du texte principal ; l'erreur affecte le contour, le label et le texte d'aide.

Ces proportions structurent les composants. Les surfaces sont neutres ; le contraste et l'espacement portent la hiérarchie. Une action principale sombre dans le thème clair, ou claire dans le thème sombre, ressort sans multiplier les accents colorés. Les états nutritionnels emploient une couleur sémantique discrète. Les cartes reposent sur un contour fin plutôt que sur le dégradé et l'ombre prononcés de l'interface initiale.

La palette exacte, la grille d'espacement 4/8/12/16/20/24/32/40/48 px, le titre de page à 32 px, la largeur maximale de 1 280 px et les seuils 900/640 px sont **des choix de transposition pour cette application**, pas des valeurs officiellement attribuées à Luma. La taille des cibles doit rester adaptée à l'usage tactile ; la variante `large` offre 44 px pour les actions qui le nécessitent.

La police de l'application est une pile système. Inter est utilisée seulement si elle est déjà disponible localement. Recoleta, mentionnée dans la section Text pour les pages marketing et soumise à licence, n'est pas incluse. Aucune police distante n'est chargée.

## Tokens et thèmes

`ui/tokens.json` est la source des tokens CSS. `ui/tokens.py` les convertit en variables `--ns-*`. Les groupes couvrent police, espace, rayon, hauteur de contrôle, layout, mouvement et couleurs sémantiques pour chaque thème.

| Token | Clair | Sombre |
| --- | --- | --- |
| `surface` | `#ffffff` | `#17191b` |
| `surface-secondary` | `#f7f7f7` | `#222427` |
| `text`, `action` | `#131517` | `#f5f5f5` |
| `muted` | `#62676c` | `#b0b3b8` |
| `border` | `#dedfe1` | `#3b3e43` |
| `success` | `#28734d` | `#7dcda2` |
| `danger` | `#c0334d` | `#fa92a3` |

`ui.apply_theme()` lit `st.context.theme.type` et injecte les tokens du thème courant. Si le contexte n'a pas encore de thème, le thème clair configuré sert de valeur initiale. Les six valeurs fondamentales de la configuration native sont synchronisées manuellement avec les tokens ; un test vérifie les couleurs pour prévenir une divergence. Après une modification de thème dans Streamlit, un rerun synchronise les composants personnalisés.

`.streamlit/config.toml` conserve la configuration serveur et ajoute les thèmes `[theme.light]` et `[theme.dark]`, le corps à 16 px, les titres à 600, les rayons et les bordures de widgets. Le changement de thème reste accessible dans les réglages Streamlit.

## Architecture

```text
ui/
  __init__.py             API publique
  tokens.json             valeurs partagées
  tokens.py               conversion en variables CSS
  theme.py                sélection du thème et installation du CSS
  styles.css              présentation et adaptateur DOM Streamlit
  components.py           Button, Input, Number Input, Select, Card, Stat Card, Table
  layout.py               shell, header, onglets et colonnes adaptatives
  live_input.py           adaptateur Python du Custom Component v2
  frontend/
    live_input.js         événements, debounce, clavier et nettoyage
    live_input.css        styles isolés dans le Shadow DOM
design_system.py          galerie locale sans accès aux données utilisateur
tests/test_ui_integration.py
```

`ui` n'importe aucune logique métier depuis `app`. Les vues de `app/ui.py` assemblent les composants, calculent les valeurs et appellent le stockage. Les clés des widgets métier déjà présents sont conservées ; les conteneurs ont des clés `ui-*` pour cibler leur présentation. Les nouvelles actions disposent de clés explicites.

## Composants et contrats

| API | Contrat |
| --- | --- |
| `button(label, key=…, variant=…, size=…, **kwargs)` | Retourne un booléen. Variantes `primary`, `secondary`, `ghost`, `danger`. Tailles `small`, `medium`, `large`. Transmet `disabled`, `help`, `on_click`, `args`, `kwargs`, `icon`, `width` à Streamlit. |
| `input(label, key=…, helper=…, error=…, variant=…, size=…)` | Retourne une chaîne. Variantes `outline` / `solid`. État, placeholder, type et désactivation natifs. Validation fournie par l'appelant. |
| `number_input(label, key=…, …)` | Conserve les bornes, le pas, le type et la validation numériques natifs. |
| `select(label, options, key=…, …)` | Retourne une option ou `None` avec `index=None`. Conserve recherche, navigation au clavier, `format_func` et `filter_mode` natifs. |
| `card(key=…, title=…, description=…, compact=…)` | Context manager accueillant de vrais widgets Streamlit. Padding normal 20 px, compact 16 px. |
| `stat_card(label, value, target=…, progress=…, progress_label=…)` | Affichage échappé, progression bornée à 0–100 %, sémantique `progressbar`. |
| `data_table(headers, rows, progress_column=…)` | Table HTML sémantique, textes échappés, défilement horizontal, zone accessible au clavier. |
| `live_input(label, key=…, …)` | Recherche avec accessoire loupe, effacement et synchronisation Python à chaque pause de saisie. |

Les boutons proposent repos, survol, activation, focus clavier et désactivation. Les champs et Select proposent repos, survol, focus, valeur, placeholder, erreur et désactivation. Le CSS des variantes d'erreur ne remplace pas la validation métier. Le texte d'erreur natif est annoncé via `role="alert"` ; les attributs internes `aria-invalid`/`aria-describedby` ne sont pas modifiés sur les widgets natifs. Le composant personnalisé les gère explicitement.

Exemple d'écran :

```python
import streamlit as st
import ui

st.set_page_config(layout="wide")
ui.apply_theme()
with ui.app_shell():
    ui.page_header("Mon repas", "Composez un repas et ajustez vos quantités.")
    with ui.card(key="meal", title="Composition"):
        name = ui.input("Nom", key="meal-name", placeholder="Déjeuner")
        food = ui.select("Aliment", ["Amandes", "Banane"], key="food", index=None)
        if ui.button("Ajouter", key="add", variant="primary", disabled=food is None):
            st.toast(f"{food} ajouté")
```

Chaque clé doit être unique dans le script. Une clé de widget ne doit pas être réaffectée après son instanciation ; les callbacks ou un indicateur traité au début du rerun permettent les réinitialisations.

## Natif et Custom Components

Button, Input, Number Input et Select conservent le moteur Streamlit : il assure les callbacks, les reruns, les formulaires et les contrôles clavier. Le sélecteur simple conserve le filtrage `contains`. Un Select personnalisé n'apporterait pas assez de valeur pour justifier de réimplémenter les règles d'un combobox accessible.

La recherche avancée exige une communication pendant la saisie et des accessoires précis. `live_input` utilise donc [Custom Components v2](https://docs.streamlit.io/develop/api-reference/custom-components/st.components.v2.component), disponible dans la version installée. Le composant s'enregistre une fois par processus et communique via `setStateValue("value", …)` et `on_value_change`. Il n'accède jamais aux champs du document parent et n'installe aucun `MutationObserver` sur Streamlit.

Le debounce par défaut est de 180 ms. Entrée et la perte de focus transmettent immédiatement la valeur ; Échap et le bouton d'effacement vident la recherche. La composition IME suspend la transmission jusqu'à sa fin. Les timers et listeners sont nettoyés. La valeur reçue est recopiée dans la clé métier `food_search_query`. Les données du label, de l'aide et des erreurs passent par `textContent`, jamais par une interpolation HTML.

Le composant recherche vise les changements immédiats hors formulaire. Pour un `st.form`, employer les widgets natifs afin de conserver la soumission groupée.

## Adaptation des écrans

Repas regroupe le catalogue, la sélection et l'analyse dans trois cartes. Les aliments possèdent des cartes compactes et une action de retrait Danger. Les macros regroupent valeur, cible et barre dans la même carte. Les micronutriments utilisent une table qui défile horizontalement sur petit écran au lieu de faire éclater chaque ligne en six blocs verticaux.

Le calculateur possède des cartes Profil et Activité. Les objectifs éditables et les repas sauvegardés emploient les mêmes contrôles et boutons. Les messages de confirmation conservent leur bouton de fermeture et prennent des couleurs sémantiques légères. Le header, la navigation et les espacements sont partagés entre les vues.

Les layouts nommés passent en une colonne à 900 px ; les marges se réduisent à 640 px. Les onglets peuvent défiler. Les autres colonnes gardent le comportement natif Streamlit. Ces seuils nécessitent encore une vérification visuelle dans un navigateur.

Deux incohérences initiales sont corrigées pendant l'intégration : les totaux sont calculés après la lecture des quantités du rendu courant, et le chargement d'un repas actualise également son nom dans le champ de sauvegarde.

## Vérification et maintenance

```bash
python -m unittest discover -s tests -v
python -m compileall -q main.py design_system.py app ui
streamlit run main.py
```

Galerie indépendante, éventuellement sur un second port :

```bash
streamlit run design_system.py --server.port 8502
```

Avec la configuration du dépôt, la galerie est accessible à `http://localhost:8502/streamlit/`. Elle ne lit ni ne modifie les repas, préférences ou objectifs sauvegardés.

Les neuf tests Python passent : ajout/retrait, quantité et total du même rendu, sauvegarde/chargement et nom, validation d'un repas vide, callbacks d'objectifs, recommandations, catalogue avancé/favoris/tri, langue et restauration après une nouvelle session, rendu de la galerie, et concordance tokens/configuration. Tous les accès persistants de l'application pendant les tests pointent vers un répertoire temporaire.

AppTest vérifie le serveur et les widgets natifs, mais n'exécute pas le JavaScript et ne vérifie pas les pixels. À contrôler dans la galerie : largeurs 390/768/1 280 px, thèmes clair/sombre, survol, focus Tab, menu Select avec flèches/Entrée/Échap, recherche continue avec accents/IME, effacement, conservation du focus pendant les reruns et réduction des animations.

Les sélecteurs `data-testid` et BaseWeb sont rassemblés dans `ui/styles.css`. Ils constituent la zone de compatibilité à vérifier lors d'une mise à jour de Streamlit. Le composant v2 utilise des styles isolés ; ses dépendances au DOM sont limitées à ses propres éléments. Aucune nouvelle dépendance Python ou étape de build JavaScript n'est nécessaire.
