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

# Version actuelle de l'application
APP_VERSION = "1.0.0"  # ⚠️ À mettre à jour à chaque release
GITHUB_REPO = "ldevalbray/production_prediction"  # Votre repo GitHub
UPDATE_CHECK_URL = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

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
    """Retourne la version actuelle de l'application."""
    return APP_VERSION

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

def migrate_old_files_to_data_dir(app_dir: Path):
    """
    Migre les anciens fichiers de données de la racine vers le dossier data/.
    Cette fonction est appelée pour assurer la compatibilité avec les anciennes versions.
    """
    data_dir = app_dir / "data"
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
    
    # Sauvegarder les fichiers protégés
    for filename in PROTECTED_FILES:
        src = app_dir / filename
        if src.exists():
            if src.is_file():
                shutil.copy2(src, backup_dir / filename)
                logger.info(f"  - Sauvegardé : {filename}")
    
    # Sauvegarder les dossiers protégés
    for dirname in PROTECTED_DIRS:
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
    
    # Restaurer les fichiers
    for filename in PROTECTED_FILES:
        src = backup_dir / filename
        if src.exists():
            dest = app_dir / filename
            shutil.copy2(src, dest)
            logger.info(f"  - Restauré : {filename}")
    
    # Restaurer les dossiers
    for dirname in PROTECTED_DIRS:
        src = backup_dir / dirname
        if src.exists():
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
        # L'archive contient généralement dist/PepiniereValbray/
        new_app_dir = None
        for item in extract_dir.rglob("PepiniereValbray"):
            if item.is_dir() and (item / "_internal").exists():
                new_app_dir = item
                break
        
        if not new_app_dir:
            # Fallback : chercher le premier dossier avec _internal
            for item in extract_dir.iterdir():
                if item.is_dir() and (item / "_internal").exists():
                    new_app_dir = item
                    break
        
        if not new_app_dir:
            raise Exception("Structure de l'archive invalide : dossier PepiniereValbray introuvable")
        
        # 4. Remplacer les fichiers de l'application (SAUF les données utilisateur)
        logger.info("Remplacement des fichiers de l'application...")
        
        # Liste des fichiers/dossiers à exclure (données utilisateur)
        exclude_items = set(PROTECTED_FILES + PROTECTED_DIRS)
        
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
        
        # 6. Exécuter les migrations de base de données si nécessaire
        # Le fichier de base de données est maintenant dans data/
        db_path = app_dir / "data" / "recoltes.db"
        if db_path.exists():
            current_schema_version = get_db_schema_version(db_path)
            if current_schema_version < target_schema_version:
                logger.info(f"Mise à jour du schéma de la base de données...")
                run_database_migrations(db_path, current_schema_version, target_schema_version)
            else:
                logger.info("Schéma de la base de données à jour")
        
        # 7. Nettoyer
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

