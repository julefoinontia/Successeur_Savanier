# Remplaçant de Téji Savanier : recherche de profils similaires

Projet personnel en Python qui identifie, parmi les milieux de terrain de 24 championnats européens, les joueurs au profil statistique le plus proche de Téji Savanier (FC Metz) et valant moins de 6 M€. Le code est réutilisable pour n'importe quel autre joueur de champ.

## Principe

1. **Extraction** des statistiques joueurs depuis FBref (via la librairie `soccerdata`).
2. **Valeurs marchandes** issues du jeu de données ouvert Transfermarkt `transfermarkt-datasets`.
3. **Analyse** : les compteurs sont ramenés par 90 minutes, standardisés, réduits par ACP (90 % de la variance conservée), puis comparés au joueur cible par similarité cosinus. Seuls les joueurs de même poste, avec assez de minutes et une valeur inférieure au plafond sont classés.
4. **Sorties** : un classement CSV et un graphique radar (cible contre les 3 meilleurs candidats).

## Contenu du dossier

| Fichier | Rôle |
|---|---|
| `00_config_championnats.py` | Ajoute 24 championnats européens à `~/soccerdata/config/league_dict.json`. À lancer une seule fois. |
| `01_extraction_fbref.py` | Télécharge les stats FBref et crée `data/fbref_joueurs.csv`. |
| `03_preparer_valeurs.py` | Télécharge la table Transfermarkt et crée `data/valeurs.csv`. |
| `02_remplacant_savanier.py` | Calcule le classement et le radar. |
| `requirements.txt` | Dépendances Python. |

Fichiers produits dans `data/` : `fbref_joueurs.csv`, `valeurs.csv`, `classement_remplacants.csv`, `radar.png`.

## Installation

Prérequis : Python 3.10 ou plus récent.

Bibliothèques externes : `soccerdata`, `scikit-learn`, `pandas`, `numpy`, `matplotlib`.

## Utilisation

Toutes les commandes se lancent depuis le même dossier.

```bash
python 00_config_championnats.py     # une seule fois
python 01_extraction_fbref.py        # ~35 min la 1re fois, ensuite cache
python 03_preparer_valeurs.py        # une seule fois (ou pour rafraîchir)
python 02_remplacant_savanier.py     # l'analyse
```

Pour vérifier que les championnats sont bien déclarés :

```bash
python -c "import soccerdata as sd; print(sd.FBref.available_leagues())"
```

## Paramètres de l'analyse

Variables au début de `02_remplacant_savanier.py` :

| Variable | Valeur par défaut | Rôle |
|---|---|---|
| `CIBLE` | `"Téji Savanier"` | Joueur à remplacer, orthographe FBref (accents et tirets tolérés). |
| `POSTE` | `"MF"` | Poste FBref : `MF`, `DF`, `FW`. |
| `VALEUR_MAX` | `6_000_000` | Plafond de valeur marchande (€). |
| `MINUTES_MIN` | `900` | Minutes minimales pour que les stats par 90 min soient fiables. |
| `SAISONS_RETENUES` | `{"2526", "2025"}` | Saisons comparées. `2025` couvre la Norvège et la Suède (saison calendaire). |
| `TOP_N` | `15` | Taille du classement. |

Pour analyser un autre joueur, changez `CIBLE` et `POSTE`, puis relancez uniquement le script 02. Pour ajouter la saison 2026-27, ajoutez `"2026-2027"` dans `SAISONS` du script 01, mettez `{"2627", "2026"}` dans `SAISONS_RETENUES` et baissez `MINUTES_MIN` (500 à 600 en début de saison).

## Limites connues

- **Stats avancées indisponibles** : FBref a retiré les données Opta (xG, passes progressives, actions défensives détaillées) le 20 janvier 2026. Les tables `passing`, `passing_types`, `goal_shot_creation`, `defense` et `possession` échouent avec un `TypeError` attendu. La comparaison repose sur les tables `standard`, `shooting`, `misc` et `playing_time`.
- **Championnats non récupérés** : `ENG-Championship`, `GER-2. Bundesliga`, `ITA-Serie B`, `ESP-Segunda Division` et `ROU-Liga I` ne renvoient aucune saison, vraisemblablement à cause d'un nom de compétition incorrect dans `00_config_championnats.py` (à vérifier sur fbref.com/en/comps/).
- **Valeurs marchandes datées** : le jeu de données Transfermarkt est à jour au 6 juillet 2026 (mises à jour suspendues). Les joueurs dont le nom diffère trop entre FBref et Transfermarkt, ou sans valeur, sont exclus du classement.
- **Poste large** : FBref ne distingue pas latéraux et défenseurs centraux (`DF`). Un filtre sur la colonne `sub_position` de Transfermarkt serait une amélioration utile hors milieux.
- **Gardiens** : non pris en charge (tables `keepers` non extraites).
- **Interprétation** : le score mesure la proximité statistique, pas le niveau ni l'adéquation tactique. Le niveau du championnat d'origine, l'âge et la fin de contrat sont à vérifier à part, avec de la vidéo.

## Dépannage

| Symptôme | Cause probable |
|---|---|
| `Invalid league '...'` | `00_config_championnats.py` non lancé, ou fichier écrit dans un autre dossier que `~/soccerdata/config/`. |
| `No such file or directory: 'data/valeurs.csv'` | Script 03 non lancé, ou scripts lancés depuis un autre dossier (Jupyter inclus). |
| `ModuleNotFoundError` | Environnement virtuel non activé, ou dépendance non installée. |
| `Cible introuvable` | Joueur absent des championnats extraits, moins de `MINUTES_MIN` minutes, ou nom mal orthographié. |
| Erreurs 403 / 429, CAPTCHA | FBref limite les requêtes. Attendre, puis relancer : le cache évite de tout retélécharger. |

## Sources de données

- Statistiques : [FBref](https://fbref.com), via [soccerdata](https://github.com/probberechts/soccerdata).
- Valeurs marchandes : [transfermarkt-datasets](https://github.com/dcaribou/transfermarkt-datasets), d'après Transfermarkt.

Respectez les conditions d'utilisation de ces sites : le projet est destiné à un usage personnel et non commercial.
