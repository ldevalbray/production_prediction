"""
Configuration centralisée pour l'application Pépinière Valbray
Utilise les variables d'environnement avec des valeurs par défaut
"""
import os
from pathlib import Path
from typing import Optional

# Chemin de base de l'application
BASE_DIR = Path(__file__).parent.resolve()

# === FICHIERS ET CHEMINS ===
# Chemins avec fallback pour compatibilité (cherche d'abord dans data/ et models/, puis à la racine)
def _get_data_path(filename):
    """Retourne le chemin d'un fichier de données avec fallback."""
    data_path = BASE_DIR / "data" / filename
    root_path = BASE_DIR / filename
    return str(data_path if data_path.exists() else root_path)

def _get_model_path(filename):
    """Retourne le chemin d'un modèle avec fallback."""
    model_path = BASE_DIR / "models" / filename
    root_path = BASE_DIR / filename
    return str(model_path if model_path.exists() else root_path)

DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "recoltes.db"))
EXCEL_PATH = os.getenv("EXCEL_PATH", _get_data_path("recoltes_fraises.xlsx"))
MODEL_PATH = os.getenv("MODEL_PATH", _get_model_path("model_fraises_v2.pkl"))
WEATHER_PATH = os.getenv("WEATHER_PATH", _get_data_path("meteo_dataset.csv"))
DATASET_PATH = os.getenv("DATASET_PATH", str(BASE_DIR / "dataset_ready_for_model.csv"))
FORECASTS_DIR = Path(os.getenv("FORECASTS_DIR", str(BASE_DIR / "forecasts")))
ARCHIVE_DIR = Path(os.getenv("ARCHIVE_DIR", str(BASE_DIR / "models" / "models_archive")))
LAST_RUN_FILE = os.getenv("LAST_RUN_FILE", str(BASE_DIR / "last_runs.json"))

# === COORDONNÉES GPS ===
LAT = float(os.getenv("LAT", "43.12"))  # Hyères par défaut
LON = float(os.getenv("LON", "6.14"))
TIMEZONE = os.getenv("TIMEZONE", "Europe/Paris")
FORECAST_DAYS = int(os.getenv("FORECAST_DAYS", "3"))

# === CONFIGURATION FLASK ===
FLASK_HOST = os.getenv("FLASK_HOST", "127.0.0.1")
FLASK_PORT = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "False").lower() == "true"

# === CONFIGURATION API ===
API_BASE_URL = os.getenv("API_BASE_URL", f"http://{FLASK_HOST}:{FLASK_PORT}/api")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")  # Liste d'origines autorisées

# === CONFIGURATION MODÈLE ML ===
MODEL_UPDATE_DELAY = int(os.getenv("MODEL_AUTO_UPDATE_DELAY", "30"))  # secondes
MODEL_SCRIPT = os.getenv("MODEL_SCRIPT", "train_model.py")
UPDATE_METEO_SCRIPT = os.getenv("UPDATE_METEO_SCRIPT", "update_meteo_dataset.py")

# === CONFIGURATION LOGGING ===
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", str(BASE_DIR / "app.log"))
LOG_FORMAT = os.getenv(
    "LOG_FORMAT",
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

# === CONFIGURATION CACHE ===
CACHE_ENABLED = os.getenv("CACHE_ENABLED", "True").lower() == "true"
CACHE_TTL = int(os.getenv("CACHE_TTL", "300"))  # 5 minutes par défaut

# === SÉCURITÉ ===
SECRET_KEY = os.getenv("SECRET_KEY", "change-me-in-production")  # ⚠️ À changer en production
MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", "16777216"))  # 16MB

# === VALIDATION ===
MAX_VARIETY_LENGTH = int(os.getenv("MAX_VARIETY_LENGTH", "50"))
MAX_PARCelle_LENGTH = int(os.getenv("MAX_PARCelle_LENGTH", "50"))
MAX_COMMENT_LENGTH = int(os.getenv("MAX_COMMENT_LENGTH", "500"))
MIN_KG_TOTAL = float(os.getenv("MIN_KG_TOTAL", "0"))
MAX_KG_TOTAL = float(os.getenv("MAX_KG_TOTAL", "10000"))  # Limite raisonnable

# Créer les dossiers nécessaires
FORECASTS_DIR.mkdir(exist_ok=True)
ARCHIVE_DIR.mkdir(exist_ok=True)

