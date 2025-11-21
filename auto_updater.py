"""
Module de mise à jour automatique pour l'application Pépinière Valbray
Vérifie les nouvelles versions depuis GitHub Releases et propose la mise à jour

IMPORTANT : Ce système préserve TOUTES les données utilisateur :
- Base de données (recoltes.db)
- Prévisions (forecasts/)
- Modèles ML locaux (models/)
- Fichiers de configuration (last_runs.json, etc.)
"""
import requests
import json
import sys
import subprocess
import platform
from pathlib import Path
from packaging import version
import zipfile
import shutil
import sqlite3
import logging
from typing import Optional, Dict, List

# Version actuelle de l'application (par défaut, sera remplacée par la version installée)
DEFAULT_APP_VERSION = "1.0.0"  # Version par défaut si aucune version n'est trouvée
GITHUB_REPO = "ldevalbray/production_prediction"  # Votre repo GitHub
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

# Fichier pour stocker la version installée
VERSION_FILE = "installed_version.txt"

# Fichiers et dossiers à PRÉSERVER lors de la mise à jour (données utilisateur)
# NOTE: Les fichiers de données utilisateur sont maintenant dans le dossier data/
# Seuls les fichiers à la racine sont listés ici
PROTECTED_FILES = [
    "app.log",               # Logs de l'application (à la racine)
]

PROTECTED_DIRS = [
    "data",                 # Toutes les données utilisateur (recoltes.db, recoltes_fraises.xlsx, last_runs.json, etc.)
    "forecasts",            # Prévisions générées (peut être dans data/forecasts ou à la racine)
    "models",               # Modèles ML entraînés localement (peut être dans data/models ou à la racine)
    "models_archive",       # Archives des modèles
]

logger = logging.getLogger(__name__)

def get_current_version():
    """
    Retourne la version actuelle de l'application.
    Essaie de lire depuis le fichier installed_version.txt, sinon utilise la version par défaut.
    """
    from pyinstaller_utils import get_base_path
    
    # Essayer de lire depuis le fichier de version installée
    try:
        base_path = get_base_path()
        version_file = base_path / VERSION_FILE
        if version_file.exists():
            version = version_file.read_text().strip()
            if version:
                logger.debug(f"Version lue depuis {version_file}: {version}")
                return version
    except Exception as e:
        logger.debug(f"Impossible de lire la version depuis le fichier : {e}")
    
    # Fallback : version par défaut
    logger.debug(f"Utilisation de la version par défaut: {DEFAULT_APP_VERSION}")
    return DEFAULT_APP_VERSION

def check_for_updates(include_prerelease=False):
    """
    Vérifie s'il y a une nouvelle version disponible sur GitHub.
    
    Args:
        include_prerelease: Si True, inclut les prereleases (builds automatiques)
    """
    try:
        # Si on veut inclure les prereleases, on doit récupérer toutes les releases
        if include_prerelease:
            releases_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            response = requests.get(releases_url, timeout=5, params={"per_page": 10})
            response.raise_for_status()
            releases = response.json()
            
            # Prendre la première release (la plus récente)
            if releases:
                release_data = releases[0]
            else:
                return {"available": False}
        else:
            # Sinon, utiliser l'endpoint /latest qui exclut les prereleases
            response = requests.get(UPDATE_CHECK_URL, timeout=5)
            response.raise_for_status()
            release_data = response.json()
        
        latest_version = release_data.get("tag_name", "").lstrip("v")
        current_version = get_current_version()
        
        # Si on est à la version par défaut et qu'on détecte une release disponible,
        # mettre à jour le fichier de version (première installation)
        if current_version == DEFAULT_APP_VERSION and latest_version:
            try:
                from pyinstaller_utils import get_base_path
                base_path = get_base_path()
                version_file = base_path / VERSION_FILE
                version_file.parent.mkdir(parents=True, exist_ok=True)
                version_file.write_text(latest_version)
                logger.info(f"Version initiale enregistrée : {latest_version}")
                current_version = latest_version
            except Exception as e:
                logger.debug(f"Impossible d'enregistrer la version initiale : {e}")
        
        # Comparer les versions (gérer les formats comme "20250101-abc1234")
        try:
            # Essayer de parser comme version normale
            latest_ver = version.parse(latest_version)
            current_ver = version.parse(current_version)
            is_newer = latest_ver > current_ver
        except:
            # Si le parsing échoue (format date-SHA), comparer les strings
            # Pour les builds automatiques, on considère toujours qu'il y a une mise à jour
            # si la version est différente
            is_newer = latest_version != current_version
        
        if is_newer:
            return {
                "available": True,
                "latest_version": latest_version,
                "current_version": current_version,
                "release_url": release_data.get("html_url", ""),
                "release_notes": release_data.get("body", ""),
                "assets": release_data.get("assets", []),
                "prerelease": release_data.get("prerelease", False)
            }
        return {"available": False}
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification des mises à jour : {e}")
        return {"available": False, "error": str(e)}

def get_download_url_for_platform(include_prerelease=True):
    """
    Retourne l'URL de téléchargement pour la plateforme actuelle.
    
    Args:
        include_prerelease: Si True, inclut les prereleases (builds automatiques)
    """
    update_info = check_for_updates(include_prerelease=include_prerelease)
    if not update_info.get("available"):
        return None
    
    assets = update_info.get("assets", [])
    platform_name = platform.system().lower()
    
    # Chercher l'asset correspondant à la plateforme
    if platform_name == "windows":
        for asset in assets:
            if "windows" in asset["name"].lower() and asset["name"].endswith(".zip"):
                return asset["browser_download_url"]
    elif platform_name == "darwin":  # macOS
        # Préférer le ZIP pour macOS (plus facile à extraire)
        for asset in assets:
            if "macos" in asset["name"].lower() and asset["name"].endswith(".zip"):
                return asset["browser_download_url"]
        # Fallback : chercher un .app ou .dmg (nécessitera un traitement spécial)
        for asset in assets:
            if "macos" in asset["name"].lower() or asset["name"].endswith((".dmg", ".app")):
                logger.warning(f"Fichier {asset['name']} détecté mais non supporté pour mise à jour automatique. Utilisez un ZIP.")
                # Ne pas retourner pour forcer l'utilisateur à télécharger manuellement
                return None
    
    return None

def get_user_data_dir(app_dir: Path) -> Path:
    """
    Retourne le chemin du dossier de données utilisateur.
    Pour macOS .app, retourne Contents/Resources/Data/ à l'intérieur du bundle.
    Pour Windows/Linux, retourne data/ dans le dossier de l'application.
    """
    import sys
    if sys.platform == "darwin":
        # Pour macOS, vérifier si app_dir est un .app ou contient un .app
        if app_dir.suffix == ".app":
            # app_dir est le bundle .app
            return app_dir / "Contents" / "Resources" / "Data"
        elif (app_dir / "Contents" / "Resources").exists():
            # app_dir pointe déjà vers le .app
            return app_dir / "Contents" / "Resources" / "Data"
        else:
            # Chercher un .app dans app_dir
            for item in app_dir.iterdir():
                if item.suffix == ".app":
                    return item / "Contents" / "Resources" / "Data"
            # Fallback: créer data/ dans app_dir
            return app_dir / "data"
    else:
        # Windows/Linux: data/ dans le dossier de l'application
        return app_dir / "data"

def migrate_old_files_to_data_dir(app_dir: Path):
    """
    Migre les anciens fichiers de données de la racine vers le dossier data/.
    Cette fonction est appelée pour assurer la compatibilité avec les anciennes versions.
    """
    data_dir = get_user_data_dir(app_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Fichiers à migrer de la racine vers data/
    files_to_migrate = [
        "recoltes.db",
        "recoltes_fraises.xlsx",
        "last_runs.json",
    ]
    
    migrated = False
    for filename in files_to_migrate:
        old_path = app_dir / filename
        new_path = data_dir / filename
        
        # Migrer seulement si le fichier existe à l'ancien emplacement et n'existe pas dans data/
        if old_path.exists() and old_path.is_file() and not new_path.exists():
            shutil.move(str(old_path), str(new_path))
            logger.info(f"  - Migré : {filename} → data/{filename}")
            migrated = True
    
    # Migrer les dossiers forecasts et models s'ils sont à la racine
    for dirname in ["forecasts", "models"]:
        old_dir = app_dir / dirname
        new_dir = data_dir / dirname
        
        if old_dir.exists() and old_dir.is_dir() and not new_dir.exists():
            shutil.move(str(old_dir), str(new_dir))
            logger.info(f"  - Migré : {dirname}/ → data/{dirname}/")
            migrated = True
    
    if migrated:
        logger.info("✅ Migration des fichiers vers data/ terminée")
    
    return migrated

def backup_user_data(app_dir: Path) -> Path:
    """
    Crée une sauvegarde complète des données utilisateur.
    Retourne le chemin du dossier de backup.
    """
    backup_dir = app_dir / "backup_before_update"
    backup_dir.mkdir(exist_ok=True)
    
    logger.info(f"Création d'une sauvegarde des données utilisateur dans {backup_dir}")
    
    # Migrer les anciens fichiers vers data/ avant la sauvegarde
    migrate_old_files_to_data_dir(app_dir)
    
    # Obtenir le chemin du dossier de données utilisateur
    data_dir = get_user_data_dir(app_dir)
    
    # Sauvegarder les fichiers protégés
    for filename in PROTECTED_FILES:
        # Chercher dans data_dir et app_dir
        src = data_dir / filename
        if not src.exists():
            src = app_dir / filename
        if src.exists() and src.is_file():
            shutil.copy2(src, backup_dir / filename)
            logger.info(f"  - Sauvegardé : {filename}")
    
    # Sauvegarder le dossier de données utilisateur complet
    if data_dir.exists() and data_dir.is_dir():
        dest = backup_dir / "data"
        shutil.copytree(data_dir, dest, dirs_exist_ok=True)
        logger.info(f"  - Sauvegardé : data/ (dossier de données utilisateur)")
    
    # Sauvegarder les autres dossiers protégés (forecasts, models, etc. peuvent être dans data/)
    for dirname in PROTECTED_DIRS:
        if dirname == "data":
            continue  # Déjà sauvegardé ci-dessus
        # Chercher dans data_dir et app_dir
        src = data_dir / dirname
        if not src.exists():
            src = app_dir / dirname
        if src.exists() and src.is_dir():
            dest = backup_dir / dirname
            shutil.copytree(src, dest, dirs_exist_ok=True)
            logger.info(f"  - Sauvegardé : {dirname}/")
    
    return backup_dir

def restore_user_data(backup_dir: Path, app_dir: Path):
    """Restaure les données utilisateur depuis la sauvegarde."""
    if not backup_dir.exists():
        logger.warning(f"Dossier de backup introuvable : {backup_dir}")
        return
    
    logger.info(f"Restauration des données utilisateur depuis {backup_dir}")
    
    # Obtenir le chemin du dossier de données utilisateur
    data_dir = get_user_data_dir(app_dir)
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Restaurer les fichiers protégés dans data_dir
    for filename in PROTECTED_FILES:
        src = backup_dir / filename
        if src.exists():
            dest = data_dir / filename
            shutil.copy2(src, dest)
            logger.info(f"  - Restauré : {filename}")
    
    # Restaurer le dossier de données utilisateur complet
    backup_data = backup_dir / "data"
    if backup_data.exists() and backup_data.is_dir():
        if data_dir.exists():
            shutil.rmtree(data_dir)
        shutil.copytree(backup_data, data_dir)
        logger.info(f"  - Restauré : data/ (dossier de données utilisateur)")
    
    # Restaurer les autres dossiers protégés
    for dirname in PROTECTED_DIRS:
        if dirname == "data":
            continue  # Déjà restauré ci-dessus
        src = backup_dir / dirname
        if src.exists():
            # Essayer dans data_dir d'abord, puis app_dir
            dest = data_dir / dirname
            if not dest.parent.exists():
                dest = app_dir / dirname
            if dest.exists():
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            logger.info(f"  - Restauré : {dirname}/")

def download_update(download_url: str, progress_callback=None) -> Path:
    """Télécharge la mise à jour."""
    try:
        response = requests.get(download_url, stream=True, timeout=30)
        response.raise_for_status()
        
        # Déterminer le nom du fichier
        filename = download_url.split("/")[-1].split("?")[0]  # Enlever les paramètres de requête
        download_path = Path(sys.executable).parent / filename
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        logger.info(f"Téléchargement de la mise à jour : {filename}")
        
        with open(download_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if progress_callback and total_size > 0:
                        progress = (downloaded / total_size) * 100
                        progress_callback(progress)
        
        # Vérifier que le fichier téléchargé est valide
        if not download_path.exists() or download_path.stat().st_size == 0:
            raise Exception("Le fichier téléchargé est vide ou n'existe pas")
        
        # Vérifier que c'est bien un ZIP (pour macOS et Windows)
        if download_path.suffix.lower() == '.zip':
            try:
                with zipfile.ZipFile(download_path, 'r') as test_zip:
                    test_zip.testzip()  # Vérifier l'intégrité
            except zipfile.BadZipFile:
                raise Exception(f"Le fichier téléchargé n'est pas un ZIP valide : {filename}")
        
        logger.info(f"Téléchargement terminé : {download_path} ({download_path.stat().st_size / 1024 / 1024:.1f} MB)")
        return download_path
    except Exception as e:
        raise Exception(f"Erreur lors du téléchargement : {e}")

def get_db_schema_version(db_path: Path) -> int:
    """Récupère la version du schéma de la base de données."""
    if not db_path.exists():
        return 0
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Vérifier si la table de version existe
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='schema_version'
        """)
        
        if cursor.fetchone():
            cursor.execute("SELECT version FROM schema_version LIMIT 1")
            result = cursor.fetchone()
            version = result[0] if result else 0
        else:
            version = 0
        
        conn.close()
        return version
    except Exception as e:
        logger.warning(f"Erreur lors de la lecture de la version du schéma : {e}")
        return 0

def set_db_schema_version(db_path: Path, version: int):
    """Définit la version du schéma de la base de données."""
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Créer la table si elle n'existe pas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS schema_version (
                version INTEGER PRIMARY KEY
            )
        """)
        
        # Insérer ou mettre à jour la version
        cursor.execute("DELETE FROM schema_version")
        cursor.execute("INSERT INTO schema_version (version) VALUES (?)", (version,))
        
        conn.commit()
        conn.close()
        logger.info(f"Version du schéma mise à jour : {version}")
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la version du schéma : {e}")

def run_database_migrations(db_path: Path, from_version: int, to_version: int):
    """
    Exécute les migrations de base de données nécessaires.
    Cette fonction doit être étendue avec les migrations réelles.
    """
    if from_version >= to_version:
        logger.info("Aucune migration nécessaire")
        return
    
    logger.info(f"Exécution des migrations de {from_version} vers {to_version}")
    
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Exemple de migration : ajouter une colonne si nécessaire
        # À adapter selon vos besoins réels
        for version in range(from_version + 1, to_version + 1):
            logger.info(f"  - Migration vers version {version}")
            
            # Exemple : Migration vers version 1
            if version == 1:
                # Ajouter la table schema_version si elle n'existe pas
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS schema_version (
                        version INTEGER PRIMARY KEY
                    )
                """)
                # Ajouter d'autres modifications de schéma si nécessaire
                # cursor.execute("ALTER TABLE recoltes ADD COLUMN new_field TEXT")
            
            # Ajouter d'autres migrations ici selon vos besoins
            # if version == 2:
            #     cursor.execute("ALTER TABLE ...")
        
        conn.commit()
        conn.close()
        
        # Mettre à jour la version
        set_db_schema_version(db_path, to_version)
        logger.info("Migrations terminées avec succès")
        
    except Exception as e:
        logger.error(f"Erreur lors des migrations : {e}")
        raise

def install_update(zip_path: Path, app_dir: Path, target_schema_version: int = 1):
    """
    Installe la mise à jour en préservant toutes les données utilisateur.
    
    Args:
        zip_path: Chemin vers le fichier ZIP de la mise à jour
        app_dir: Dossier de l'application
        target_schema_version: Version cible du schéma de base de données
    """
    try:
        logger.info("Début de l'installation de la mise à jour")
        
        # 1. Créer une sauvegarde complète
        backup_dir = backup_user_data(app_dir)
        
        # 2. Extraire la nouvelle version dans un dossier temporaire
        extract_dir = app_dir / "update_temp"
        if extract_dir.exists():
            shutil.rmtree(extract_dir)
        extract_dir.mkdir(exist_ok=True)
        
        logger.info(f"Extraction de la mise à jour dans {extract_dir}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # 3. Trouver le dossier de l'application dans l'archive
        # Pour macOS : l'archive contient PepiniereValbray.app
        # Pour Windows : l'archive contient PepiniereValbray/ avec _internal/
        new_app_dir = None
        new_app_bundle = None
        
        # D'abord, chercher un .app bundle (macOS)
        for item in extract_dir.rglob("PepiniereValbray.app"):
            if item.is_dir() and (item / "Contents").exists():
                new_app_bundle = item
                logger.info(f"Bundle .app trouvé : {new_app_bundle}")
                break
        
        # Si pas de .app, chercher un dossier avec _internal (Windows)
        if not new_app_bundle:
            for item in extract_dir.rglob("PepiniereValbray"):
                if item.is_dir() and (item / "_internal").exists():
                    new_app_dir = item
                    logger.info(f"Dossier avec _internal trouvé : {new_app_dir}")
                    break
        
        # Fallback : chercher le premier dossier avec _internal
        if not new_app_dir and not new_app_bundle:
            for item in extract_dir.iterdir():
                if item.is_dir():
                    if (item / "_internal").exists():
                        new_app_dir = item
                        logger.info(f"Dossier avec _internal trouvé (fallback) : {new_app_dir}")
                        break
                    elif item.suffix == ".app" and (item / "Contents").exists():
                        new_app_bundle = item
                        logger.info(f"Bundle .app trouvé (fallback) : {new_app_bundle}")
                        break
        
        if not new_app_dir and not new_app_bundle:
            raise Exception("Structure de l'archive invalide : dossier PepiniereValbray ou PepiniereValbray.app introuvable")
        
        # 4. Remplacer les fichiers de l'application (SAUF les données utilisateur)
        logger.info("Remplacement des fichiers de l'application...")
        
        # Liste des fichiers/dossiers à exclure (données utilisateur)
        exclude_items = set(PROTECTED_FILES + PROTECTED_DIRS)
        
        # Gérer macOS .app bundle
        if new_app_bundle:
            # Pour macOS, on doit remplacer le contenu du .app bundle
            # Trouver le .app existant
            old_app_bundle = None
            if app_dir.suffix == ".app":
                old_app_bundle = app_dir
            elif (app_dir / "Contents").exists():
                # app_dir pointe vers le .app
                old_app_bundle = app_dir
            else:
                # Remonter depuis app_dir pour trouver le .app
                # app_dir peut être Contents/Resources/Data/ ou un autre chemin
                current_path = app_dir
                max_depth = 10  # Limiter la profondeur pour éviter les boucles infinies
                depth = 0
                while current_path != current_path.parent and depth < max_depth:
                    if current_path.suffix == ".app" and (current_path / "Contents").exists():
                        old_app_bundle = current_path
                        break
                    # Vérifier si un .app est dans le dossier courant
                    for item in current_path.iterdir():
                        if item.suffix == ".app" and (item / "Contents").exists():
                            old_app_bundle = item
                            break
                    if old_app_bundle:
                        break
                    current_path = current_path.parent
                    depth += 1
            
            if not old_app_bundle:
                raise Exception(f"Bundle .app existant introuvable dans {app_dir}. Impossible de mettre à jour.")
            
            # Mettre à jour le bundle .app
            if old_app_bundle:
                logger.info(f"  - Mise à jour du bundle .app : {old_app_bundle}")
                # Remplacer Contents/ sauf Resources/Data/ (données utilisateur)
                new_contents = new_app_bundle / "Contents"
                old_contents = old_app_bundle / "Contents"
                
                # Sauvegarder Resources/Data/ si elle existe
                old_resources_data = old_contents / "Resources" / "Data"
                temp_resources_data = None
                if old_resources_data.exists():
                    temp_resources_data = app_dir / "temp_resources_data_backup"
                    if temp_resources_data.exists():
                        shutil.rmtree(temp_resources_data)
                    shutil.copytree(old_resources_data, temp_resources_data)
                
                # Remplacer MacOS/ (exécutable)
                new_macos = new_contents / "MacOS"
                old_macos = old_contents / "MacOS"
                if new_macos.exists() and old_macos.exists():
                    shutil.rmtree(old_macos)
                    shutil.copytree(new_macos, old_macos)
                    logger.info("  - Mise à jour de Contents/MacOS/")
                
                # Remplacer Frameworks/ si présent
                new_frameworks = new_contents / "Frameworks"
                old_frameworks = old_contents / "Frameworks"
                if new_frameworks.exists():
                    if old_frameworks.exists():
                        shutil.rmtree(old_frameworks)
                    shutil.copytree(new_frameworks, old_frameworks)
                    logger.info("  - Mise à jour de Contents/Frameworks/")
                
                # Remplacer Resources/ sauf Data/
                new_resources = new_contents / "Resources"
                old_resources = old_contents / "Resources"
                if new_resources.exists():
                    # Copier les fichiers de Resources/ sauf Data/
                    for item in new_resources.iterdir():
                        if item.name != "Data":
                            old_item = old_resources / item.name
                            if old_item.exists():
                                if old_item.is_dir():
                                    shutil.rmtree(old_item)
                                else:
                                    old_item.unlink()
                            if item.is_dir():
                                shutil.copytree(item, old_item)
                            else:
                                shutil.copy2(item, old_item)
                    logger.info("  - Mise à jour de Contents/Resources/ (sauf Data/)")
                
                # Restaurer Resources/Data/ si elle existait
                if temp_resources_data and temp_resources_data.exists():
                    old_resources_data = old_contents / "Resources" / "Data"
                    if old_resources_data.exists():
                        shutil.rmtree(old_resources_data)
                    shutil.copytree(temp_resources_data, old_resources_data)
                    shutil.rmtree(temp_resources_data)
                    logger.info("  - Restauration de Contents/Resources/Data/")
                
                # Remplacer Info.plist
                new_info_plist = new_contents / "Info.plist"
                old_info_plist = old_contents / "Info.plist"
                if new_info_plist.exists():
                    if old_info_plist.exists():
                        old_info_plist.unlink()
                    shutil.copy2(new_info_plist, old_info_plist)
                    logger.info("  - Mise à jour de Contents/Info.plist")
        
        # Gérer Windows/Linux (dossier avec _internal)
        elif new_app_dir:
            # Remplacer _internal (code de l'application)
            new_internal = new_app_dir / "_internal"
            old_internal = app_dir / "_internal"
            
            if new_internal.exists() and old_internal.exists():
                logger.info("  - Mise à jour de _internal/")
                shutil.rmtree(old_internal)
                shutil.copytree(new_internal, old_internal)
            
            # Remplacer l'exécutable principal
            for exe_name in ["PepiniereValbray.exe", "PepiniereValbray"]:
                new_exe = new_app_dir / exe_name
                old_exe = app_dir / exe_name
                if new_exe.exists():
                    if old_exe.exists():
                        old_exe.unlink()
                    shutil.copy2(new_exe, old_exe)
                    logger.info(f"  - Mise à jour de {exe_name}")
        
        # 5. Restaurer les données utilisateur depuis la sauvegarde
        restore_user_data(backup_dir, app_dir)
        
        # 5.1. Gérer meteo_dataset.csv de manière conditionnelle
        # Si le fichier existe déjà localement (utilisateur l'a utilisé/modifié), le protéger
        # Sinon, le copier depuis la nouvelle version (première installation)
        data_dir = get_user_data_dir(app_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        
        local_meteo = data_dir / "meteo_dataset.csv"
        
        # Chercher meteo_dataset.csv dans la nouvelle version (peut être dans _internal ou data/)
        new_meteo_path = None
        
        # Chercher meteo_dataset.csv dans la nouvelle version
        # Pour macOS .app
        if new_app_bundle:
            new_meteo_in_resources = new_app_bundle / "Contents" / "Resources" / "meteo_dataset.csv"
            if new_meteo_in_resources.exists():
                new_meteo_path = new_meteo_in_resources
            else:
                # Chercher dans _internal du bundle (si présent)
                new_meteo_in_internal = new_app_bundle / "Contents" / "Resources" / "_internal" / "meteo_dataset.csv"
                if new_meteo_in_internal.exists():
                    new_meteo_path = new_meteo_in_internal
        # Pour Windows/Linux
        elif new_app_dir:
            # Chercher dans _internal (où PyInstaller place les fichiers de données)
            new_meteo_in_internal = new_app_dir / "_internal" / "meteo_dataset.csv"
            if new_meteo_in_internal.exists():
                new_meteo_path = new_meteo_in_internal
            else:
                # Chercher dans data/ de la nouvelle version
                new_meteo_in_data = new_app_dir / "data" / "meteo_dataset.csv"
                if new_meteo_in_data.exists():
                    new_meteo_path = new_meteo_in_data
        
        if new_meteo_path:
            if local_meteo.exists():
                # Le fichier existe déjà localement : le protéger (ne pas l'écraser)
                logger.info("  - meteo_dataset.csv existe déjà localement, préservation de la version utilisateur")
            else:
                # Première installation : copier depuis la nouvelle version
                logger.info("  - Copie de meteo_dataset.csv depuis la nouvelle version (première installation)")
                shutil.copy2(new_meteo_path, local_meteo)
        
        # 6. Exécuter les migrations de base de données si nécessaire
        # Le fichier de base de données est maintenant dans le dossier de données utilisateur
        data_dir = get_user_data_dir(app_dir)
        db_path = data_dir / "recoltes.db"
        if db_path.exists():
            current_schema_version = get_db_schema_version(db_path)
            if current_schema_version < target_schema_version:
                logger.info(f"Mise à jour du schéma de la base de données...")
                run_database_migrations(db_path, current_schema_version, target_schema_version)
            else:
                logger.info("Schéma de la base de données à jour")
        
        # 7. Enregistrer la version installée
        # Récupérer la version depuis les informations de la release
        try:
            update_info = check_for_updates(include_prerelease=True)
            if update_info.get("available"):
                installed_version = update_info.get("latest_version")
                version_file = app_dir / VERSION_FILE
                # Pour macOS .app, placer le fichier dans Resources/Data/
                if app_dir.suffix == ".app" or (app_dir / "Contents").exists():
                    data_dir = get_user_data_dir(app_dir)
                    version_file = data_dir / VERSION_FILE
                else:
                    version_file = app_dir / VERSION_FILE
                version_file.parent.mkdir(parents=True, exist_ok=True)
                version_file.write_text(installed_version)
                logger.info(f"Version installée enregistrée : {installed_version}")
        except Exception as e:
            logger.warning(f"Impossible d'enregistrer la version installée : {e}")
        
        # 8. Nettoyer
        logger.info("Nettoyage des fichiers temporaires...")
        shutil.rmtree(extract_dir)
        zip_path.unlink()
        
        # Garder le backup pendant 7 jours (optionnel)
        # Vous pouvez ajouter une logique pour supprimer les anciens backups
        
        logger.info("✅ Mise à jour installée avec succès !")
        logger.info("⚠️  Redémarrez l'application pour appliquer les changements.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'installation : {e}")
        # En cas d'erreur, restaurer depuis la sauvegarde
        if backup_dir.exists():
            logger.info("Tentative de restauration depuis la sauvegarde...")
            try:
                restore_user_data(backup_dir, app_dir)
                logger.info("Données restaurées depuis la sauvegarde")
            except Exception as restore_error:
                logger.error(f"Erreur lors de la restauration : {restore_error}")
        raise

