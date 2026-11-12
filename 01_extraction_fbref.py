"""
01_extraction_fbref.py
Extrait les stats joueurs de FBref (via soccerdata) pour tous les championnats
choisis et les fusionne dans data/fbref_joueurs.csv.
Prérequis : pip install soccerdata   (installe aussi pandas, lxml, requests...)
Durée : plusieurs dizaines de minutes la 1re fois (FBref impose ~3 s entre requêtes),
puis quasi instantané grâce au cache de soccerdata.
"""
import os  # module standard : créer des dossiers
import pandas as pd  # manipulation de tableaux de données
import soccerdata as sd  # librairie qui scrape FBref et gère cache + limites de débit

# Championnats à extraire : "Big 5" + tous ceux ajoutés par 00_config_championnats.py
LIGUES = [
    "FRA-Ligue 1", "ENG-Premier League", "ESP-La Liga", "ITA-Serie A", "GER-Bundesliga",  # Big 5 (natifs)
    "FRA-Ligue 2", "ENG-Championship", "GER-2. Bundesliga", "ITA-Serie B", "ESP-Segunda Division",  # D2
    "NED-Eredivisie", "POR-Primeira Liga", "BEL-Pro League", "SCO-Premiership", "TUR-Super Lig",  # mineurs
    "AUT-Bundesliga", "SUI-Super League", "DEN-Superliga", "GRE-Super League", "CZE-First League",
    "POL-Ekstraklasa", "ROU-Liga I", "HUN-NB I", "UKR-Premier League", "RUS-Premier League",
    "SRB-SuperLiga", "CRO-HNL", "NOR-Eliteserien", "SWE-Allsvenskan",
]
# Saisons à extraire (format accepté par soccerdata). Ajoute "2026-2027" pour la saison en cours.
SAISONS = ["2024-2025", "2025-2026","2026-27"]
# Types de tables FBref à récupérer (les tables "avancées" vides depuis janv. 2026 seront ignorées)
STAT_TYPES = [
    "standard", "shooting", "passing", "passing_types",
    "goal_shot_creation", "defense", "possession", "misc", "playing_time",
]
# Colonnes qui identifient une ligne joueur de façon unique (sert de clé de fusion)
CLES = ["league", "season", "team", "player"]


def aplatir(df: pd.DataFrame) -> pd.DataFrame:
    """Transforme les colonnes à deux niveaux (MultiIndex) en noms simples 'Groupe_Stat'."""
    df = df.reset_index()  # remonte l'index (league, season, team, player) en colonnes normales
    cols = []  # liste qui contiendra les nouveaux noms de colonnes
    for c in df.columns:  # parcourt chaque colonne
        if isinstance(c, tuple):  # si le nom est un couple (groupe, stat)...
            # ...on le colle avec "_" en ignorant les morceaux vides ou "Unnamed"
            c = "_".join(str(x) for x in c if x and not str(x).startswith("Unnamed"))
        cols.append(c)  # ajoute le nom nettoyé
    df.columns = cols  # remplace les noms de colonnes
    return df  # renvoie le tableau aplati


def extraire_ligue(ligue: str) -> pd.DataFrame | None:
    """Récupère et fusionne toutes les tables d'UN championnat (None si échec total)."""
    fbref = sd.FBref(leagues=[ligue], seasons=SAISONS)  # scraper limité à ce championnat
    fusion = None  # tableau fusionné, vide au départ
    for st in STAT_TYPES:  # une table FBref après l'autre
        try:  # on isole chaque table : une erreur ne bloque pas les autres
            df = aplatir(fbref.read_player_season_stats(stat_type=st))  # télécharge + aplatit
        except Exception as e:  # table absente, nom de ligue invalide, blocage réseau...
            print(f"   [{ligue}] {st} ignorée : {type(e).__name__}")  # signale sans planter
            continue  # passe à la table suivante
        if df.empty:  # table téléchargée mais vide
            continue  # on l'ignore
        if fusion is None:  # première table valide : elle sert de base
            fusion = df
        else:  # tables suivantes : on ajoute seulement les colonnes nouvelles
            nouvelles = [c for c in df.columns if c in CLES or c not in fusion.columns]
            fusion = fusion.merge(df[nouvelles], on=CLES, how="outer")  # jointure sur la clé joueur
    return fusion  # tableau complet du championnat (ou None)


def main():
    os.makedirs("data", exist_ok=True)  # crée le dossier de sortie s'il n'existe pas
    morceaux = []  # un tableau par championnat réussi
    for ligue in LIGUES:  # boucle sur tous les championnats
        print(f"-> {ligue}")  # progression
        try:  # un nom de ligue erroné ne doit pas arrêter tout le script
            df = extraire_ligue(ligue)  # extraction du championnat
        except Exception as e:  # ex. championnat introuvable dans league_dict.json
            print(f"   ÉCHEC {ligue} : {type(e).__name__}: {e}")  # message d'erreur
            continue  # championnat suivant
        if df is not None and not df.empty:  # on garde seulement les extractions réussies
            morceaux.append(df)  # ajoute à la liste
    if not morceaux:  # rien n'a fonctionné
        raise SystemExit("Aucune donnée récupérée : vérifie réseau et noms de championnats.")
    total = pd.concat(morceaux, ignore_index=True)  # empile tous les championnats
    total.to_csv("data/fbref_joueurs.csv", index=False)  # sauvegarde au format CSV
    print(f"OK : {len(total)} lignes, {total.shape[1]} colonnes -> data/fbref_joueurs.csv")  # bilan
    print("Saisons trouvées :", sorted(total["season"].astype(str).unique()))  # utile pour le script 2


if __name__ == "__main__":  # exécute main() uniquement si on lance ce fichier directement
    main()
