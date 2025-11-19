"""
Utilitaires de cache pour améliorer les performances
Utilise functools.lru_cache pour un cache simple en mémoire
"""
from functools import lru_cache
from typing import Optional
import pandas as pd

# Import de la configuration
try:
    from config import CACHE_ENABLED, CACHE_TTL
except ImportError:
    CACHE_ENABLED = True
    CACHE_TTL = 300  # 5 minutes par défaut

# Cache pour les paramètres (données relativement statiques)
@lru_cache(maxsize=128)
def get_parametres_cached():
    """Récupère les paramètres avec cache."""
    if not CACHE_ENABLED:
        from database import get_parametres
        return get_parametres()
    
    from database import get_parametres
    return get_parametres()

# Cache pour la configuration de récolte quotidienne
@lru_cache(maxsize=32)
def get_recolte_quotidienne_cached():
    """Récupère la configuration de récolte quotidienne avec cache."""
    if not CACHE_ENABLED:
        from database import get_recolte_quotidienne
        return get_recolte_quotidienne()
    
    from database import get_recolte_quotidienne
    return get_recolte_quotidienne()

# Fonction pour invalider le cache
def clear_cache():
    """Invalide tous les caches."""
    get_parametres_cached.cache_clear()
    get_recolte_quotidienne_cached.cache_clear()

