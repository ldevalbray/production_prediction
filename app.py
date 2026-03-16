"""
Backend Flask pour l'interface web de la Pépinière Valbray
"""
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
import subprocess
import sys
import json
import os
from datetime import datetime
from pathlib import Path
import threading
import pandas as pd
from threading import Timer
import logging
import atexit
import signal

try:
    import requests
except ImportError:
    requests = None

# Gestion du splash screen PyInstaller
try:
    import pyi_splash  # type: ignore
except Exception:
    pyi_splash = None


def splash_is_active():
    """Retourne True si le splash PyInstaller est affiché."""
    if not pyi_splash:
        return False
    try:
        # Vérifier si l'IPC du splash est disponible
        if hasattr(pyi_splash, "is_alive"):
            return pyi_splash.is_alive()
        # Fallback: essayer d'accéder à un attribut pour voir si le module est initialisé
        return hasattr(pyi_splash, "update_text")
    except (KeyError, AttributeError, Exception):
        # Si l'IPC n'est pas disponible (KeyError: '_PYI_SPLASH_IPC'), le splash n'est pas actif
        return False


def splash_update(message):
    """Met à jour le texte du splash si disponible."""
    if not pyi_splash:
        return
    try:
        if splash_is_active():
            pyi_splash.update_text(message)
    except (KeyError, AttributeError, Exception):
        # Ignorer silencieusement si le splash n'est pas disponible
        pass


def splash_close():
    """Ferme le splash si encore affiché."""
    if not pyi_splash:
        return
    try:
        if splash_is_active():
            pyi_splash.close()
    except (KeyError, AttributeError, Exception):
        # Ignorer silencieusement si le splash n'est pas disponible
        pass

# Configuration du logging
try:
    from logger_config import setup_logging, logger
    setup_logging()
except ImportError:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)

# Import des validateurs
try:
    from validators import (
        ValidationError, validate_variety, validate_parcelle, validate_date,
        validate_kg_total, validate_nb_rangees, validate_commentaires,
        validate_annee, validate_nb_plants, validate_fraction_fraiseraie, validate_id
    )
except ImportError:
    logger.warning("Module validators non disponible, validation désactivée")
    ValidationError = Exception
    # Fonctions de validation par défaut (pass-through)
    def validate_variety(v): return v
    def validate_parcelle(v): return v
    def validate_date(v): return v
    def validate_kg_total(v): return v
    def validate_nb_rangees(v): return v or 10
    def validate_commentaires(v): return v
    def validate_annee(v): return v
    def validate_nb_plants(v): return v
    def validate_fraction_fraiseraie(v): return v
    def validate_id(v): return v

# Import du module de base de données
try:
    from database import (
        init_database, get_parametres, add_parametre, update_parametre, delete_parametre,
        get_recoltes, add_recolte, update_recolte, delete_recolte,
        get_jour_courant, set_jour_courant, clear_jour_courant,
        get_plants_par_annee, set_plants_par_annee,
        get_recolte_quotidienne, set_recolte_quotidienne,
        export_to_excel,
        get_forecasts, get_latest_forecast, get_latest_forecast_date,
        export_forecast_to_excel, delete_forecast
    )
    DB_AVAILABLE = True
except ImportError:
    DB_AVAILABLE = False
    print("⚠️ Module database.py non disponible, utilisation d'Excel uniquement")

# Import de l'utilitaire PyInstaller
try:
    from pyinstaller_utils import is_pyinstaller, get_script_path, get_resource_path, get_base_path
except ImportError:
    def is_pyinstaller():
        return False
    def get_script_path(script_name):
        script_path = (Path(__file__).parent / "scripts" / script_name).resolve()
        return str(script_path) if script_path.exists() else script_name
    def get_resource_path(relative_path):
        return Path(__file__).parent / relative_path
    def get_base_path():
        return Path(__file__).parent

# Import du gestionnaire d'icône système
try:
    from system_tray import SystemTrayManager
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    logger.warning("Module system_tray non disponible, l'icône système ne sera pas créée")

# Déterminer le chemin du frontend (gestion PyInstaller)
if is_pyinstaller():
    frontend_path = get_resource_path('frontend/build')
else:
    frontend_path = Path(__file__).parent / 'frontend' / 'build'

if splash_is_active():
    splash_update("Initialisation du serveur Flask...")

app = Flask(__name__, static_folder=str(frontend_path), static_url_path='')

# Configuration CORS
try:
    from config import CORS_ORIGINS, ensure_directories
    # Créer les dossiers nécessaires au démarrage (après l'import de config)
    ensure_directories()
    if CORS_ORIGINS == ["*"]:
        CORS(app)
    else:
        CORS(app, origins=CORS_ORIGINS)
except ImportError:
    CORS(app)  # Par défaut, autoriser toutes les origines

# Handler d'erreurs global
@app.errorhandler(ValidationError)
def handle_validation_error(e):
    """Gère les erreurs de validation."""
    logger.warning(f"Erreur de validation : {e}")
    return jsonify({"error": str(e)}), 400

@app.errorhandler(Exception)
def handle_generic_error(e):
    """Gère les erreurs génériques."""
    logger.error(f"Erreur non gérée : {e}", exc_info=True)
    return jsonify({"error": "Une erreur interne est survenue"}), 500

# Configuration - Utiliser config.py pour les chemins (cohérent avec le reste de l'application)
try:
    from config import LAST_RUN_FILE, EXCEL_PATH, FORECASTS_DIR, BASE_DIR
    BASE_PATH = BASE_DIR
except ImportError:
    # Fallback si config n'est pas disponible
    BASE_PATH = get_base_path()
    LAST_RUN_FILE = str(BASE_PATH / "last_runs.json")
    EXCEL_PATH = str(BASE_PATH / "recoltes_fraises.xlsx")
    FORECASTS_DIR = str(BASE_PATH / "forecasts")
SERVER_HOST = os.environ.get("PEPINIERE_HOST", "127.0.0.1")
SERVER_PORT = int(os.environ.get("PEPINIERE_PORT", "5000"))
SERVER_BASE_URL = os.environ.get("PEPINIERE_BASE_URL", f"http://{SERVER_HOST}:{SERVER_PORT}")

# Créer le dossier forecasts s'il n'existe pas
Path(FORECASTS_DIR).mkdir(parents=True, exist_ok=True)

if splash_is_active():
    splash_update("Chargement des modules applicatifs...")

# État global pour éviter les exécutions simultanées
script_running = False
script_status = {"running": False, "mode": None, "output": []}
model_update_timer = None  # Timer pour la mise à jour différée du modèle
MODEL_AUTO_UPDATE_DELAY = int(os.environ.get('MODEL_AUTO_UPDATE_DELAY', 30))  # 30 secondes par défaut

# Stream personnalisé pour capturer les logs en temps réel
class RealtimeOutputCapture:
    """Classe pour capturer la sortie en temps réel et l'ajouter à script_status."""
    def __init__(self, max_lines=100):
        self.max_lines = max_lines
        self.buffer = []
    
    def write(self, text):
        """Écrit dans le buffer et met à jour script_status."""
        if text and text.strip():
            # Séparer les lignes
            lines = text.rstrip().split('\n')
            for line in lines:
                if line.strip():
                    self.buffer.append(line.strip())
                    # Garder seulement les dernières lignes
                    if len(self.buffer) > self.max_lines:
                        self.buffer.pop(0)
                    # Mettre à jour script_status en temps réel
                    script_status["output"] = self.buffer.copy()
    
    def flush(self):
        """Méthode requise pour les streams."""
        pass
    
    def getvalue(self):
        """Retourne tout le contenu du buffer."""
        return '\n'.join(self.buffer)

# Handler personnalisé pour capturer les logs du module logging
class RealtimeLogHandler(logging.Handler):
    """Handler pour capturer les logs du module logging en temps réel."""
    def __init__(self, output_capture):
        super().__init__()
        self.output_capture = output_capture
    
    def emit(self, record):
        """Émet un log et l'ajoute à la capture."""
        try:
            msg = self.format(record)
            self.output_capture.write(msg)
        except Exception:
            pass  # Ignorer les erreurs de logging

def safe_load_json(p):
    """Charge un fichier JSON de manière sécurisée."""
    if not Path(p).exists():
        return {}
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def save_last_run(mode, status="✅ Succès"):
    """Sauvegarde la dernière exécution."""
    d = safe_load_json(LAST_RUN_FILE)
    d[mode] = {
        "time": datetime.now().strftime("%d %b %H:%M"),
        "status": status
    }
    with open(LAST_RUN_FILE, 'w', encoding='utf-8') as f:
        json.dump(d, f, indent=2, ensure_ascii=False)


def is_server_already_running(url=None, timeout=1.0):
    """Retourne True uniquement si une instance Pépinière répond déjà."""
    if url is None:
        url = f"{SERVER_BASE_URL}/api/status"

    def _looks_like_pepiniere_status(payload):
        return isinstance(payload, dict) and ("scriptRunning" in payload or "lastRuns" in payload)

    # Essayer d'abord avec requests si disponible
    if requests:
        try:
            response = requests.get(url, timeout=timeout)
            if not response.ok:
                return False
            try:
                return _looks_like_pepiniere_status(response.json())
            except Exception:
                return False
        except Exception:
            pass
    
    # Fallback: utiliser urllib si requests n'est pas disponible
    try:
        import urllib.request
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status != 200:
                return False
            raw = response.read().decode("utf-8", errors="ignore")
            payload = json.loads(raw)
            return _looks_like_pepiniere_status(payload)
    except Exception:
        pass

    return False

def is_port_in_use(host, port, timeout=0.3):
    """Retourne True si un port TCP est déjà occupé."""
    try:
        import socket
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            return sock.connect_ex((host, int(port))) == 0
    except Exception:
        return False

def find_available_port(host, start_port, max_tries=20):
    """Trouve un port libre à partir de start_port."""
    for port in range(int(start_port), int(start_port) + int(max_tries)):
        if not is_port_in_use(host, port):
            return port
    return None

def set_server_binding(host, port):
    """Met à jour la config runtime du serveur et l'environnement associé."""
    global SERVER_HOST, SERVER_PORT, SERVER_BASE_URL
    SERVER_HOST = host
    SERVER_PORT = int(port)
    SERVER_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    os.environ["PEPINIERE_HOST"] = SERVER_HOST
    os.environ["PEPINIERE_PORT"] = str(SERVER_PORT)
    os.environ["PEPINIERE_BASE_URL"] = SERVER_BASE_URL


def trigger_model_update_async(delay=MODEL_AUTO_UPDATE_DELAY):
    """
    Déclenche la mise à jour du modèle après un délai.
    Le délai permet d'éviter plusieurs mises à jour si plusieurs modifications sont faites rapidement.
    """
    global model_update_timer, script_running
    
    # Ne pas déclencher si une mise à jour manuelle est en cours
    if script_running:
        return
    
    # Annuler le timer précédent si une nouvelle modification arrive
    if model_update_timer:
        model_update_timer.cancel()
    
    def update_worker():
        """Fonction qui exécute la mise à jour du modèle."""
        global script_running, model_update_timer
        if script_running:
            return
        
        script_running = True
        model_update_timer = None  # Réinitialiser le timer
        
        try:
            print("🔄 Mise à jour automatique du modèle déclenchée...")
            script_path = get_script_path("run_daily_cycle.py")
            # Définir le répertoire de travail sur le dossier de l'exécutable
            cwd = str(BASE_PATH) if is_pyinstaller() else None
            result = subprocess.run(
                [sys.executable, script_path, "--mode", "update"],
                check=False,  # Ne pas lever d'exception si ça échoue
                capture_output=True,
                text=True,
                timeout=600,  # Timeout de 10 minutes
                cwd=cwd
            )
            if result.returncode == 0:
                print("✅ Mise à jour automatique du modèle terminée avec succès")
            else:
                print(f"⚠️ Mise à jour automatique du modèle échouée : {result.stderr[:200]}")
        except subprocess.TimeoutExpired:
            print("⚠️ Mise à jour automatique du modèle : timeout (10 minutes)")
        except Exception as e:
            print(f"⚠️ Erreur lors de la mise à jour automatique du modèle : {e}")
        finally:
            script_running = False
    
    # Programmer la mise à jour après le délai
    model_update_timer = Timer(delay, update_worker)
    model_update_timer.start()
    print(f"⏱️ Mise à jour du modèle programmée dans {delay} secondes...")

@app.route('/api/status', methods=['GET'])
def get_status():
    """Retourne le statut actuel de l'application."""
    last_runs = safe_load_json(LAST_RUN_FILE)
    return jsonify({
        "lastRuns": last_runs,
        "scriptRunning": script_status["running"],
        "scriptMode": script_status["mode"]
    })

@app.route('/api/run', methods=['POST'])
def run_script():
    """Exécute un script en mode forecast ou update."""
    global script_running, script_status
    
    if script_running:
        return jsonify({"error": "Une opération est déjà en cours."}), 400
    
    data = request.json
    mode = data.get('mode')
    
    if mode not in ['forecast', 'update']:
        return jsonify({"error": "Mode invalide"}), 400
    
    script_running = True
    script_status = {
        "running": True,
        "mode": mode,
        "output": []  # Réinitialiser les logs au début
    }
    
    def worker():
        global script_running, script_status
        ok = True
        err = ""
        output_capture = RealtimeOutputCapture(max_lines=100)
        
        try:
            # Dans PyInstaller, importer directement le module au lieu d'utiliser subprocess
            if is_pyinstaller():
                import importlib.util
                from contextlib import redirect_stdout, redirect_stderr
                
                script_path = get_script_path("run_daily_cycle.py")
                if Path(script_path).exists():
                    # Sauvegarder les arguments sys.argv
                    old_argv = sys.argv.copy()
                    sys.argv = [script_path, "--mode", mode]
                    
                    # Sauvegarder les streams originaux
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    
                    # Sauvegarder les handlers du logger
                    root_logger = logging.getLogger()
                    old_handlers = root_logger.handlers.copy()
                    log_handler = None
                    
                    try:
                        # Rediriger stdout et stderr vers notre capture en temps réel
                        sys.stdout = output_capture
                        sys.stderr = output_capture
                        
                        # Ajouter un handler personnalisé pour capturer les logs
                        log_handler = RealtimeLogHandler(output_capture)
                        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
                        root_logger.addHandler(log_handler)
                        
                        # Charger et exécuter le module
                        spec = importlib.util.spec_from_file_location(
                            "run_daily_cycle",
                            script_path
                        )
                        if spec and spec.loader:
                            module = importlib.util.module_from_spec(spec)
                            spec.loader.exec_module(module)
                    finally:
                        # Retirer le handler personnalisé
                        if log_handler:
                            root_logger.removeHandler(log_handler)
                        # Restaurer les streams
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
                        # Restaurer sys.argv
                        sys.argv = old_argv
                else:
                    ok = False
                    err = f"Script introuvable : {script_path}"
                    output_capture.write(f"Erreur : {err}")
            else:
                # Méthode normale avec subprocess (développement)
                script_path = get_script_path("run_daily_cycle.py")
                cwd = str(BASE_PATH) if is_pyinstaller() else None
                process = subprocess.Popen(
                    [sys.executable, script_path, "--mode", mode],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    universal_newlines=True,
                    cwd=cwd
                )
                
                for line in process.stdout:
                    if line.strip():
                        output_capture.write(line)
                
                process.wait()
                if process.returncode != 0:
                    ok = False
                    err_lines = output_capture.buffer[-10:] if len(output_capture.buffer) > 10 else output_capture.buffer
                    err = "\n".join(err_lines)
        except Exception as e:
            ok = False
            err = str(e)
            import traceback
            output_capture.write(f"Erreur : {err}")
            output_capture.write(traceback.format_exc())
        
        script_running = False
        script_status["running"] = False
        script_status["mode"] = None  # Réinitialiser le mode après la fin du script
        
        if ok:
            save_last_run(mode, "✅ Succès")
        else:
            save_last_run(mode, "❌ Erreur")
    
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    
    return jsonify({"message": f"Script {mode} démarré", "status": "started"})

@app.route('/api/script-output', methods=['GET'])
def get_script_output():
    """Retourne la sortie du script en cours d'exécution."""
    return jsonify({
        "running": script_status["running"],
        "mode": script_status["mode"],
        "output": script_status["output"]
    })

@app.route('/api/files/excel', methods=['GET'])
def get_excel_path():
    """Retourne le chemin du fichier Excel."""
    path = Path(EXCEL_PATH).resolve()
    return jsonify({
        "exists": path.exists(),
        "path": str(path),
        "name": path.name
    })

@app.route('/api/files/forecasts', methods=['GET'])
def get_forecasts_dir():
    """Retourne les informations sur le dossier des prévisions."""
    path = Path(FORECASTS_DIR).resolve()
    files = []
    if path.exists() and path.is_dir():
        files = [f.name for f in path.iterdir() if f.is_file()]
    return jsonify({
        "exists": path.exists(),
        "path": str(path),
        "files": sorted(files, reverse=True)[:10]  # Les 10 plus récents
    })

@app.route('/api/files/open', methods=['POST'])
def open_file():
    """Ouvre un fichier ou dossier."""
    data = request.json
    file_path = data.get('path')
    
    if not file_path:
        return jsonify({"error": "Chemin manquant"}), 400
    
    p = Path(file_path).resolve()
    if not p.exists():
        return jsonify({"error": f"{p} introuvable"}), 404
    
    try:
        if sys.platform.startswith("darwin"):
            os.system(f"open '{p}' &")
        elif os.name == "nt":
            os.startfile(str(p))
        else:
            os.system(f"xdg-open '{p}' &")
        return jsonify({"message": f"Ouverture de {p.name}"})
    except Exception as e:
        return jsonify({"error": f"Impossible d'ouvrir {file_path}: {e}"}), 500

@app.route('/api/forecasts/list', methods=['GET'])
def list_forecasts():
    """Liste toutes les prévisions disponibles depuis la base de données."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        # Récupérer toutes les dates de prévisions uniques
        forecasts_dates = []
        df_all = get_forecasts()
        if not df_all.empty and 'forecast_date' in df_all.columns:
            unique_dates = df_all['forecast_date'].unique()
            for date in unique_dates:
                date_str = date.strftime('%Y-%m-%d') if hasattr(date, 'strftime') else str(date)
                forecasts_dates.append({
                    "forecast_date": date_str,
                    "filename": f"forecast_{date_str}.xlsx",  # Nom fictif pour compatibilité
                    "path": f"db://forecasts/{date_str}"  # Identifiant pour la DB
                })
        
        # Trier par date (plus récent en premier)
        forecasts_dates.sort(key=lambda x: x["forecast_date"], reverse=True)
        
        return jsonify({
            "forecasts": forecasts_dates
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la liste des prévisions : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/forecasts/latest', methods=['GET'])
def get_latest_forecast_api():
    """Récupère la dernière prévision depuis la base de données."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        df = get_latest_forecast()
        
        if df.empty:
            return jsonify({"error": "Aucune prévision trouvée"}), 404
        
        forecast_date = get_latest_forecast_date()
        
        # Convertir les dates en string pour JSON
        if 'date' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            else:
                df['date'] = df['date'].astype(str)
        
        # Mapper les colonnes de la base de données vers les noms utilisés dans le frontend
        column_mapping = {
            'temperature_max': 'temp_max',
            'temperature_min': 'temp_min',
            'precipitation_sum': 'rain_mm',
            'sunshine_duration': 'sun_hours',
            'relative_humidity_mean': 'humidity'
        }
        
        # Renommer les colonnes si elles existent
        for old_name, new_name in column_mapping.items():
            if old_name in df.columns:
                df[new_name] = df[old_name]
        
        # Calculer temp_mean si temp_max et temp_min sont présents
        if 'temp_max' in df.columns and 'temp_min' in df.columns:
            df['temp_mean'] = (df['temp_max'] + df['temp_min']) / 2
        
        # Convertir sunshine_duration de secondes en heures si nécessaire
        if 'sun_hours' in df.columns:
            # Si la valeur est > 24, c'est probablement en secondes, convertir en heures
            df['sun_hours'] = df['sun_hours'].apply(lambda x: x / 3600.0 if x and x > 24 else x)
        
        # Convertir NaN en None pour JSON
        df_clean = df.where(pd.notnull(df), None)
        data = df_clean.to_dict('records')
        
        # Nettoyer les valeurs nan restantes
        import math
        def clean_nan(value):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None
            return value
        
        data = [{k: clean_nan(v) for k, v in row.items()} for row in data]
        
        return jsonify({
            "filename": f"forecast_{forecast_date}.xlsx",
            "date": forecast_date,
            "data": data,
            "summary": {
                "total_rows": len(df),
                "dates": sorted(df['date'].unique().tolist()) if 'date' in df.columns else [],
                "parcelles": sorted(df['parcelle'].unique().tolist()) if 'parcelle' in df.columns else [],
                "varieties": sorted(df['variety'].unique().tolist()) if 'variety' in df.columns else []
            }
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la dernière prévision : {e}", exc_info=True)
        return jsonify({"error": f"Erreur lors de la récupération: {str(e)}"}), 500

@app.route('/api/forecasts/<forecast_date>', methods=['GET'])
def get_forecast_by_date(forecast_date):
    """Récupère une prévision spécifique par sa date de génération (format YYYY-MM-DD)."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        df = get_forecasts(forecast_date=forecast_date)
        
        if df.empty:
            return jsonify({"error": "Prévision introuvable"}), 404
        
        # Convertir les dates en string pour JSON
        if 'date' in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df['date']):
                df['date'] = df['date'].dt.strftime('%Y-%m-%d')
            else:
                df['date'] = df['date'].astype(str)
        
        # Convertir NaN en None pour JSON
        import math
        def clean_nan(value):
            if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
                return None
            return value
        
        df_clean = df.where(pd.notnull(df), None)
        data = df_clean.to_dict('records')
        data = [{k: clean_nan(v) for k, v in row.items()} for row in data]
        
        return jsonify({
            "filename": f"forecast_{forecast_date}.xlsx",
            "date": forecast_date,
            "data": data,
            "summary": {
                "total_rows": len(df),
                "dates": sorted(df['date'].unique().tolist()) if 'date' in df.columns else [],
                "parcelles": sorted(df['parcelle'].unique().tolist()) if 'parcelle' in df.columns else [],
                "varieties": sorted(df['variety'].unique().tolist()) if 'variety' in df.columns else []
            }
        })
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la prévision : {e}", exc_info=True)
        return jsonify({"error": f"Erreur lors de la récupération: {str(e)}"}), 500

@app.route('/api/forecasts/<forecast_date>/download', methods=['GET'])
def download_forecast(forecast_date):
    """Exporte et télécharge une prévision en Excel."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    
    try:
        # Exporter vers Excel
        output_path = export_forecast_to_excel(forecast_date=forecast_date)
        filename = Path(output_path).name
        
        return send_from_directory(
            str(Path(output_path).parent),
            filename,
            as_attachment=True,
            download_name=filename
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 404
    except Exception as e:
        logger.error(f"Erreur lors de l'export de la prévision : {e}", exc_info=True)
        return jsonify({"error": f"Erreur lors de l'export: {str(e)}"}), 500

# ===== ENDPOINTS API POUR LA GESTION DES DONNÉES (SQLite) =====

@app.route('/api/db/init', methods=['POST'])
def init_db():
    """Initialise la base de données."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        init_database()
        return jsonify({"message": "Base de données initialisée"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/db/import', methods=['POST'])
def import_from_excel():
    """Importe les données depuis le fichier Excel vers la base de données."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        from scripts.migrate_excel_to_db import migrate_excel_to_db
        success = migrate_excel_to_db()
        if success:
            return jsonify({"message": "Données importées depuis Excel avec succès"})
        else:
            return jsonify({"error": "Échec de l'importation des données"}), 500
    except FileNotFoundError as e:
        return jsonify({"error": f"Fichier Excel introuvable : {e}"}), 404
    except Exception as e:
        logger.error(f"Erreur lors de l'importation depuis Excel : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/db/export-template', methods=['GET', 'POST'])
def export_template():
    """Exporte les données de la base vers un fichier Excel (template)."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        from database import export_to_excel
        from pyinstaller_utils import get_base_path
        
        # Créer le fichier dans le dossier de l'application
        app_dir = get_base_path()
        output_path = app_dir / "recoltes_fraises_template.xlsx"
        
        # Exporter les données actuelles (ou créer un template vide si la base est vide)
        export_to_excel(str(output_path))
        
        # Retourner le fichier pour téléchargement
        return send_from_directory(
            str(app_dir),
            "recoltes_fraises_template.xlsx",
            as_attachment=True,
            download_name="recoltes_fraises_template.xlsx"
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'export du template : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/db/upload-excel', methods=['POST'])
def upload_excel():
    """Télécharge un fichier Excel et l'importe dans la base de données."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        if 'file' not in request.files:
            return jsonify({"error": "Aucun fichier fourni"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "Aucun fichier sélectionné"}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({"error": "Le fichier doit être un fichier Excel (.xlsx ou .xls)"}), 400
        
        # Sauvegarder temporairement le fichier
        from pyinstaller_utils import get_base_path
        import tempfile
        
        app_dir = get_base_path()
        temp_dir = app_dir / "temp_imports"
        temp_dir.mkdir(exist_ok=True)
        
        temp_path = temp_dir / file.filename
        file.save(str(temp_path))
        
        try:
            from scripts.migrate_excel_to_db import migrate_excel_to_db
            # Passer directement le chemin du fichier temporaire
            success = migrate_excel_to_db(excel_path=str(temp_path))
            
            # Nettoyer le fichier temporaire
            temp_path.unlink()
            
            if success:
                return jsonify({"message": "Données importées depuis Excel avec succès"})
            else:
                return jsonify({"error": "Échec de l'importation des données"}), 500
        except Exception as e:
            # Nettoyer le fichier temporaire même en cas d'erreur
            if temp_path.exists():
                temp_path.unlink()
            raise
                
    except Exception as e:
        logger.error(f"Erreur lors de l'upload et import Excel : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

# --- PARAMETRES ---
@app.route('/api/parametres', methods=['GET'])
def api_get_parametres():
    """Récupère tous les paramètres."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        import numpy as np
        import math
        df = get_parametres()
        # Convertir en dictionnaire d'abord
        records = df.to_dict('records')
        # Nettoyer TOUTES les valeurs NaN/NaT/NA de manière exhaustive
        for record in records:
            for key, value in record.items():
                # Vérifier tous les types de NaN possibles
                if value is None:
                    continue
                # Vérifier si c'est un float NaN
                if isinstance(value, float):
                    if math.isnan(value) or str(value).lower() == 'nan':
                        record[key] = None
                        continue
                # Vérifier si c'est un numpy NaN
                try:
                    if hasattr(np, 'isnan') and np.isnan(value):
                        record[key] = None
                        continue
                except (TypeError, ValueError):
                    pass
                # Vérifier si c'est pandas NA
                if pd.isna(value) if hasattr(pd, 'isna') else False:
                    record[key] = None
                    continue
                # Vérifier si c'est une chaîne "NaN"
                if isinstance(value, str) and value.lower() == 'nan':
                    record[key] = None
                    continue
        return jsonify({"data": records})
    except Exception as e:
        logger.error(f"Erreur lors de la récupération des paramètres : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/parametres', methods=['POST'])
def api_add_parametre():
    """Ajoute un paramètre."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation
        parcelle = validate_parcelle(data.get('parcelle'))
        variety = validate_variety(data.get('variety'))
        nb_rangees = validate_nb_rangees(data.get('nb_rangees', 10))
        saison_debut = data.get('saison_debut')
        saison_fin = data.get('saison_fin')
        
        id = add_parametre(
            parcelle=parcelle,
            variety=variety,
            nb_rangees=nb_rangees,
            saison_debut=saison_debut,
            saison_fin=saison_fin
        )
        trigger_model_update_async()
        logger.info(f"Paramètre ajouté : {parcelle}/{variety}")
        return jsonify({"id": id, "message": "Paramètre ajouté"}), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du paramètre : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/parametres/<int:id>', methods=['PUT'])
def api_update_parametre(id):
    """Met à jour un paramètre."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        validate_id(id)
        data = request.json
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation des champs fournis
        parcelle = validate_parcelle(data.get('parcelle')) if data.get('parcelle') else None
        variety = validate_variety(data.get('variety')) if data.get('variety') else None
        nb_rangees = validate_nb_rangees(data.get('nb_rangees')) if data.get('nb_rangees') is not None else None
        
        # Gérer saison_debut et saison_fin : distinguer "non fourni" de "fourni avec None"
        saison_debut = data.get('saison_debut')
        saison_fin = data.get('saison_fin')
        # Si le champ est présent dans data (même avec None), on veut le mettre à jour
        update_saison_debut = 'saison_debut' in data
        update_saison_fin = 'saison_fin' in data
        
        success = update_parametre(
            id=id,
            parcelle=parcelle,
            variety=variety,
            nb_rangees=nb_rangees,
            saison_debut=saison_debut,
            saison_fin=saison_fin,
            update_saison_debut=update_saison_debut,
            update_saison_fin=update_saison_fin
        )
        if success:
            trigger_model_update_async()
            logger.info(f"Paramètre {id} mis à jour")
            # Retourner les données mises à jour
            from database import get_parametres
            df = get_parametres()
            updated_param = df[df['id'] == id]
            if not updated_param.empty:
                df = df.where(pd.notnull(df), None)
                param_dict = updated_param.to_dict('records')[0]
                return jsonify({"message": "Paramètre mis à jour", "data": param_dict})
            return jsonify({"message": "Paramètre mis à jour"})
        else:
            return jsonify({"error": "Paramètre introuvable"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du paramètre {id} : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/parametres/<int:id>', methods=['DELETE'])
def api_delete_parametre(id):
    """Supprime un paramètre."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        success = delete_parametre(id)
        if success:
            trigger_model_update_async()
            return jsonify({"message": "Paramètre supprimé"})
        else:
            return jsonify({"error": "Paramètre introuvable"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RECOLTES ---
@app.route('/api/recoltes', methods=['GET'])
def api_get_recoltes():
    """Récupère les récoltes avec filtres optionnels."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        variety = request.args.get('variety')
        df = get_recoltes(start_date=start_date, end_date=end_date, variety=variety)
        # Convertir les dates en string pour JSON
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df = df.where(pd.notnull(df), None)
        return jsonify({"data": df.to_dict('records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recoltes', methods=['POST'])
def api_add_recolte():
    """Ajoute une récolte."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation
        date = validate_date(data.get('date'))
        variety = validate_variety(data.get('variety'))
        kg_total = validate_kg_total(data.get('kg_total'))
        commentaires = validate_commentaires(data.get('commentaires'))
        
        id = add_recolte(
            date=date,
            variety=variety,
            kg_total=kg_total,
            commentaires=commentaires
        )
        trigger_model_update_async()
        logger.info(f"Récolte ajoutée : {date} - {variety} - {kg_total}kg")
        return jsonify({"id": id, "message": "Récolte ajoutée"}), 201
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la récolte : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/recoltes/<int:id>', methods=['PUT'])
def api_update_recolte(id):
    """Met à jour une récolte."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        validate_id(id)
        data = request.json
        if not data:
            return jsonify({"error": "Données JSON requises"}), 400
        
        # Validation des champs fournis
        date = validate_date(data.get('date')) if data.get('date') else None
        variety = validate_variety(data.get('variety')) if data.get('variety') else None
        kg_total = validate_kg_total(data.get('kg_total')) if data.get('kg_total') is not None else None
        commentaires = validate_commentaires(data.get('commentaires'))
        
        success = update_recolte(
            id=id,
            date=date,
            variety=variety,
            kg_total=kg_total,
            commentaires=commentaires
        )
        if success:
            trigger_model_update_async()
            logger.info(f"Récolte {id} mise à jour")
            return jsonify({"message": "Récolte mise à jour"})
        else:
            return jsonify({"error": "Récolte introuvable"}), 404
    except ValidationError as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la récolte {id} : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/api/recoltes/<int:id>', methods=['DELETE'])
def api_delete_recolte(id):
    """Supprime une récolte."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        success = delete_recolte(id)
        if success:
            trigger_model_update_async()
            return jsonify({"message": "Récolte supprimée"})
        else:
            return jsonify({"error": "Récolte introuvable"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- JOUR COURANT ---
@app.route('/api/jour-courant', methods=['GET'])
def api_get_jour_courant():
    """Récupère les données du jour courant."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        date = request.args.get('date')
        df = get_jour_courant(date=date)
        if 'date' in df.columns:
            df['date'] = df['date'].dt.strftime('%Y-%m-%d')
        df = df.where(pd.notnull(df), None)
        return jsonify({"data": df.to_dict('records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jour-courant', methods=['POST'])
def api_set_jour_courant():
    """Ajoute ou met à jour les données du jour courant."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        data = request.json
        id = set_jour_courant(
            date=data.get('date'),
            variety=data.get('variety'),
            kg_premiere_rangee=data.get('kg_premiere_rangee'),
            commentaires=data.get('commentaires')
        )
        return jsonify({"id": id, "message": "Données du jour courant enregistrées"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/jour-courant', methods=['DELETE'])
def api_clear_jour_courant():
    """Efface les données du jour courant."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        date = request.args.get('date')
        clear_jour_courant(date=date)
        return jsonify({"message": "Données du jour courant effacées"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- PLANTS PAR ANNEE ---
@app.route('/api/plants-par-annee', methods=['GET'])
def api_get_plants_par_annee():
    """Récupère les données de plants par année."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        annee = request.args.get('annee', type=int)
        df = get_plants_par_annee(annee=annee)
        df = df.where(pd.notnull(df), None)
        return jsonify({"data": df.to_dict('records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plants-par-annee', methods=['POST'])
def api_set_plants_par_annee():
    """Ajoute ou met à jour les plants par année."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        data = request.json
        id = set_plants_par_annee(
            variety=data.get('variety'),
            annee=data.get('annee'),
            nb_plants=data.get('nb_plants')
        )
        trigger_model_update_async()
        return jsonify({"id": id, "message": "Plants par année enregistrés"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/plants-par-annee/<int:id>', methods=['DELETE'])
def api_delete_plants_par_annee(id):
    """Supprime un enregistrement de plants par année."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        from database import get_connection
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM plants_par_annee WHERE id = ?", (id,))
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            trigger_model_update_async()
            return jsonify({"message": "Plants par année supprimés"})
        else:
            return jsonify({"error": "Enregistrement introuvable"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- RECOLTE QUOTIDIENNE ---
@app.route('/api/recolte-quotidienne', methods=['GET'])
def api_get_recolte_quotidienne():
    """Récupère la configuration de récolte quotidienne."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        df = get_recolte_quotidienne()
        df = df.where(pd.notnull(df), None)
        return jsonify({"data": df.to_dict('records')})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recolte-quotidienne', methods=['POST'])
def api_set_recolte_quotidienne():
    """Ajoute ou met à jour la configuration de récolte quotidienne."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        data = request.json
        id = set_recolte_quotidienne(
            jour_semaine=data.get('jour_semaine'),
            jour_semaine_num=data.get('jour_semaine_num'),
            fraction_fraiseraie=data.get('fraction_fraiseraie'),
            description=data.get('description')
        )
        trigger_model_update_async()
        return jsonify({"id": id, "message": "Configuration enregistrée"}), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- EXPORT EXCEL ---
@app.route('/api/export-excel', methods=['POST'])
def api_export_excel():
    """Exporte toutes les données vers Excel."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        output_path = request.json.get('output_path', 'recoltes_export.xlsx')
        export_to_excel(output_path)
        return jsonify({"message": "Export réussi", "path": output_path})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/recoltes/download', methods=['GET'])
def download_recoltes():
    """Télécharge toutes les récoltes en Excel."""
    if not DB_AVAILABLE:
        return jsonify({"error": "Base de données non disponible"}), 503
    try:
        # S'assurer que le répertoire de base existe
        BASE_PATH.mkdir(parents=True, exist_ok=True)
        
        output_path = str(BASE_PATH / f"recoltes_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx")
        export_to_excel(output_path)
        
        # Vérifier que le fichier a bien été créé
        output_file = Path(output_path)
        if not output_file.exists():
            raise FileNotFoundError(f"Le fichier d'export n'a pas pu être créé : {output_path}")
        
        filename = output_file.name
        parent_dir = str(output_file.parent)
        
        return send_from_directory(
            parent_dir,
            filename,
            as_attachment=True,
            download_name=filename
        )
    except FileNotFoundError as e:
        logger.error(f"Fichier introuvable lors de l'export des récoltes : {e}", exc_info=True)
        return jsonify({"error": f"Fichier introuvable : {str(e)}"}), 404
    except PermissionError as e:
        logger.error(f"Erreur de permissions lors de l'export des récoltes : {e}", exc_info=True)
        return jsonify({"error": f"Erreur de permissions : {str(e)}"}), 500
    except Exception as e:
        logger.error(f"Erreur lors de l'export des récoltes : {e}", exc_info=True)
        return jsonify({"error": f"Erreur lors de l'export: {str(e)}"}), 500

# Route pour servir l'application React en production
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder = Path(app.static_folder)
    if path != "" and (static_folder / path).exists():
        return send_from_directory(static_folder, path)
    else:
        # Servir index.html pour toutes les routes (SPA)
        index_path = static_folder / 'index.html'
        if index_path.exists():
            return send_from_directory(static_folder, 'index.html')
        else:
            return jsonify({"error": "Frontend non trouvé. Veuillez compiler le frontend avec 'npm run build'."}), 404


# Flag pour fermer le splash au premier accès (Flask 3.x compatible)
_splash_closed = False

@app.before_request
def _close_splash_on_first_request():
    """Ferme l'écran de chargement PyInstaller au premier accès HTTP (compatible Flask 3.x)."""
    global _splash_closed
    if not _splash_closed:
        _splash_closed = True
        splash_update("Application prête")
        splash_close()

def open_browser(target_url=None, delay=1.5, background=True):
    """Ouvre le navigateur par défaut après un court délai."""
    url = target_url or SERVER_BASE_URL

    def _open():
        import time
        import webbrowser
        if delay and delay > 0:
            time.sleep(delay)
        try:
            # Sur macOS, forcer l'ouverture dans un nouvel onglet/fenêtre
            if sys.platform == "darwin":
                # Utiliser 'open' pour forcer l'ouverture même si le navigateur est déjà ouvert
                os.system(f'open "{url}" &')
            else:
                webbrowser.open(url)
            logger.info(f"Navigateur ouvert vers {url}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du navigateur : {e}")
            # Fallback: essayer avec os.system sur macOS
            if sys.platform == "darwin":
                try:
                    os.system(f'open "{url}" &')
                except Exception:
                    pass

    if background:
        threading.Thread(target=_open, daemon=True).start()
    else:
        _open()

# Variable globale pour le gestionnaire d'icône système
tray_manager = None

def cleanup_resources():
    """Nettoie les ressources à la fermeture de l'application."""
    global tray_manager, model_update_timer
    
    logger.info("Nettoyage des ressources...")
    
    # Arrêter le timer de mise à jour du modèle s'il est actif
    if model_update_timer:
        try:
            model_update_timer.cancel()
        except Exception:
            pass
    
    # Arrêter l'icône système
    if tray_manager:
        try:
            tray_manager.stop()
        except Exception as e:
            logger.error(f"Erreur lors de l'arrêt de l'icône système : {e}")
    
    # Fermer les connexions à la base de données
    if DB_AVAILABLE:
        try:
            from database import get_connection
            conn = get_connection()
            if conn:
                conn.close()
        except Exception as e:
            logger.error(f"Erreur lors de la fermeture de la base de données : {e}")
    
    logger.info("Nettoyage terminé")

def schedule_app_shutdown(delay_seconds=2.0, reason=""):
    """Planifie l'arrêt complet de l'application après un court délai."""
    def _shutdown():
        import time
        time.sleep(max(0.0, float(delay_seconds)))
        try:
            logger.info(f"Arrêt programmé de l'application ({reason})")
            cleanup_resources()
        except Exception as e:
            logger.warning(f"Erreur durant le cleanup avant arrêt programmé: {e}")
        finally:
            # Sortie forcée pour garantir la libération des verrous de fichiers Windows.
            os._exit(0)

    threading.Thread(target=_shutdown, daemon=True).start()

# ===== API ENDPOINTS POUR MISE À JOUR AUTOMATIQUE =====

@app.route('/api/updates/check', methods=['GET'])
def api_check_updates():
    """Vérifie les mises à jour disponibles."""
    try:
        from auto_updater import check_for_updates, get_current_version
        # Inclure les prereleases pour détecter les builds automatiques
        include_prerelease = request.args.get('include_prerelease', 'true').lower() == 'true'
        
        # Récupérer la version actuelle pour le débogage
        current_version = get_current_version()
        
        # Vérifier les mises à jour
        update_info = check_for_updates(include_prerelease=include_prerelease)
        
        # Ajouter des informations de débogage
        update_info['debug'] = {
            'current_version': current_version,
            'include_prerelease': include_prerelease,
            'github_repo': 'ldevalbray/production_prediction'
        }
        
        logger.info(f"Vérification des mises à jour : disponible={update_info.get('available', False)}, "
                   f"actuelle={current_version}, dernière={update_info.get('latest_version', 'N/A')}")
        
        return jsonify(update_info)
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des mises à jour : {e}", exc_info=True)
        return jsonify({"error": str(e), "available": False}), 500

@app.route('/api/updates/download', methods=['POST'])
def api_download_update():
    """Télécharge et installe la mise à jour."""
    try:
        from auto_updater import get_download_url_for_platform, download_update, install_update
        from pyinstaller_utils import get_base_path
        
        download_url = get_download_url_for_platform()
        if not download_url:
            return jsonify({"error": "Aucune mise à jour disponible pour cette plateforme"}), 404
        
        app_dir = get_base_path()
        
        # Télécharger la mise à jour
        def progress_callback(progress):
            # Vous pouvez implémenter un système de WebSocket pour notifier le frontend
            logger.info(f"Téléchargement : {progress:.1f}%")
        
        zip_path = download_update(download_url, progress_callback)
        
        # Installer la mise à jour (version du schéma cible = 1 pour l'instant)
        install_update(zip_path, app_dir, target_schema_version=1)
        
        message = "Mise à jour installée avec succès. Veuillez redémarrer l'application pour appliquer les changements."
        auto_close_scheduled = False
        if sys.platform == "win32" and is_pyinstaller():
            # Sur Windows packagé, l'update est différée et nécessite la fermeture complète
            # du process pour libérer les DLL/.pyd verrouillés.
            message = ("Mise à jour planifiée avec succès. "
                       "L'application va se fermer automatiquement dans quelques secondes.")
            auto_close_scheduled = True
            schedule_app_shutdown(delay_seconds=2.5, reason="finalisation mise à jour Windows")

        return jsonify({
            "success": True,
            "message": message,
            "requires_restart": True,
            "auto_close_scheduled": auto_close_scheduled,
        })
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour : {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

def check_updates_async():
    """Vérifie les mises à jour en arrière-plan au démarrage."""
    try:
        from auto_updater import check_for_updates
        
        # Vérifier d'abord les releases stables, puis les prereleases
        update_info = check_for_updates(include_prerelease=False)
        if not update_info.get("available"):
            # Si pas de release stable, vérifier les prereleases (builds automatiques)
            update_info = check_for_updates(include_prerelease=True)
        
        if update_info.get("available"):
            latest_version = update_info.get("latest_version")
            current_version = update_info.get("current_version")
            is_prerelease = update_info.get("prerelease", False)
            release_type = "prerelease (build automatique)" if is_prerelease else "release stable"
            logger.info(f"Une nouvelle version est disponible : {latest_version} (actuelle : {current_version}) - {release_type}")
        else:
            logger.info("L'application est à jour")
    except Exception as e:
        logger.warning(f"Impossible de vérifier les mises à jour : {e}")

# Vérifier les mises à jour au démarrage (en arrière-plan)
threading.Thread(target=check_updates_async, daemon=True).start()

# Enregistrer les gestionnaires de fermeture
atexit.register(cleanup_resources)

def signal_handler(signum, frame):
    """Gère les signaux système (SIGTERM, SIGINT)."""
    logger.info(f"Signal {signum} reçu, fermeture de l'application...")
    cleanup_resources()
    sys.exit(0)

# Enregistrer les gestionnaires de signaux (uniquement sur Unix/macOS)
if sys.platform != 'win32':
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

if __name__ == '__main__':
    # Si le port demandé est occupé par un autre service, basculer automatiquement.
    if not is_server_already_running() and is_port_in_use(SERVER_HOST, SERVER_PORT):
        fallback_port = find_available_port(SERVER_HOST, SERVER_PORT + 1, max_tries=20)
        if fallback_port is not None:
            previous_port = SERVER_PORT
            set_server_binding(SERVER_HOST, fallback_port)
            logger.warning(
                f"Port {previous_port} déjà occupé par un autre service; bascule automatique sur {SERVER_PORT}."
            )
        else:
            logger.error(
                f"Port {SERVER_PORT} occupé et aucun port libre trouvé dans la plage {SERVER_PORT + 1}-{SERVER_PORT + 20}."
            )

    if is_server_already_running():
        logger.info("Serveur déjà en cours d'exécution, ouverture d'une nouvelle fenêtre vers l'instance existante.")
        splash_update("Serveur déjà actif, redirection...")
        splash_close()
        # Ouvrir le navigateur immédiatement et de manière synchrone pour s'assurer que ça fonctionne
        try:
            import webbrowser
            import time
            # Attendre un peu pour que le splash se ferme
            time.sleep(0.2)
            # Sur macOS, utiliser 'open' pour forcer l'ouverture
            if sys.platform == "darwin":
                os.system(f'open "{SERVER_BASE_URL}" &')
            else:
                webbrowser.open(SERVER_BASE_URL)
            logger.info(f"Navigateur ouvert vers {SERVER_BASE_URL}")
        except Exception as e:
            logger.error(f"Erreur lors de l'ouverture du navigateur : {e}")
        sys.exit(0)

    # Fermer le splash juste avant de démarrer le serveur (fallback si aucun accès HTTP n'arrive rapidement)
    splash_update("Démarrage du serveur...")
    
    # Démarrer l'icône système si disponible
    if SYSTEM_TRAY_AVAILABLE:
        try:
            tray_manager = SystemTrayManager(
                server_url=SERVER_BASE_URL,
                on_quit=cleanup_resources
            )
            tray_manager.start()
            logger.info("Icône système démarrée")
        except Exception as e:
            logger.error(f"Erreur lors du démarrage de l'icône système : {e}")
    
    # Ouvrir le navigateur automatiquement (sauf si on est dans un exécutable PyInstaller en mode production)
    if not is_pyinstaller() or os.environ.get('FLASK_ENV') != 'production':
        open_browser()

    # Fermer le splash après un court délai pour s'assurer qu'il se ferme même sans accès HTTP
    def delayed_splash_close():
        import time
        time.sleep(2)  # Attendre 2 secondes après le démarrage
        splash_close()
    
    threading.Thread(target=delayed_splash_close, daemon=True).start()
    
    # Initialiser la base de données au démarrage
    if DB_AVAILABLE:
        try:
            init_database()
            logger.info("Base de données initialisée avec succès")
            if splash_is_active():
                splash_update("Base de données initialisée...")
            
            # Vérifier si la base est vide et importer depuis Excel si disponible
            try:
                from database import get_parametres
                from config import EXCEL_PATH
                
                # Vérifier si la base est vide (pas de paramètres)
                params_df = get_parametres()
                if params_df.empty and Path(EXCEL_PATH).exists():
                    logger.info("Base de données vide, tentative d'import depuis Excel...")
                    if splash_is_active():
                        splash_update("Import des données depuis Excel...")
                    
                    from scripts.migrate_excel_to_db import migrate_excel_to_db
                    if migrate_excel_to_db():
                        logger.info("Données importées depuis Excel avec succès")
                    else:
                        logger.warning("Échec de l'importation depuis Excel")
            except Exception as e:
                logger.debug(f"Import automatique depuis Excel non disponible : {e}")
                # Ne pas bloquer le démarrage si l'import échoue
                
        except Exception as e:
            logger.error(f"Erreur lors de l'initialisation de la base de données : {e}", exc_info=True)
            # Continuer quand même, l'utilisateur pourra initialiser manuellement via /api/db/init
    
    try:
        app.run(debug=not is_pyinstaller(), port=SERVER_PORT, host=SERVER_HOST, use_reloader=False)
    except KeyboardInterrupt:
        logger.info("Interruption clavier détectée, fermeture...")
        cleanup_resources()
    except Exception as e:
        logger.error(f"Erreur lors de l'exécution du serveur : {e}", exc_info=True)
        cleanup_resources()
        raise

