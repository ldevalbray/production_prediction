"""
Configuration du système de logging pour l'application
"""
import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler

# Import de la configuration
try:
    from config import LOG_LEVEL, LOG_FILE, LOG_FORMAT
except ImportError:
    LOG_LEVEL = "INFO"
    LOG_FILE = "app.log"
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"


def setup_logging():
    """
    Configure le système de logging pour l'application.
    Logs à la fois dans un fichier et dans la console.
    """
    # Créer le dossier de logs si nécessaire
    log_path = Path(LOG_FILE)
    if log_path.parent != Path('.'):
        log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Configuration du format
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Handler pour fichier avec rotation
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Handler pour console
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Configuration du logger racine
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    # Supprimer les handlers existants pour éviter les doublons
    root_logger.handlers.clear()
    
    # Ajouter les handlers
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Logger spécifique pour l'application
    app_logger = logging.getLogger('pepiniere_valbray')
    app_logger.setLevel(getattr(logging, LOG_LEVEL.upper(), logging.INFO))
    
    return app_logger


# Initialiser le logging au chargement du module
logger = setup_logging()

