"""
03_preparer_valeurs.py
Télécharge la table des joueurs du jeu de données ouvert "transfermarkt-datasets"
(David Cariboo) et produit data/valeurs.csv (colonnes : player, market_value_eur)
pour le script 02.
Prérequis : pandas (déjà installé). Aucune autre librairie.
ATTENTION : ce jeu de données est à jour au 6 juillet 2026 seulement (mises à jour
suspendues) : les valeurs correspondent donc à l'été 2026, pas à novembre 2026.
"""
import os  # module standard : créer le dossier de sortie
import urllib.error  # module standard : gérer les erreurs de téléchargement
import urllib.request  # module standard : télécharger un fichier
import pandas as pd  # lecture et traitement des tableaux

# URL publique du fichier players (compressé en gzip, pandas le décompresse seul)
URL = "https://pub-e682421888d945d684bcae8890b0ec20.r2.dev/data/players.csv.gz"
# Si le téléchargement automatique échoue : télécharge le fichier à la main dans ce
# dossier (même URL dans ton navigateur) et mets ici son nom, ex. "players.csv.gz".
FICHIER_LOCAL = None

# Dernière saison minimale pour garder un joueur (évite les joueurs retirés depuis longtemps)
SAISON_MIN = 2024


def main():
    os.makedirs("data", exist_ok=True)  # crée le dossier data si besoin
    source = FICHIER_LOCAL  # fichier local si renseigné
    if source is None:  # sinon on télécharge nous-mêmes le fichier
        source = "data/players.csv.gz"  # copie locale du fichier téléchargé
        print(f"Téléchargement de {URL} ...")  # information de progression
        # Certains serveurs refusent l'identité par défaut de Python : on se présente comme un navigateur
        req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r, open(source, "wb") as f:  # télécharge
                f.write(r.read())  # enregistre le fichier sur le disque
        except urllib.error.HTTPError as e:  # le serveur refuse toujours
            raise SystemExit(
                f"Téléchargement refusé (HTTP {e.code}). Ouvre {URL} dans ton navigateur, "
                "enregistre players.csv.gz dans ce dossier, puis mets FICHIER_LOCAL = \"players.csv.gz\" en haut du script."
            )
    print(f"Lecture de {source} ...")  # information de progression
    df = pd.read_csv(source)  # décompresse (gzip automatique) et charge la table
    print(f"{len(df)} joueurs, colonnes : {list(df.columns)}")  # permet de contrôler les colonnes

    # Vérifie que les deux colonnes indispensables existent
    for col in ("name", "market_value_in_eur"):
        if col not in df.columns:  # structure du fichier différente de celle attendue
            raise SystemExit(f"Colonne '{col}' absente : envoie-moi la liste de colonnes ci-dessus.")

    # Garde seulement les joueurs récents si la colonne last_season existe
    if "last_season" in df.columns:
        df = df[df["last_season"] >= SAISON_MIN]  # ex. dernière saison jouée >= 2024

    df = df.dropna(subset=["name", "market_value_in_eur"])  # supprime les joueurs sans valeur
    # Colonnes de sortie : on renomme pour correspondre à ce qu'attend le script 02
    sortie = df.rename(columns={"name": "player", "market_value_in_eur": "market_value_eur"})
    garder = ["player", "market_value_eur"]  # colonnes obligatoires
    # Colonnes optionnelles utiles pour vérifier les homonymes (si présentes)
    garder += [c for c in ("current_club_name", "date_of_birth", "position") if c in sortie.columns]
    sortie = sortie[garder]

    os.makedirs("data", exist_ok=True)  # crée le dossier data si besoin
    sortie.to_csv("data/valeurs.csv", index=False)  # sauvegarde au format CSV
    print(f"OK : {len(sortie)} joueurs -> data/valeurs.csv")  # bilan
    # Contrôle rapide : valeur de la cible du projet
    cible = sortie[sortie["player"].str.contains("Savanier", case=False, na=False)]
    print(cible.to_string(index=False) if not cible.empty else "Savanier non trouvé dans ce fichier.")


if __name__ == "__main__":  # exécute main() uniquement si on lance ce fichier directement
    main()
