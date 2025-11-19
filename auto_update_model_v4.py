import pandas as pd
import numpy as np
import joblib
import subprocess
from datetime import datetime
from pathlib import Path
import os
import sys

# Import de l'utilitaire PyInstaller pour gérer les chemins
try:
    from pyinstaller_utils import get_base_path, get_resource_path, get_script_path
except ImportError:
    def get_base_path():
        return Path(__file__).parent
    def get_resource_path(relative_path):
        return Path(__file__).parent / relative_path
    def get_script_path(script_name):
        return script_name

# === PARAMÈTRES ===
BASE_PATH = get_base_path()
EXCEL_PATH = str(get_resource_path("recoltes_fraises.xlsx"))
WEATHER_PATH = str(get_resource_path("meteo_dataset.csv"))
DATASET_PATH = str(BASE_PATH / "dataset_ready_for_model.csv")  # Créé dans le dossier de l'exécutable
MODEL_SCRIPT = get_script_path("train_model.py")
MODEL_OUTPUT = str(BASE_PATH / "model_fraises_v2.pkl")  # Sauvegardé dans le dossier de l'exécutable
ARCHIVE_DIR = BASE_PATH / "models_archive"  # Dans le dossier de l'exécutable
UPDATE_METEO_SCRIPT = get_script_path("update_meteo_dataset.py")

# === 0. MISE À JOUR DES DONNÉES MÉTÉO ===
print("🌤️ Vérification et mise à jour des données météo...")
python_exec = sys.executable
try:
    result = subprocess.run(
        [python_exec, UPDATE_METEO_SCRIPT],
        check=False,  # Ne pas lever d'exception si le script échoue
        capture_output=True,
        text=True
    )
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("⚠️ La mise à jour des données météo a échoué, mais on continue avec les données existantes...")
        if result.stderr:
            print(f"   Erreur : {result.stderr}")
except Exception as e:
    print(f"⚠️ Erreur lors de la mise à jour des données météo : {e}")
    print("   On continue avec les données existantes...")

# === 1. LECTURE ET FUSION ===
print("📘 Lecture du fichier maître des récoltes...")
# Utiliser data_loader pour compatibilité SQLite/Excel
try:
    from data_loader import load_recoltes_with_params, load_parametres, load_recolte_quotidienne, load_plants_par_annee
    USE_DATA_LOADER = True
except ImportError:
    USE_DATA_LOADER = False
    print("⚠️ Module data_loader non disponible, utilisation d'Excel uniquement")

if USE_DATA_LOADER:
    df_recoltes = load_recoltes_with_params()
    params = load_parametres()
else:
    df_recoltes = pd.read_excel(EXCEL_PATH, sheet_name="Recoltes", parse_dates=["date"])
    params = pd.read_excel(EXCEL_PATH, sheet_name="Paramètres")

if df_recoltes.empty:
    raise ValueError("❌ Le fichier 'Recoltes' est vide.")
if params.empty:
    raise ValueError("❌ L'onglet 'Paramètres' est vide.")

# Nettoyage des clés de jointure
# Note: pas besoin de parcelle dans Recoltes, chaque variété est associée à une parcelle dans Paramètres
for df in [df_recoltes, params]:
    if "variety" in df.columns:
        df["variety"] = df["variety"].astype(str).str.strip().str.lower()
    if "parcelle" in df.columns:
        df["parcelle"] = df["parcelle"].astype(str).str.strip().str.lower()

# Fusion sur variety uniquement (la parcelle est déduite depuis Paramètres)
df_recoltes = df_recoltes.merge(params, on=["variety"], how="left")


# Vérifie si plusieurs colonnes nb_rangees existent après fusion
if "nb_rangees_x" in df_recoltes.columns and "nb_rangees_y" in df_recoltes.columns:
    df_recoltes["nb_rangees"] = df_recoltes["nb_rangees_x"].fillna(df_recoltes["nb_rangees_y"])
    df_recoltes.drop(columns=["nb_rangees_x", "nb_rangees_y"], inplace=True)
elif "nb_rangees_x" in df_recoltes.columns:
    df_recoltes.rename(columns={"nb_rangees_x": "nb_rangees"}, inplace=True)
elif "nb_rangees_y" in df_recoltes.columns:
    df_recoltes.rename(columns={"nb_rangees_y": "nb_rangees"}, inplace=True)

# Vérification post-fusion
if "nb_rangees" not in df_recoltes.columns:
    raise ValueError("❌ Impossible de trouver la colonne 'nb_rangees' après fusion. Vérifie ton fichier Paramètres.")

# Gestion du cas où nb_rangees est vide/NaN
if df_recoltes["nb_rangees"].isna().any():
    missing = df_recoltes[df_recoltes["nb_rangees"].isna()][["variety"]].drop_duplicates()
    print("⚠️ Avertissement : certaines variétés n'ont pas de 'nb_rangees' dans 'Paramètres' :")
    print(missing.to_string(index=False))
    print("👉 Utilisation d'une valeur par défaut (10 rangées) pour ces variétés.")
    # Valeur par défaut si nb_rangees est vide
    df_recoltes["nb_rangees"] = df_recoltes["nb_rangees"].fillna(10)

# Vérification que la parcelle a bien été ajoutée depuis Paramètres
if "parcelle" not in df_recoltes.columns:
    raise ValueError("❌ La colonne 'parcelle' n'a pas été ajoutée depuis 'Paramètres'. Vérifie que chaque variété a une parcelle associée.")

# Nettoyage
df_recoltes = df_recoltes.dropna(subset=["date", "parcelle", "variety", "kg_total"])
df_recoltes["kg_total"] = df_recoltes["kg_total"].astype(float)
# Calcul de kg_par_rangee (gère le cas où nb_rangees pourrait être 0)
df_recoltes["kg_par_rangee"] = df_recoltes["kg_total"] / df_recoltes["nb_rangees"].replace(0, np.nan)
df_recoltes = df_recoltes.sort_values(["parcelle", "variety", "date"])
# Supprimer les lignes où kg_par_rangee est NaN (division par 0 ou nb_rangees manquant)
df_recoltes = df_recoltes.dropna(subset=["kg_par_rangee"])

# === AJOUT DES FEATURES LIÉES À L'ORGANISATION HEBDOMADAIRE ===
print("📅 Ajout des features d'organisation hebdomadaire des récoltes...")

# Jour de la semaine (0=Lundi, 6=Dimanche)
df_recoltes["jour_semaine"] = df_recoltes["date"].dt.dayofweek

# Charger les paramètres de récolte quotidienne
recolte_quotidienne = pd.DataFrame()  # Initialiser pour éviter les erreurs
try:
    if USE_DATA_LOADER:
        recolte_quotidienne = load_recolte_quotidienne()
    else:
        recolte_quotidienne = pd.read_excel(EXCEL_PATH, sheet_name="Recolte_quotidienne")
    if not recolte_quotidienne.empty:
        # Créer un mapping jour_semaine_num -> fraction_fraiseraie
        fraction_map = dict(zip(
            recolte_quotidienne["jour_semaine_num"],
            recolte_quotidienne["fraction_fraiseraie"]
        ))
        # Appliquer le mapping
        df_recoltes["fraction_fraiseraie"] = df_recoltes["jour_semaine"].map(fraction_map)
        print(f"✅ Paramètres de récolte quotidienne chargés depuis Excel ({len(recolte_quotidienne)} jours)")
    else:
        recolte_quotidienne = pd.DataFrame()  # Réinitialiser si vide
        raise ValueError("L'onglet 'Recolte_quotidienne' est vide")
except Exception as e:
    print(f"⚠️ Erreur lors de la lecture de 'Recolte_quotidienne' : {e}")
    print("👉 Utilisation des valeurs par défaut.")
    # Valeurs par défaut en cas d'erreur
    recolte_quotidienne = pd.DataFrame()  # S'assurer qu'elle est vide pour utiliser le fallback
    def get_fraction_fraiseraie(dayofweek):
        if dayofweek in [0, 1, 2]:  # Lundi, Mardi, Mercredi
            return 1/3
        elif dayofweek in [3, 4, 5]:  # Jeudi, Vendredi, Samedi
            return 1/2
        else:  # Dimanche
            return 0
    df_recoltes["fraction_fraiseraie"] = df_recoltes["jour_semaine"].apply(get_fraction_fraiseraie)

# Nombre de jours depuis la dernière récolte pour cette parcelle/variété
# IMPORTANT : Prise en compte de l'inertie de la récolte basée sur les paramètres de récolte quotidienne
# Pour chaque jour de récolte, la fraction récoltée n'a pas été récoltée depuis le dernier jour de récolte
# dans le cycle hebdomadaire (selon les paramètres de récolte quotidienne)

# Construire un mapping des jours de récolte depuis les paramètres
if not recolte_quotidienne.empty:
    # Identifier les jours de récolte (fraction > 0)
    jours_recolte = recolte_quotidienne[recolte_quotidienne["fraction_fraiseraie"] > 0].copy()
    jours_recolte = jours_recolte.sort_values("jour_semaine_num")
    jours_recolte_nums = sorted(jours_recolte["jour_semaine_num"].tolist())
    
    # Créer un mapping : pour chaque jour, trouver le dernier jour de récolte avant lui dans le cycle
    def find_last_harvest_day_before(current_day):
        """Trouve le dernier jour de récolte avant current_day dans le cycle hebdomadaire."""
        # Chercher dans les jours précédents de la semaine actuelle
        prev_days = [d for d in jours_recolte_nums if d < current_day]
        if prev_days:
            return max(prev_days)
        # Si pas de jour précédent dans la semaine, prendre le dernier jour de récolte de la semaine précédente
        if jours_recolte_nums:
            return max(jours_recolte_nums)
        return None
    
    def calculate_days_since_last_harvest_day(current_dayofweek, current_date, group):
        """Calcule les jours depuis le dernier jour de récolte dans le cycle hebdomadaire."""
        # Si ce n'est pas un jour de récolte, utiliser la logique standard
        if current_dayofweek not in jours_recolte_nums:
            # Chercher la dernière récolte précédente
            prev_recoltes = group[group["date"] < current_date]
            if not prev_recoltes.empty:
                last_recolte_date = prev_recoltes["date"].max()
                return (current_date - last_recolte_date).days
            return 0
        
        # Trouver le dernier jour de récolte avant ce jour dans le cycle
        last_harvest_day = find_last_harvest_day_before(current_dayofweek)
        
        if last_harvest_day is None:
            return 0
        
        # Calculer les jours depuis ce dernier jour de récolte
        # Si le dernier jour est dans la semaine actuelle (avant aujourd'hui)
        if last_harvest_day < current_dayofweek:
            days_since = current_dayofweek - last_harvest_day
            # Trouver la date du dernier jour de récolte dans l'historique
            last_harvest_date = current_date - pd.Timedelta(days=days_since)
            prev_recoltes = group[group["date"] <= last_harvest_date]
            if not prev_recoltes.empty:
                actual_last_date = prev_recoltes["date"].max()
                return (current_date - actual_last_date).days
            return days_since
        else:
            # Le dernier jour de récolte est dans la semaine précédente
            # Calculer les jours depuis ce jour de la semaine précédente
            days_back_to_last_harvest = (7 - last_harvest_day) + current_dayofweek
            last_harvest_date = current_date - pd.Timedelta(days=days_back_to_last_harvest)
            prev_recoltes = group[group["date"] <= last_harvest_date]
            if not prev_recoltes.empty:
                actual_last_date = prev_recoltes["date"].max()
                return (current_date - actual_last_date).days
            return days_back_to_last_harvest
    
    def calculate_jours_since_last_recolte_with_inertia(group):
        """Calcule les jours depuis la dernière récolte en tenant compte de l'inertie hebdomadaire."""
        group = group.sort_values("date")
        group = group.copy()
        group["jours_since_last_recolte"] = 0
        
        for i in range(len(group)):
            current_date = group.iloc[i]["date"]
            current_dayofweek = current_date.dayofweek  # 0=Lundi, 6=Dimanche
            
            days = calculate_days_since_last_harvest_day(current_dayofweek, current_date, group)
            group.iloc[i, group.columns.get_loc("jours_since_last_recolte")] = days
        
        return group
else:
    # Fallback : utiliser la logique par défaut si pas de paramètres
    def calculate_jours_since_last_recolte_with_inertia(group):
        """Calcule les jours depuis la dernière récolte (logique par défaut)."""
        group = group.sort_values("date")
        group = group.copy()
        group["jours_since_last_recolte"] = 0
        
        for i in range(1, len(group)):
            prev_date = group.iloc[i-1]["date"]
            current_date = group.iloc[i]["date"]
            group.iloc[i, group.columns.get_loc("jours_since_last_recolte")] = (current_date - prev_date).days
        
        return group

df_recoltes = df_recoltes.groupby(["parcelle", "variety"]).apply(calculate_jours_since_last_recolte_with_inertia).reset_index(drop=True)

# Pour gérer les cas où il n'y a pas eu de récolte le weekend, on calcule aussi
# le nombre de jours depuis la dernière récolte globale (toutes parcelles/variétés confondues)
# Utiliser la même logique que dans forecast_next3days_v3.py :
# Calculer les jours depuis la dernière date globale jusqu'à cette date
df_recoltes = df_recoltes.sort_values("date")
dates_uniques = sorted(df_recoltes["date"].unique())

def calculate_jours_since_last_recolte_globale(row):
    """Calcule les jours depuis la dernière récolte globale."""
    current_date = row["date"]
    # Trouver la dernière date avant la date actuelle
    prev_dates = [d for d in dates_uniques if d < current_date]
    if prev_dates:
        last_global_date = max(prev_dates)
        return (current_date - last_global_date).days
    else:
        return 0  # Première date = 0 jours

df_recoltes["jours_since_last_recolte_globale"] = df_recoltes.apply(calculate_jours_since_last_recolte_globale, axis=1)

df_recoltes["kg_par_rangee_prev_day"] = df_recoltes.groupby(["parcelle", "variety"])["kg_par_rangee"].shift(1)

print(f"📊 Données récoltes : {len(df_recoltes)} lignes, dernière date = {df_recoltes['date'].max().date()}")
print(f"   Jours de récolte : {sorted(df_recoltes['jour_semaine'].unique())} (0=Lundi, 6=Dimanche)")

# === 2. MÉTÉO ===
if not Path(WEATHER_PATH).exists():
    raise FileNotFoundError(f"❌ Fichier météo introuvable : {WEATHER_PATH}")

meteo = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
if meteo.empty:
    raise ValueError("❌ Le fichier météo est vide ou invalide.")

# Vérifie la cohérence temporelle
if df_recoltes["date"].min() < meteo["date"].min() or df_recoltes["date"].max() > meteo["date"].max():
    print("⚠️ Avertissement : certaines dates de récolte sont hors plage météo.")

dataset = pd.merge(df_recoltes, meteo, on="date", how="left")

# Vérification des NaN météo
if dataset[["temp_mean", "rain_mm", "sun_hours"]].isna().any().any():
    print("⚠️ Avertissement : des lignes contiennent des données météo manquantes.")

# === 2.5. INTÉGRATION DE PLANTS_PAR_ANNEE ===
print("🌱 Intégration des données de plants par année...")
try:
    if USE_DATA_LOADER:
        plants_par_annee = load_plants_par_annee()
    else:
        plants_par_annee = pd.read_excel(EXCEL_PATH, sheet_name="Plants_par_annee")
    if not plants_par_annee.empty:
        # Nettoyage des données
        plants_par_annee["variety"] = plants_par_annee["variety"].astype(str).str.strip().str.lower()
        plants_par_annee["Année"] = plants_par_annee["Année"].astype(int)
        
        # Extraction de l'année depuis la date
        dataset["year"] = dataset["date"].dt.year
        
        # Fusion avec Plants_par_annee sur variety et année
        dataset = dataset.merge(
            plants_par_annee[["variety", "Année", "Nb_plants"]],
            left_on=["variety", "year"],
            right_on=["variety", "Année"],
            how="left"
        )
        
        # Renommer la colonne pour plus de clarté
        if "Nb_plants" in dataset.columns:
            dataset.rename(columns={"Nb_plants": "nb_plants"}, inplace=True)
            dataset.drop(columns=["Année"], inplace=True, errors="ignore")
        
        # Gestion des valeurs manquantes
        if dataset["nb_plants"].isna().any():
            missing_count = dataset["nb_plants"].isna().sum()
            print(f"⚠️ Avertissement : {missing_count} lignes n'ont pas de 'nb_plants' (année/variété non trouvée).")
            print("👉 Utilisation d'une valeur par défaut (moyenne par variété) pour ces lignes.")
            # Valeur par défaut : moyenne par variété
            default_by_variety = dataset.groupby("variety")["nb_plants"].mean()
            for variety in default_by_variety.index:
                mask = (dataset["variety"] == variety) & (dataset["nb_plants"].isna())
                if not pd.isna(default_by_variety[variety]):
                    dataset.loc[mask, "nb_plants"] = default_by_variety[variety]
            
            # Si toujours NaN, utiliser la moyenne globale
            dataset["nb_plants"] = dataset["nb_plants"].fillna(dataset["nb_plants"].mean())
        
        print(f"✅ Données de plants intégrées : {len(plants_par_annee)} combinaisons variété/année")
        print(f"   Plage de nb_plants : {dataset['nb_plants'].min():.0f} à {dataset['nb_plants'].max():.0f}")
        # Supprimer la colonne temporaire "year" si elle existe
        dataset.drop(columns=["year"], inplace=True, errors="ignore")
    else:
        print("⚠️ L'onglet 'Plants_par_annee' est vide. Colonne 'nb_plants' non ajoutée.")
        dataset["nb_plants"] = np.nan
except Exception as e:
    print(f"⚠️ Erreur lors de la lecture de 'Plants_par_annee' : {e}")
    print("👉 Colonne 'nb_plants' non ajoutée.")
    dataset["nb_plants"] = np.nan

dataset.to_csv(DATASET_PATH, index=False)
print(f"✅ Dataset prêt : {DATASET_PATH} ({len(dataset)} lignes)")

# === 3. ENTRAÎNEMENT DU MODÈLE ===
print("🌲 Réentraînement du modèle...")
python_exec = sys.executable  # utilise le même interpréteur que celui du script
try:
    result = subprocess.run(
    [python_exec, MODEL_SCRIPT],
    check=True,
    capture_output=True,
    text=True
)
    print(result.stdout)
except subprocess.CalledProcessError as e:
    print("❌ Erreur pendant l'entraînement du modèle :")
    print(e.stderr)
    raise

# === 4. ARCHIVAGE ===
ARCHIVE_DIR.mkdir(exist_ok=True)
date_tag = datetime.now().strftime("%Y-%m-%d")

dataset_path_arch = ARCHIVE_DIR / f"dataset_ready_for_model_{date_tag}.csv"
model_path_arch = ARCHIVE_DIR / f"model_fraises_v2_{date_tag}.pkl"
log_path_arch = ARCHIVE_DIR / f"training_log_{date_tag}.txt"

dataset.to_csv(dataset_path_arch, index=False)
joblib.dump(joblib.load(MODEL_OUTPUT), model_path_arch)
with open(log_path_arch, "w") as f:
    f.write(result.stdout)

print(f"""
💾 Archivage effectué :
 - Dataset : {dataset_path_arch}
 - Modèle  : {model_path_arch}
 - Log     : {log_path_arch}
✅ Réentraînement terminé avec succès.
""")
