"""
Utilitaires pour gérer l'exécution dans un exécutable PyInstaller.
"""
import sys
import os
from pathlib import Path

def is_pyinstaller():
    """Détecte si le code s'exécute dans un exécutable PyInstaller."""
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

def get_base_path():
    """Retourne le chemin de base de l'application.
    
    Dans un exécutable PyInstaller, retourne le dossier de l'exécutable.
    Sinon, retourne le dossier du script.
    """
    if is_pyinstaller():
        # Dans un exécutable, le chemin de base est le dossier de l'exécutable
        return Path(sys.executable).parent
    else:
        # En développement, le chemin de base est le dossier du script
        return Path(__file__).parent

def get_resource_path(relative_path):
    """Retourne le chemin absolu d'une ressource.
    
    Dans un exécutable PyInstaller, les ressources sont dans sys._MEIPASS.
    Sinon, elles sont dans le dossier du script.
    """
    if is_pyinstaller():
        # Les fichiers de données sont dans le dossier temporaire PyInstaller
        base_path = Path(sys._MEIPASS)
    else:
        # En développement, les fichiers sont dans le dossier du script
        base_path = Path(__file__).parent
    
    return base_path / relative_path

def get_script_path(script_name):
    """Retourne le chemin d'un script Python.
    
    Dans un exécutable PyInstaller, essaie de trouver le script dans sys._MEIPASS.
    Sinon, retourne le chemin relatif normal.
    """
    if is_pyinstaller():
        # Dans un exécutable, les scripts sont dans sys._MEIPASS
        script_path = Path(sys._MEIPASS) / script_name
        if script_path.exists():
            return str(script_path)
        # Sinon, essayer dans le dossier de l'exécutable
        script_path = Path(sys.executable).parent / script_name
        if script_path.exists():
            return str(script_path)
    
    # En développement ou si non trouvé, retourner le nom du script
    return script_name

