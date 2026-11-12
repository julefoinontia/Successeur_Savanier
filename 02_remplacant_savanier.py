"""
02_remplacant_savanier.py
Cherche les milieux les plus proches du profil de Téji Savanier valant < 6 M€.
Prérequis : pip install scikit-learn   (pandas, numpy, matplotlib supposés installés)
Entrées  : data/fbref_joueurs.csv (script 01) et data/valeurs.csv (colonnes : player, market_value_eur)
Sorties  : data/classement_remplacants.csv et data/radar.png
"""
import unicodedata  # module standard : retirer les accents des noms
from difflib import get_close_matches  # module standard : appariement approximatif de noms

import matplotlib.pyplot as plt  # tracé du radar
import numpy as np  # calcul numérique
import pandas as pd  # tableaux de données
from sklearn.decomposition import PCA  # réduction de dimension (stats corrélées)
from sklearn.metrics.pairwise import cosine_similarity  # mesure de proximité de profils
from sklearn.preprocessing import StandardScaler  # mise à la même échelle (moyenne 0, écart-type 1)

CIBLE = "Téji Savanier"  # joueur à remplacer
# Codes de saison tels que soccerdata les écrit : "2526" = 2025-26 ; "2026" = saison calendaire 2026
SAISONS_RETENUES = {"2526", "2026", "2627", "2026"}
MINUTES_MIN = 300  # minutes minimum pour que les stats par 90 min soient fiables
VALEUR_MAX = 6_000_000  # plafond de valeur marchande en euros
POSTE = "MF"  # code FBref du poste (MF = milieu ; GK, DF, FW existent aussi)
TOP_N = 15  # taille du classement final
# Mots-clés de colonnes à exclure des variables d'analyse (identité, temps de jeu, résultats d'équipe)
GROUPES_EXCLUS = ("per 90", "team success", "playing time")
STATS_EXCLUES = {"age", "born", "mp", "starts", "min", "90s", "rk", "mn/mp", "min%", "compl", "subs", "unsub"}


def norm(s: str) -> str:
    """Normalise un nom : sans accents, minuscules, sans tirets ni espaces en double."""
    s = unicodedata.normalize("NFKD", str(s)).encode("ascii", "ignore").decode()  # supprime les accents
    return " ".join(s.lower().replace("-", " ").split())  # minuscules + espaces propres


def preparer_features(df: pd.DataFrame) -> pd.DataFrame:
    """Construit la matrice de stats : compteurs ramenés à 90 min, pourcentages conservés."""
    n90 = df["minutes"] / 90  # nombre de "90 minutes" jouées par joueur
    feats = {}  # dictionnaire nom_de_variable -> série de valeurs
    for c in df.select_dtypes(include=np.number).columns:  # uniquement les colonnes numériques
        groupe = c.split("_")[0].lower()  # partie avant "_" (ex. "Performance")
        stat = c.split("_")[-1].lower()  # partie après "_" (ex. "Gls")
        if c in ("minutes", "valeur_eur"):  # colonnes que j'ai créées moi-même
            continue  # ne sont pas des stats de jeu
        if any(g in groupe for g in GROUPES_EXCLUS) or stat in STATS_EXCLUES:  # colonnes à écarter
            continue
        if "%" in c:  # un pourcentage est déjà normalisé
            feats[c] = df[c]  # on le garde tel quel
        else:  # un compteur brut (tacles, passes...)
            feats[f"{c}/90"] = df[c] / n90  # on le ramène par 90 minutes
    X = pd.DataFrame(feats, index=df.index)  # assemble en tableau
    X = X.loc[:, X.isna().mean() < 0.3]  # retire les colonnes vides à plus de 30 %
    X = X.fillna(X.median())  # comble les trous restants avec la médiane
    return X.loc[:, X.std() > 0]  # retire les colonnes constantes (inutiles)


def main():
    df_all = pd.read_csv("data/fbref_joueurs.csv")  # charge toutes les données extraites
    df_all["season"] = df_all["season"].astype(str)  # codes de saison en texte
    # Colonne des minutes jouées (le nom exact dépend de l'aplatissement)
    col_min = next(c for c in ("Playing Time_Min", "Min") if c in df_all.columns)
    # Convertit en nombre (retire les virgules de milliers type "1,234")
    df_all["minutes"] = pd.to_numeric(df_all[col_min].astype(str).str.replace(",", ""), errors="coerce")

    # --- Valeurs marchandes (Transfermarkt) et appariement avec les noms FBref
    val = pd.read_csv("data/valeurs.csv")  # fichier player, market_value_eur
    val["k"] = val["player"].map(norm)  # clé normalisée de chaque nom
    val = val.sort_values("market_value_eur", ascending=False).drop_duplicates("k")  # 1 ligne par nom
    dico_val = dict(zip(val["k"], val["market_value_eur"]))  # clé -> valeur
    # Index par nom de famille (dernier mot) : la recherche approchée ne compare qu'avec les homonymes
    par_famille = {}  # nom de famille -> liste de clés Transfermarkt
    for k in dico_val:  # parcourt toutes les clés normalisées
        par_famille.setdefault(k.split()[-1], []).append(k)  # regroupe par dernier mot

    def valeur(nom):  # trouve la valeur marchande d'un joueur FBref
        k = norm(nom)  # nom normalisé du joueur FBref
        if k in dico_val:  # 1) correspondance exacte : instantanée
            return dico_val[k]
        candidats = par_famille.get(k.split()[-1], [])  # 2) sinon : seulement les mêmes noms de famille
        m = get_close_matches(k, candidats, n=1, cutoff=0.88)  # meilleur nom approchant (≥ 88 %)
        return dico_val[m[0]] if m else np.nan  # NaN si aucun nom ne correspond
    print("Appariement des valeurs marchandes...")  # progression

    # --- Joueurs candidats : bonnes saisons, bon poste, assez de minutes
    pool = df_all[df_all["season"].isin(SAISONS_RETENUES)]  # saisons retenues
    pool = pool[pool["pos"].astype(str).str.contains(POSTE) & (pool["minutes"] >= MINUTES_MIN)]

    # --- Ligne de la cible : sa saison la plus récente avec assez de minutes (même hors saisons retenues)
    lignes_cible = df_all[(df_all["player"].map(norm) == norm(CIBLE)) & (df_all["minutes"] >= MINUTES_MIN)]
    if lignes_cible.empty:  # cible introuvable
        print("Saisons disponibles :", sorted(df_all["season"].unique()))  # aide au diagnostic
        raise SystemExit(f"{CIBLE} introuvable (championnat non extrait, minutes ou orthographe ?)")
    ligne_cible = lignes_cible.sort_values("season").iloc[[-1]]  # saison la plus récente
    cles_id = ["league", "season", "team", "player"]  # identifiant unique d'une ligne
    pool = pd.concat([pool, ligne_cible]).drop_duplicates(subset=cles_id).reset_index(drop=True)
    pool["valeur_eur"] = pool["player"].map(valeur)  # ajoute la valeur marchande à chaque joueur
    print(f"{len(pool)} candidats, dont {pool['valeur_eur'].notna().sum()} avec une valeur trouvée")  # contrôle

    X = preparer_features(pool)  # matrice de variables par 90 minutes
    print(f"{len(pool)} joueurs, {X.shape[1]} variables")  # contrôle de taille

    i = pool.index[pool["player"].map(norm) == norm(CIBLE)][0]  # position de la cible dans le tableau

    # --- Similarité : standardisation -> ACP (90 % de variance) -> similarité cosinus
    Z = StandardScaler().fit_transform(X)  # chaque variable : moyenne 0, écart-type 1
    Z = PCA(n_components=0.90, random_state=0).fit_transform(Z)  # garde les axes expliquant 90 % de la variance
    pool["similarite"] = cosine_similarity(Z[[i]], Z)[0]  # proximité de chaque joueur avec la cible (1 = identique)

    # --- Filtre valeur < 6 M€, exclusion de la cible, tri par similarité
    res = pool[(pool.index != i) & (pool["valeur_eur"] < VALEUR_MAX)]  # NaN exclus automatiquement
    res = res.sort_values("similarite", ascending=False).head(TOP_N)  # meilleurs profils
    cols = ["player", "team", "league", "season", "age", "valeur_eur", "similarite"]  # colonnes à afficher
    sortie = res[[c for c in cols if c in res.columns]]  # garde celles qui existent
    print(sortie.to_string(index=False))  # affiche le classement
    sortie.to_csv("data/classement_remplacants.csv", index=False)  # sauvegarde

    # --- Radar : Joueur contre le top 3, sur les 8 stats où il se distingue le plus
    pct = X.rank(pct=True) * 100  # percentile (0-100) de chaque joueur pour chaque stat
    z_cible = ((X.loc[i] - X.mean()) / X.std()).abs()  # écart du joueur à la moyenne, par stat
    axes = z_cible.sort_values(ascending=False).index[:8]  # les 8 stats les plus marquantes
    angles = np.linspace(0, 2 * np.pi, len(axes), endpoint=False).tolist() + [0]  # angles + retour au départ
    fig, ax = plt.subplots(subplot_kw={"polar": True}, figsize=(7, 7))  # figure en coordonnées polaires
    for j in [i, *res.head(3).index]:  # cible puis les 3 meilleurs candidats
        v = pct.loc[j, axes].tolist() + [pct.loc[j, axes[0]]]  # valeurs + point de fermeture
        ax.plot(angles, v, label=pool.loc[j, "player"])  # trace le contour
        ax.fill(angles, v, alpha=0.08)  # remplit légèrement
    ax.set_xticks(angles[:-1])  # positions des étiquettes
    ax.set_xticklabels(axes, fontsize=7)  # noms des stats
    ax.set_ylim(0, 100)  # échelle de percentiles
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))  # légende hors du cercle
    plt.tight_layout()  # ajuste les marges
    plt.savefig("data/radar.png", dpi=150)  # enregistre l'image
    print("Fichiers : data/classement_remplacants.csv, data/radar.png")  # bilan


if __name__ == "__main__":  # exécute main() uniquement si on lance ce fichier directement
    main()
