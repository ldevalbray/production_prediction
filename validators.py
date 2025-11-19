"""
Module de validation des données pour l'API
Utilise des validations simples sans dépendances externes
"""
from datetime import datetime
from typing import Optional
import re

# Import de la configuration
try:
    from config import (
        MAX_VARIETY_LENGTH, MAX_PARCelle_LENGTH, MAX_COMMENT_LENGTH,
        MIN_KG_TOTAL, MAX_KG_TOTAL
    )
except ImportError:
    # Valeurs par défaut si config n'est pas disponible
    MAX_VARIETY_LENGTH = 50
    MAX_PARCelle_LENGTH = 50
    MAX_COMMENT_LENGTH = 500
    MIN_KG_TOTAL = 0
    MAX_KG_TOTAL = 10000


class ValidationError(Exception):
    """Exception levée lors d'une erreur de validation."""
    pass


def validate_variety(variety: str) -> str:
    """Valide et normalise une variété."""
    if not variety or not isinstance(variety, str):
        raise ValidationError("La variété est requise et doit être une chaîne de caractères")
    
    variety = variety.strip()
    if not variety:
        raise ValidationError("La variété ne peut pas être vide")
    
    if len(variety) > MAX_VARIETY_LENGTH:
        raise ValidationError(f"La variété ne peut pas dépasser {MAX_VARIETY_LENGTH} caractères")
    
    return variety.lower()


def validate_parcelle(parcelle: str) -> str:
    """Valide et normalise une parcelle."""
    if not parcelle or not isinstance(parcelle, str):
        raise ValidationError("La parcelle est requise et doit être une chaîne de caractères")
    
    parcelle = parcelle.strip()
    if not parcelle:
        raise ValidationError("La parcelle ne peut pas être vide")
    
    if len(parcelle) > MAX_PARCelle_LENGTH:
        raise ValidationError(f"La parcelle ne peut pas dépasser {MAX_PARCelle_LENGTH} caractères")
    
    return parcelle.lower()


def validate_date(date_str: str) -> str:
    """Valide une date au format YYYY-MM-DD."""
    if not date_str or not isinstance(date_str, str):
        raise ValidationError("La date est requise et doit être une chaîne de caractères")
    
    date_str = date_str.strip()
    
    # Format attendu : YYYY-MM-DD
    date_pattern = re.compile(r'^\d{4}-\d{2}-\d{2}$')
    if not date_pattern.match(date_str):
        raise ValidationError("La date doit être au format YYYY-MM-DD (ex: 2025-01-15)")
    
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
    except ValueError:
        raise ValidationError(f"Date invalide : {date_str}")
    
    return date_str


def validate_kg_total(kg_total: float) -> float:
    """Valide un poids total en kg."""
    try:
        kg_total = float(kg_total)
    except (ValueError, TypeError):
        raise ValidationError("Le poids total doit être un nombre")
    
    if kg_total < MIN_KG_TOTAL:
        raise ValidationError(f"Le poids total doit être supérieur ou égal à {MIN_KG_TOTAL} kg")
    
    if kg_total > MAX_KG_TOTAL:
        raise ValidationError(f"Le poids total ne peut pas dépasser {MAX_KG_TOTAL} kg")
    
    return kg_total


def validate_nb_rangees(nb_rangees: Optional[int]) -> int:
    """Valide un nombre de rangées."""
    if nb_rangees is None:
        return 10  # Valeur par défaut
    
    try:
        nb_rangees = int(nb_rangees)
    except (ValueError, TypeError):
        raise ValidationError("Le nombre de rangées doit être un entier")
    
    if nb_rangees < 1:
        raise ValidationError("Le nombre de rangées doit être supérieur à 0")
    
    if nb_rangees > 1000:  # Limite raisonnable
        raise ValidationError("Le nombre de rangées ne peut pas dépasser 1000")
    
    return nb_rangees


def validate_commentaires(commentaires: Optional[str]) -> Optional[str]:
    """Valide des commentaires."""
    if commentaires is None:
        return None
    
    if not isinstance(commentaires, str):
        raise ValidationError("Les commentaires doivent être une chaîne de caractères")
    
    commentaires = commentaires.strip()
    
    if len(commentaires) > MAX_COMMENT_LENGTH:
        raise ValidationError(f"Les commentaires ne peuvent pas dépasser {MAX_COMMENT_LENGTH} caractères")
    
    return commentaires if commentaires else None


def validate_annee(annee: int) -> int:
    """Valide une année."""
    try:
        annee = int(annee)
    except (ValueError, TypeError):
        raise ValidationError("L'année doit être un entier")
    
    current_year = datetime.now().year
    if annee < 2000 or annee > current_year + 10:
        raise ValidationError(f"L'année doit être entre 2000 et {current_year + 10}")
    
    return annee


def validate_nb_plants(nb_plants: int) -> int:
    """Valide un nombre de plants."""
    try:
        nb_plants = int(nb_plants)
    except (ValueError, TypeError):
        raise ValidationError("Le nombre de plants doit être un entier")
    
    if nb_plants < 1:
        raise ValidationError("Le nombre de plants doit être supérieur à 0")
    
    if nb_plants > 1000000:  # Limite raisonnable
        raise ValidationError("Le nombre de plants ne peut pas dépasser 1 000 000")
    
    return nb_plants


def validate_fraction_fraiseraie(fraction: float) -> float:
    """Valide une fraction de fraiseraie (entre 0 et 1)."""
    try:
        fraction = float(fraction)
    except (ValueError, TypeError):
        raise ValidationError("La fraction de fraiseraie doit être un nombre")
    
    if fraction < 0 or fraction > 1:
        raise ValidationError("La fraction de fraiseraie doit être entre 0 et 1")
    
    return fraction


def validate_id(id_value: int) -> int:
    """Valide un ID (doit être un entier positif)."""
    try:
        id_value = int(id_value)
    except (ValueError, TypeError):
        raise ValidationError("L'ID doit être un entier")
    
    if id_value < 1:
        raise ValidationError("L'ID doit être un entier positif")
    
    return id_value

