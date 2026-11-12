"""
00_config_championnats.py
Ajoute les championnats européens "mineurs" au fichier league_dict.json de
soccerdata, pour que FBref() puisse les lire. À exécuter UNE SEULE FOIS.
Aucune installation nécessaire (modules standard de Python uniquement).
"""
import json  # module standard : lire/écrire du JSON
import os  # module standard : lire les variables d'environnement
from pathlib import Path  # module standard : manipuler les chemins de fichiers

# Dossier de config de soccerdata : $SOCCERDATA_DIR si défini, sinon ~/soccerdata
RACINE = Path(os.environ.get("SOCCERDATA_DIR", Path.home() / "soccerdata"))
DOSSIER = RACINE / "config"  # soccerdata cherche league_dict.json dans ce sous-dossier
DOSSIER.mkdir(parents=True, exist_ok=True)  # crée le dossier s'il n'existe pas encore
CHEMIN = DOSSIER / "league_dict.json"  # chemin complet du fichier de configuration

# Format : "CLE-INTERNE": ("nom EXACT de la compétition sur FBref", mois début, mois fin)
# Saison à cheval sur deux années : août -> mai. Saison calendaire : mars -> novembre.
# (vérifié) = nom retrouvé sur FBref ; (à vérifier) = nom probable, à contrôler sur fbref.com/en/comps/
CHAMPIONNATS = {
    "FRA-Ligue 2": ("Ligue 2", "Aug", "May"),  # (à vérifier) 2e division française
    "ENG-Championship": ("Championship", "Aug", "May"),  # (vérifié) 2e division anglaise
    "GER-2. Bundesliga": ("2. Bundesliga", "Aug", "May"),  # (vérifié) 2e division allemande
    "ITA-Serie B": ("Serie B", "Aug", "May"),  # (à vérifier) 2e division italienne
    "ESP-Segunda Division": ("Segunda División", "Aug", "May"),  # (à vérifier) 2e division espagnole
    "NED-Eredivisie": ("Eredivisie", "Aug", "May"),  # (vérifié) Pays-Bas
    "POR-Primeira Liga": ("Primeira Liga", "Aug", "May"),  # (vérifié) Portugal
    "BEL-Pro League": ("Belgian Pro League", "Jul", "May"),  # (vérifié) Belgique
    "SCO-Premiership": ("Scottish Premiership", "Aug", "May"),  # (vérifié) Écosse
    "TUR-Super Lig": ("Süper Lig", "Aug", "May"),  # (à vérifier) Turquie
    "AUT-Bundesliga": ("Austrian Football Bundesliga", "Jul", "May"),  # (vérifié) Autriche
    "SUI-Super League": ("Swiss Super League", "Jul", "May"),  # (à vérifier) Suisse
    "DEN-Superliga": ("Danish Superliga", "Jul", "May"),  # (à vérifier) Danemark
    "GRE-Super League": ("Super League Greece", "Aug", "May"),  # (à vérifier) Grèce
    "CZE-First League": ("Czech First League", "Jul", "May"),  # (à vérifier) Tchéquie
    "POL-Ekstraklasa": ("Ekstraklasa", "Jul", "May"),  # (vérifié) Pologne
    "ROU-Liga I": ("Liga I", "Jul", "May"),  # (vérifié, parfois noté "Liga I (M)") Roumanie
    "HUN-NB I": ("Nemzeti Bajnokság I", "Jul", "May"),  # (vérifié) Hongrie
    "UKR-Premier League": ("Ukrainian Premier League", "Aug", "May"),  # (vérifié) Ukraine
    "RUS-Premier League": ("Russian Premier League", "Jul", "May"),  # (vérifié) Russie
    "SRB-SuperLiga": ("Serbian SuperLiga", "Jul", "May"),  # (à vérifier) Serbie
    "CRO-HNL": ("Croatian Football League", "Jul", "May"),  # (à vérifier) Croatie
    "NOR-Eliteserien": ("Eliteserien", "Mar", "Nov"),  # (à vérifier) Norvège, saison calendaire
    "SWE-Allsvenskan": ("Allsvenskan", "Mar", "Nov"),  # (à vérifier) Suède, saison calendaire
}

# Charge le fichier existant (pour ne rien écraser) ou part d'un dictionnaire vide
existant = json.loads(CHEMIN.read_text(encoding="utf-8")) if CHEMIN.exists() else {}

for cle, (nom_fbref, debut, fin) in CHAMPIONNATS.items():  # parcourt chaque championnat à ajouter
    entree = existant.get(cle, {})  # reprend l'entrée existante si la clé y est déjà
    entree["FBref"] = nom_fbref  # nom de la compétition tel que FBref l'affiche
    entree["season_start"] = debut  # mois de début de saison (sert à décoder "2526", etc.)
    entree["season_end"] = fin  # mois de fin de saison
    existant[cle] = entree  # enregistre l'entrée dans le dictionnaire global

# Réécrit le fichier JSON (UTF-8 pour conserver les accents, indentation lisible)
CHEMIN.write_text(json.dumps(existant, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"{len(CHAMPIONNATS)} championnats ajoutés/mis à jour dans {CHEMIN}")  # confirmation
print("Liste des clés à copier dans 01_extraction_fbref.py :")  # rappel pour l'étape suivante
print(list(CHAMPIONNATS))  # affiche les clés
