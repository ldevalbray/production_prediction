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
import os
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

def safe_remove(path: Path, critical: bool = False):
    """
    Supprime un fichier ou dossier de manière sécurisée, en gérant les liens symboliques.
    
    Args:
        path: Chemin vers le fichier/dossier à supprimer
        critical: Si True, lève une exception en cas d'échec (pour les opérations critiques)
    """
    if not path.exists():
        return
    
    try:
        # Vérifier si c'est un lien symbolique (doit être vérifié AVANT is_file/is_dir)
        # Utiliser os.path.islink() qui est plus fiable que path.is_symlink() dans certains cas
        if os.path.islink(str(path)) or path.is_symlink():
            path.unlink()  # Supprimer le lien symbolique (NE JAMAIS utiliser rmtree)
            logger.debug(f"Lien symbolique supprimé : {path}")
            return
        elif path.is_file():
            path.unlink()  # Supprimer le fichier
            logger.debug(f"Fichier supprimé : {path}")
            return
        elif path.is_dir():
            # VÉRIFICATION CRITIQUE : Ne JAMAIS appeler rmtree sur un lien symbolique
            # Vérifier une dernière fois avant d'appeler rmtree (au cas où le statut aurait changé)
            if os.path.islink(str(path)) or path.is_symlink():
                path.unlink()
                logger.debug(f"Lien symbolique (dossier) supprimé : {path}")
                return
            
            # Pour les dossiers, utiliser une méthode qui gère les liens symboliques
            # IMPORTANT: Ne jamais appeler rmtree directement, toujours vérifier les liens d'abord
            def handle_remove_readonly(func, path_str, exc_info):
                """Gère les erreurs lors de la suppression, notamment les liens symboliques."""
                try:
                    # Vérifier si c'est un lien symbolique AVANT toute autre opération
                    # C'est CRITIQUE : rmtree ne peut JAMAIS être appelé sur un lien symbolique
                    if os.path.islink(path_str):
                        # C'est un lien symbolique : utiliser unlink uniquement
                        os.unlink(path_str)
                        return  # CRITIQUE : ne JAMAIS appeler func() (rmtree) sur un lien symbolique
                    
                    # Vérifier avec Path aussi
                    try:
                        path_obj = Path(path_str)
                        if path_obj.is_symlink():
                            os.unlink(path_str)
                            return  # CRITIQUE : ne JAMAIS appeler func() sur un lien symbolique
                    except:
                        pass
                    
                    # Ce n'est PAS un lien symbolique, on peut essayer de changer les permissions
                    try:
                        os.chmod(path_str, 0o777)
                        func(path_str)
                    except Exception:
                        # Si ça échoue, essayer unlink comme dernier recours
                        try:
                            os.unlink(path_str)
                        except:
                            pass
                except Exception as e:
                    logger.debug(f"Erreur dans handle_remove_readonly pour {path_str} : {e}")
                    # Dernier recours : si c'est un lien, utiliser unlink (NE JAMAIS appeler func)
                    try:
                        if os.path.islink(path_str):
                            os.unlink(path_str)
                    except:
                        pass
            
            try:
                # Vérifier une dernière fois avant d'appeler rmtree
                if os.path.islink(str(path)) or path.is_symlink():
                    path.unlink()
                    logger.debug(f"Lien symbolique détecté avant rmtree, supprimé avec unlink : {path}")
                    return
                
                # Essayer d'abord avec rmtree standard (mais avec gestion d'erreur)
                # rmtree ne devrait jamais être appelé sur un lien symbolique grâce aux vérifications
                shutil.rmtree(str(path), onerror=handle_remove_readonly)
                logger.debug(f"Dossier supprimé : {path}")
            except (OSError, PermissionError) as e:
                # Si l'erreur mentionne "symbolic link", c'est qu'on a raté une vérification
                error_msg = str(e).lower()
                if 'symbolic link' in error_msg or 'symlink' in error_msg:
                    logger.warning(f"Lien symbolique détecté dans l'erreur, utilisation de unlink : {path}")
                    try:
                        if os.path.islink(str(path)) or path.is_symlink():
                            path.unlink()
                            return
                    except:
                        pass
                
                # Si ça échoue, supprimer manuellement élément par élément
                logger.warning(f"Erreur lors de la suppression de {path} : {e}, tentative de suppression manuelle")
                _remove_directory_manually(path)
                # Vérifier que la suppression a réussi
                if path.exists() and critical:
                    raise Exception(f"Impossible de supprimer {path}")
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de {path} : {e}")
        if critical:
            raise  # Lever l'exception pour les opérations critiques
        # Sinon, juste logger l'erreur pour ne pas bloquer la mise à jour

def _remove_directory_manually(path: Path):
    """
    Supprime un dossier manuellement en gérant les liens symboliques.
    Fonction helper pour safe_remove.
    IMPORTANT: Ne suit PAS les liens symboliques pour éviter les boucles infinies.
    """
    try:
        # Parcourir récursivement et supprimer chaque élément
        # Utiliser followlinks=False pour NE PAS suivre les liens symboliques
        for root, dirs, files in os.walk(path, topdown=False, followlinks=False):
            # Supprimer les fichiers
            for file in files:
                file_path = Path(root) / file
                try:
                    # Toujours utiliser unlink pour les fichiers (gère les liens symboliques)
                    if file_path.exists() or file_path.is_symlink():
                        file_path.unlink()
                except (OSError, PermissionError) as e:
                    logger.warning(f"Impossible de supprimer {file_path} : {e}")
                except Exception as e:
                    logger.warning(f"Erreur inattendue lors de la suppression de {file_path} : {e}")
            
            # Supprimer les dossiers (après avoir supprimé leur contenu)
            for dir_name in dirs:
                dir_path = Path(root) / dir_name
                try:
                    # Vérifier si c'est un lien symbolique AVANT d'essayer rmdir
                    if dir_path.is_symlink():
                        dir_path.unlink()
                    elif dir_path.exists():
                        # Essayer rmdir seulement si ce n'est pas un lien symbolique
                        try:
                            dir_path.rmdir()
                        except OSError:
                            # Le dossier n'est pas vide, continuer
                            pass
                except (OSError, PermissionError) as e:
                    logger.warning(f"Impossible de supprimer {dir_path} : {e}")
                except Exception as e:
                    logger.warning(f"Erreur inattendue lors de la suppression de {dir_path} : {e}")
        
        # Finalement, supprimer le dossier racine
        try:
            if path.is_symlink():
                path.unlink()
            elif path.exists():
                # Essayer rmdir d'abord
                try:
                    path.rmdir()
                except OSError:
                    # Si rmdir échoue, vérifier s'il reste des fichiers
                    # Si oui, essayer une dernière fois avec rmtree en gérant les erreurs
                    try:
                        # Utiliser onerror pour gérer les liens symboliques
                        def handle_error(func, path_str, exc_info):
                            path_obj = Path(path_str)
                            if path_obj.is_symlink() or os.path.islink(path_str):
                                os.unlink(path_str)
                            else:
                                # Ignorer l'erreur
                                pass
                        shutil.rmtree(str(path), onerror=handle_error)
                    except Exception:
                        # Dernier recours : ignorer complètement
                        pass
        except (OSError, PermissionError) as e:
            logger.warning(f"Impossible de supprimer le dossier racine {path} : {e}")
        except Exception as e:
            logger.warning(f"Erreur inattendue lors de la suppression du dossier racine {path} : {e}")
    except Exception as e:
        logger.warning(f"Erreur lors de la suppression manuelle de {path} : {e}")

def safe_copytree(src: Path, dst: Path, ignore_symlinks: bool = True):
    """
    Copie un dossier de manière sécurisée, en gérant les liens symboliques.
    
    Args:
        src: Source
        dst: Destination
        ignore_symlinks: Si True, ignore les liens symboliques (recommandé pour éviter les problèmes)
    """
    try:
        # Créer le dossier de destination s'il n'existe pas
        dst.mkdir(parents=True, exist_ok=True)
        
        # Utiliser copytree avec une fonction d'ignore pour les liens symboliques si nécessaire
        if ignore_symlinks:
            def ignore_symlink(dir, files):
                """Ignore les liens symboliques lors de la copie."""
                ignored = []
                for file in files:
                    file_path = Path(dir) / file
                    if file_path.is_symlink():
                        ignored.append(file)
                        logger.debug(f"Lien symbolique ignoré lors de la copie : {file_path}")
                return ignored
            
            shutil.copytree(str(src), str(dst), dirs_exist_ok=True, ignore=ignore_symlink)
        else:
            # Copier normalement mais gérer les erreurs
            shutil.copytree(str(src), str(dst), dirs_exist_ok=True)
    except Exception as e:
        logger.error(f"Erreur lors de la copie de {src} vers {dst} : {e}")
        raise

def get_current_version():
    """
    Retourne la version actuelle de l'application.
    Essaie de lire depuis le fichier installed_version.txt, sinon utilise la version par défaut.
    """
    from pyinstaller_utils import get_base_path
    import sys
    
    # Essayer de lire depuis le fichier de version installée
    try:
        base_path = get_base_path()
        
        # Pour macOS .app, chercher dans le dossier de données
        version_file = None
        if sys.platform == "darwin" and (base_path.suffix == ".app" or (base_path / "Contents").exists()):
            # Chercher dans le dossier de données utilisateur
            data_dir = get_user_data_dir(base_path)
            version_file = data_dir / VERSION_FILE
            # Fallback : chercher aussi à la racine du bundle
            if not version_file.exists():
                version_file = base_path / VERSION_FILE
        else:
            version_file = base_path / VERSION_FILE
        
        if version_file.exists():
            version = version_file.read_text().strip()
            if version:
                logger.info(f"Version lue depuis {version_file}: {version}")
                return version
            else:
                logger.warning(f"Fichier de version vide : {version_file}")
        else:
            logger.info(f"Fichier de version introuvable : {version_file}")
    except Exception as e:
        logger.warning(f"Impossible de lire la version depuis le fichier : {e}")
    
    # Fallback : version par défaut
    logger.info(f"Utilisation de la version par défaut: {DEFAULT_APP_VERSION}")
    return DEFAULT_APP_VERSION

def check_for_updates(include_prerelease=False):
    """
    Vérifie s'il y a une nouvelle version disponible sur GitHub.
    
    Args:
        include_prerelease: Si True, inclut les prereleases (builds automatiques)
    """
    try:
        logger.info(f"Vérification des mises à jour (include_prerelease={include_prerelease})...")
        
        # Si on veut inclure les prereleases, on doit récupérer toutes les releases
        if include_prerelease:
            releases_url = f"https://api.github.com/repos/{GITHUB_REPO}/releases"
            response = requests.get(releases_url, timeout=10, params={"per_page": 10})
            response.raise_for_status()
            releases = response.json()
            
            # Prendre la première release (la plus récente)
            if releases:
                release_data = releases[0]
            else:
                logger.info("Aucune release trouvée")
                return {"available": False}
        else:
            # Sinon, utiliser l'endpoint /latest qui exclut les prereleases
            response = requests.get(UPDATE_CHECK_URL, timeout=10)
            response.raise_for_status()
            release_data = response.json()
        
        latest_version = release_data.get("tag_name", "").lstrip("v")
        if not latest_version:
            logger.warning("Aucun tag_name trouvé dans la release")
            return {"available": False}
        
        logger.info(f"Version la plus récente trouvée sur GitHub : {latest_version}")
        
        current_version = get_current_version()
        logger.info(f"Version actuelle de l'application : {current_version}")
        
        # Si on est à la version par défaut (fichier n'existe pas), 
        # enregistrer la version de la release actuelle comme version installée
        # Cela permet de détecter les futures mises à jour
        if current_version == DEFAULT_APP_VERSION:
            try:
                from pyinstaller_utils import get_base_path
                base_path = get_base_path()
                
                # Pour macOS .app, placer le fichier dans le dossier de données
                if sys.platform == "darwin" and (base_path.suffix == ".app" or (base_path / "Contents").exists()):
                    # Trouver le dossier de données
                    data_dir = get_user_data_dir(base_path)
                    version_file = data_dir / VERSION_FILE
                else:
                    version_file = base_path / VERSION_FILE
                
                version_file.parent.mkdir(parents=True, exist_ok=True)
                version_file.write_text(latest_version)
                logger.info(f"Version initiale enregistrée dans {version_file}: {latest_version}")
                # Ne pas changer current_version ici, on veut comparer avec la version par défaut
            except Exception as e:
                logger.warning(f"Impossible d'enregistrer la version initiale : {e}")
        
        # Comparer les versions (gérer les formats comme "20250101-abc1234")
        is_newer = False
        try:
            # Essayer de parser comme version normale (semver)
            latest_ver = version.parse(latest_version)
            current_ver = version.parse(current_version)
            is_newer = latest_ver > current_ver
            logger.info(f"Comparaison de versions : {latest_ver} > {current_ver} = {is_newer}")
        except Exception as parse_error:
            # Si le parsing échoue (format date-SHA), comparer les strings
            # Pour les builds automatiques, on considère toujours qu'il y a une mise à jour
            # si la version est différente
            is_newer = latest_version != current_version
            logger.info(f"Comparaison de versions (string) : '{latest_version}' != '{current_version}' = {is_newer}")
            logger.debug(f"Erreur de parsing (normal pour formats non-semver) : {parse_error}")
        
        if is_newer:
            logger.info(f"✅ Nouvelle version disponible : {latest_version} (actuelle : {current_version})")
            return {
                "available": True,
                "latest_version": latest_version,
                "current_version": current_version,
                "release_url": release_data.get("html_url", ""),
                "release_notes": release_data.get("body", ""),
                "assets": release_data.get("assets", []),
                "prerelease": release_data.get("prerelease", False)
            }
        else:
            logger.info(f"L'application est à jour (version {current_version})")
            return {"available": False, "current_version": current_version, "latest_version": latest_version}
    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur réseau lors de la vérification des mises à jour : {e}")
        return {"available": False, "error": f"Erreur réseau : {str(e)}"}
    except Exception as e:
        logger.error(f"Erreur lors de la vérification des mises à jour : {e}", exc_info=True)
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
        safe_copytree(data_dir, dest)
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
            safe_copytree(src, dest)
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
            safe_remove(data_dir)
        safe_copytree(backup_data, data_dir)
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
                safe_remove(dest)
            safe_copytree(src, dest)
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

def _check_disk_space(path: Path, required_bytes: int) -> bool:
    """Vérifie qu'il y a assez d'espace disque disponible."""
    try:
        import shutil
        stat = shutil.disk_usage(path)
        available = stat.free
        # Nécessiter au moins 2x l'espace requis (pour sécurité)
        if available < required_bytes * 2:
            logger.error(f"Espace disque insuffisant : {available / 1024 / 1024:.1f} MB disponible, "
                        f"{required_bytes * 2 / 1024 / 1024:.1f} MB requis")
            return False
        return True
    except Exception as e:
        logger.warning(f"Impossible de vérifier l'espace disque : {e}")
        return True  # Continuer si on ne peut pas vérifier

def _check_write_permissions(path: Path) -> bool:
    """Vérifie qu'on a les permissions d'écriture."""
    try:
        # Essayer de créer un fichier test
        test_file = path / ".write_test"
        test_file.write_text("test")
        test_file.unlink()
        return True
    except (PermissionError, OSError) as e:
        logger.error(f"Pas de permissions d'écriture dans {path} : {e}")
        return False
    except Exception as e:
        logger.warning(f"Erreur lors de la vérification des permissions : {e}")
        return True  # Continuer si on ne peut pas vérifier

def _verify_file_integrity(file_path: Path, expected_size: int = None) -> bool:
    """Vérifie l'intégrité d'un fichier."""
    try:
        if not file_path.exists():
            logger.error(f"Fichier introuvable : {file_path}")
            return False
        if expected_size and file_path.stat().st_size != expected_size:
            logger.error(f"Taille de fichier incorrecte : {file_path}")
            return False
        return True
    except Exception as e:
        logger.error(f"Erreur lors de la vérification de {file_path} : {e}")
        return False

def _find_app_bundle(app_dir: Path) -> Path:
    """
    Trouve le bundle .app à partir de app_dir qui peut être Contents/Resources/Data/.
    
    Args:
        app_dir: Chemin qui peut être le bundle .app, Contents/Resources/Data/, ou autre
        
    Returns:
        Le chemin du bundle .app
    """
    # Si app_dir est déjà le bundle .app
    if app_dir.suffix == ".app" and (app_dir / "Contents").exists():
        return app_dir
    
    # Si app_dir pointe vers Contents/Resources/Data/, remonter jusqu'au .app
    current_path = app_dir
    max_depth = 10
    depth = 0
    
    while current_path != current_path.parent and depth < max_depth:
        # Vérifier si on est dans un bundle .app
        if current_path.suffix == ".app" and (current_path / "Contents").exists():
            return current_path
        
        # Vérifier si le parent est un bundle .app
        parent = current_path.parent
        if parent.suffix == ".app" and (parent / "Contents").exists():
            return parent
        
        # Vérifier si un .app est dans le dossier courant
        if current_path.is_dir():
            for item in current_path.iterdir():
                if item.suffix == ".app" and (item / "Contents").exists():
                    return item
        
        current_path = current_path.parent
        depth += 1
    
    # Si on ne trouve pas, retourner app_dir tel quel
    return app_dir

def install_update(zip_path: Path, app_dir: Path, target_schema_version: int = 1):
    """
    Installe la mise à jour en préservant toutes les données utilisateur.
    
    Args:
        zip_path: Chemin vers le fichier ZIP de la mise à jour
        app_dir: Dossier de l'application (peut être le bundle .app ou Contents/Resources/Data/)
        target_schema_version: Version cible du schéma de base de données
    """
    backup_dir = None
    extract_dir = None
    temp_resources_data = None
    
    try:
        logger.info("Début de l'installation de la mise à jour")
        
        # Trouver le bundle .app réel (app_dir peut être Contents/Resources/Data/)
        app_bundle = _find_app_bundle(app_dir)
        logger.info(f"Bundle .app détecté : {app_bundle}")
        logger.info(f"app_dir fourni : {app_dir}")
        
        # Déterminer le dossier parent pour les fichiers temporaires (accessible en écriture)
        if sys.platform == "darwin" and app_bundle.suffix == ".app":
            # Sur macOS, utiliser le dossier parent du bundle .app
            parent_dir = app_bundle.parent
        else:
            # Pour Windows/Linux, utiliser le dossier de l'app
            parent_dir = app_bundle
        
        # Vérifications préliminaires
        if not zip_path.exists():
            raise Exception(f"Fichier ZIP introuvable : {zip_path}")
        
        if not app_bundle.exists():
            raise Exception(f"Bundle de l'application introuvable : {app_bundle}")
        
        # Vérifier les permissions d'écriture dans le dossier parent (pour la sauvegarde temporaire)
        if not _check_write_permissions(parent_dir):
            raise Exception(f"Pas de permissions d'écriture dans {parent_dir}")
        
        # Vérifier l'espace disque (estimer 3x la taille du ZIP)
        zip_size = zip_path.stat().st_size
        if not _check_disk_space(parent_dir, zip_size * 3):
            raise Exception("Espace disque insuffisant pour la mise à jour")
        
        # 1. Créer une sauvegarde complète
        backup_dir = backup_user_data(app_bundle)
        if not backup_dir.exists():
            raise Exception("Échec de la création de la sauvegarde")
        
        # 2. Extraire la nouvelle version dans un dossier temporaire
        # Utiliser le dossier parent pour l'extraction (accessible en écriture)
        extract_dir = parent_dir / f"update_temp_{app_bundle.name}"
        if extract_dir.exists():
            safe_remove(extract_dir, critical=True)  # Critique : doit pouvoir supprimer l'ancien extract_dir
        extract_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Extraction de la mise à jour dans {extract_dir}")
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                # Vérifier l'intégrité du ZIP avant extraction
                bad_file = zip_ref.testzip()
                if bad_file:
                    raise Exception(f"Archive ZIP corrompue : {bad_file}")
                
                # Extraire
                zip_ref.extractall(extract_dir)
                
                # Vérifier que l'extraction a réussi (au moins un fichier)
                if not any(extract_dir.rglob("*")):
                    raise Exception("L'extraction du ZIP n'a produit aucun fichier")
        except zipfile.BadZipFile as e:
            raise Exception(f"Fichier ZIP invalide : {e}")
        except Exception as e:
            raise Exception(f"Erreur lors de l'extraction : {e}")
        
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
            # Utiliser le bundle .app trouvé précédemment
            old_app_bundle = app_bundle
            
            if not old_app_bundle or not old_app_bundle.exists():
                raise Exception(f"Bundle .app existant introuvable : {app_bundle}. Impossible de mettre à jour.")
            
            # Mettre à jour le bundle .app
            if old_app_bundle:
                logger.info(f"  - Mise à jour du bundle .app : {old_app_bundle}")
                # Remplacer Contents/ sauf Resources/Data/ (données utilisateur)
                new_contents = new_app_bundle / "Contents"
                old_contents = old_app_bundle / "Contents"
                
                # Sauvegarder Resources/Data/ si elle existe
                old_resources_data = old_contents / "Resources" / "Data"
                if old_resources_data.exists():
                    # Sur macOS, on ne peut pas écrire dans le bundle .app
                    # Créer la sauvegarde temporaire dans le dossier parent (accessible en écriture)
                    temp_resources_data = parent_dir / f"temp_resources_data_backup_{app_bundle.name}"
                    
                    if temp_resources_data.exists():
                        safe_remove(temp_resources_data)
                    
                    # Créer le dossier parent si nécessaire
                    temp_resources_data.parent.mkdir(parents=True, exist_ok=True)
                    
                    safe_copytree(old_resources_data, temp_resources_data)
                    # Vérifier que la sauvegarde a réussi
                    if not temp_resources_data.exists():
                        raise Exception(f"Échec de la sauvegarde de Resources/Data/ vers {temp_resources_data}")
                    logger.info(f"  - Sauvegarde temporaire créée : {temp_resources_data}")
                
                # Remplacer MacOS/ (exécutable)
                new_macos = new_contents / "MacOS"
                old_macos = old_contents / "MacOS"
                if new_macos.exists() and old_macos.exists():
                    safe_remove(old_macos)
                    safe_copytree(new_macos, old_macos)
                    # Vérifier que la copie a réussi
                    if not old_macos.exists() or not any(old_macos.iterdir()):
                        raise Exception("Échec de la mise à jour de Contents/MacOS/")
                    logger.info("  - Mise à jour de Contents/MacOS/")
                
                # Remplacer Frameworks/ si présent
                new_frameworks = new_contents / "Frameworks"
                old_frameworks = old_contents / "Frameworks"
                if new_frameworks.exists():
                    if old_frameworks.exists():
                        safe_remove(old_frameworks)
                    safe_copytree(new_frameworks, old_frameworks)
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
                                safe_remove(old_item)
                            if item.is_dir():
                                safe_copytree(item, old_item)
                            else:
                                # Vérifier que ce n'est pas un lien symbolique avant de copier
                                if not item.is_symlink():
                                    shutil.copy2(item, old_item)
                                else:
                                    logger.debug(f"Lien symbolique ignoré : {item}")
                    logger.info("  - Mise à jour de Contents/Resources/ (sauf Data/)")
                
                # Restaurer Resources/Data/ si elle existait
                if temp_resources_data:
                    if temp_resources_data.exists():
                        old_resources_data = old_contents / "Resources" / "Data"
                        # Créer le dossier parent si nécessaire
                        old_resources_data.parent.mkdir(parents=True, exist_ok=True)
                        
                        if old_resources_data.exists():
                            safe_remove(old_resources_data)
                        safe_copytree(temp_resources_data, old_resources_data)
                        
                        # Vérifier que la restauration a réussi
                        if not old_resources_data.exists():
                            raise Exception(f"Échec de la restauration de Resources/Data/ depuis {temp_resources_data}")
                        
                        # Nettoyer la sauvegarde temporaire
                        safe_remove(temp_resources_data)
                        logger.info("  - Restauration de Contents/Resources/Data/")
                    else:
                        logger.warning(f"Sauvegarde temporaire introuvable : {temp_resources_data}, Resources/Data/ ne sera pas restauré")
                
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
            # Pour Windows/Linux, app_dir devrait pointer vers le dossier de l'app
            old_app_dir = app_bundle if app_bundle.suffix != ".app" else app_bundle.parent
            new_internal = new_app_dir / "_internal"
            old_internal = old_app_dir / "_internal"
            
            if new_internal.exists() and old_internal.exists():
                logger.info("  - Mise à jour de _internal/")
                safe_remove(old_internal)
                safe_copytree(new_internal, old_internal)
            
            # Remplacer l'exécutable principal
            for exe_name in ["PepiniereValbray.exe", "PepiniereValbray"]:
                new_exe = new_app_dir / exe_name
                old_exe = old_app_dir / exe_name
                if new_exe.exists():
                    if old_exe.exists():
                        old_exe.unlink()
                    shutil.copy2(new_exe, old_exe)
                    logger.info(f"  - Mise à jour de {exe_name}")
        
        # 5. Restaurer les données utilisateur depuis la sauvegarde
        restore_user_data(backup_dir, app_bundle)
        
        # 5.1. Gérer meteo_dataset.csv de manière conditionnelle
        # Si le fichier existe déjà localement (utilisateur l'a utilisé/modifié), le protéger
        # Sinon, le copier depuis la nouvelle version (première installation)
        data_dir = get_user_data_dir(app_bundle)
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
        data_dir = get_user_data_dir(app_bundle)
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
                # Pour macOS .app, placer le fichier dans Resources/Data/
                data_dir = get_user_data_dir(app_bundle)
                version_file = data_dir / VERSION_FILE
                version_file.parent.mkdir(parents=True, exist_ok=True)
                version_file.write_text(installed_version)
                logger.info(f"Version installée enregistrée : {installed_version}")
        except Exception as e:
            logger.warning(f"Impossible d'enregistrer la version installée : {e}")
        
        # 8. Nettoyer (seulement si tout s'est bien passé)
        logger.info("Nettoyage des fichiers temporaires...")
        try:
            if extract_dir and extract_dir.exists():
                safe_remove(extract_dir)
            if temp_resources_data:
                # Nettoyer la sauvegarde temporaire si elle existe encore
                if temp_resources_data.exists():
                    safe_remove(temp_resources_data)
                # Sur macOS, aussi nettoyer dans le dossier parent au cas où
                if sys.platform == "darwin" and app_bundle.suffix == ".app":
                    temp_backup_pattern = parent_dir / f"temp_resources_data_backup_{app_bundle.name}"
                    if temp_backup_pattern.exists():
                        safe_remove(temp_backup_pattern)
            if zip_path.exists():
                zip_path.unlink()
        except Exception as cleanup_error:
            logger.warning(f"Erreur lors du nettoyage (non critique) : {cleanup_error}")
        
        # Garder le backup pendant 7 jours (optionnel)
        # Vous pouvez ajouter une logique pour supprimer les anciens backups
        
        logger.info("✅ Mise à jour installée avec succès !")
        logger.info("⚠️  Redémarrez l'application pour appliquer les changements.")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Erreur lors de l'installation : {e}", exc_info=True)
        
        # Nettoyer les fichiers temporaires en cas d'erreur
        try:
            if extract_dir and extract_dir.exists():
                safe_remove(extract_dir)
            if temp_resources_data:
                if temp_resources_data.exists():
                    safe_remove(temp_resources_data)
                # Sur macOS, aussi nettoyer dans le dossier parent au cas où
                if sys.platform == "darwin" and app_bundle.suffix == ".app":
                    temp_backup_pattern = parent_dir / f"temp_resources_data_backup_{app_bundle.name}"
                    if temp_backup_pattern.exists():
                        safe_remove(temp_backup_pattern)
        except Exception as cleanup_error:
            logger.warning(f"Erreur lors du nettoyage après erreur : {cleanup_error}")
        
        # En cas d'erreur, restaurer depuis la sauvegarde
        if backup_dir and backup_dir.exists():
            logger.info("Tentative de restauration depuis la sauvegarde...")
            try:
                restore_user_data(backup_dir, app_bundle)
                logger.info("✅ Données restaurées depuis la sauvegarde")
            except Exception as restore_error:
                logger.error(f"❌ Erreur critique lors de la restauration : {restore_error}", exc_info=True)
                logger.error("⚠️  Les données peuvent être dans backup_before_update/")
                # Ne pas lever d'exception ici pour permettre à l'utilisateur de restaurer manuellement
        
        # Lever l'exception originale pour signaler l'échec
        raise

