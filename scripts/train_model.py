import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib
from datetime import datetime
import os
import sys
from pathlib import Path
from math import sqrt

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# === PARAMÈTRES ===
# Utiliser config.py si disponible, sinon fallback
try:
    from config import DATASET_PATH as DATASET_PATH_CONFIG, MODEL_PATH
    DATASET_PATH = DATASET_PATH_CONFIG
    MODEL_OUTPUT = MODEL_PATH
except ImportError:
    # Fallback: chercher dans les bons dossiers
    BASE_DIR = Path(__file__).parent.parent.resolve()
    DATASET_PATH = str(BASE_DIR / "dataset_ready_for_model.csv")
    model_path = BASE_DIR / "models" / "model_fraises_v2.pkl"
    root_path = BASE_DIR / "model_fraises_v2.pkl"
    MODEL_OUTPUT = str(model_path if model_path.parent.exists() else root_path)

print("🌱 Entraînement du modèle de prédiction de récolte...")

# === LECTURE DU DATASET ===
df = pd.read_csv(DATASET_PATH, parse_dates=["date"])

# Vérifications de base
if df.empty:
    raise ValueError("❌ Le dataset est vide.")
if "kg_par_rangee" not in df.columns:
    raise ValueError("❌ La colonne 'kg_par_rangee' est manquante dans le dataset.")

# === PRÉPARATION DES FEATURES ===
# Variables explicatives (input)
features = [
    "temp_mean", "temp_min", "temp_max", "rain_mm",
    "humidity", "sun_hours", "kg_par_rangee_prev_day"
]

# Ajouter nb_plants si présent dans le dataset
if "nb_plants" in df.columns:
    features.append("nb_plants")
    print("✅ Feature 'nb_plants' détectée et ajoutée au modèle.")

# Ajouter les features d'organisation hebdomadaire si présentes
if "jour_semaine" in df.columns:
    features.append("jour_semaine")
    print("✅ Feature 'jour_semaine' détectée et ajoutée au modèle.")
if "fraction_fraiseraie" in df.columns:
    features.append("fraction_fraiseraie")
    print("✅ Feature 'fraction_fraiseraie' détectée et ajoutée au modèle.")
if "jours_since_last_recolte" in df.columns:
    features.append("jours_since_last_recolte")
    print("✅ Feature 'jours_since_last_recolte' détectée et ajoutée au modèle.")
if "jours_since_last_recolte_globale" in df.columns:
    features.append("jours_since_last_recolte_globale")
    print("✅ Feature 'jours_since_last_recolte_globale' détectée et ajoutée au modèle.")

# Encodage simple des variables catégorielles
df = pd.get_dummies(df, columns=["parcelle", "variety"], drop_first=True)

# Colonnes finales pour X
X_cols = [col for col in features if col in df.columns] + \
         [col for col in df.columns if col.startswith("parcelle_") or col.startswith("variety_")]

# Jeu d'entraînement / test
X = df[X_cols]
y = df["kg_par_rangee"]

# Filtre les lignes sans valeurs complètes
X = X.replace([np.inf, -np.inf], np.nan).dropna()
y = y.loc[X.index]

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# === MODÈLE ===
model = RandomForestRegressor(
    n_estimators=300,
    max_depth=15,
    random_state=42,
    n_jobs=-1
)

# === ENTRAÎNEMENT ===
model.fit(X_train, y_train)
y_pred = model.predict(X_test)

# === ÉVALUATION ===
rmse = sqrt(mean_squared_error(y_test, y_pred))
r2 = r2_score(y_test, y_pred)
print(f"✅ Entraînement terminé : RMSE = {rmse:.2f} | R² = {r2:.3f}")

# === SAUVEGARDE ===
joblib.dump(model, MODEL_OUTPUT)
print(f"💾 Modèle sauvegardé sous : {MODEL_OUTPUT}")

# === ARCHIVAGE OPTIONNEL ===
date_tag = datetime.now().strftime("%Y-%m-%d")
archive_dir = "models_archive"
os.makedirs(archive_dir, exist_ok=True)
archive_path = os.path.join(archive_dir, f"model_fraises_v2_{date_tag}.pkl")
joblib.dump(model, archive_path)

print(f"📦 Modèle archivé : {archive_path}")
