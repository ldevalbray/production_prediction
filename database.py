"""
Module de gestion de la base de données SQLite pour les récoltes
Remplace progressivement l'utilisation d'Excel
"""
import sqlite3
import pandas as pd
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import logging
from contextlib import contextmanager

# Import de la configuration centralisée
try:
    from config import DB_PATH
except ImportError:
    DB_PATH = "recoltes.db"

# Configuration du logging
logger = logging.getLogger(__name__)

@contextmanager
def get_db_connection():
    """
    Context manager pour les connexions à la base de données.
    Gère automatiquement le commit, rollback et la fermeture.
    """
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row  # Permet d'accéder aux colonnes par nom
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        logger.error(f"Erreur lors de l'accès à la base de données : {e}", exc_info=True)
        raise
    finally:
        if conn:
            conn.close()

def get_connection():
    """
    Crée une connexion à la base de données.
    ⚠️ DEPRECATED: Utilisez get_db_connection() avec un context manager à la place.
    """
    logger.warning("get_connection() est déprécié. Utilisez get_db_connection() avec un context manager.")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialise le schéma de la base de données."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Table: parametres (parcelle, variety, nb_rangees)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS parametres (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    parcelle TEXT NOT NULL,
                    variety TEXT NOT NULL,
                    nb_rangees INTEGER DEFAULT 10,
                    saison_debut INTEGER,
                    saison_fin INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(parcelle, variety)
                )
            """)
            
            # Table: recoltes (historique des récoltes)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recoltes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    variety TEXT NOT NULL,
                    kg_total REAL NOT NULL,
                    commentaires TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Table: jour_courant (données du jour en cours)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jour_courant (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE NOT NULL,
                    variety TEXT NOT NULL,
                    kg_premiere_rangee REAL,
                    commentaires TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(date, variety)
                )
            """)
            
            # Table: plants_par_annee
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS plants_par_annee (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    variety TEXT NOT NULL,
                    annee INTEGER NOT NULL,
                    nb_plants INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(variety, annee)
                )
            """)
            
            # Table: recolte_quotidienne (organisation hebdomadaire)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS recolte_quotidienne (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    jour_semaine TEXT NOT NULL,
                    jour_semaine_num INTEGER NOT NULL,
                    fraction_fraiseraie REAL NOT NULL,
                    description TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(jour_semaine_num)
                )
            """)
            
            # Table: forecasts (prévisions de récolte)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS forecasts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    forecast_date DATE NOT NULL,
                    date DATE NOT NULL,
                    parcelle TEXT NOT NULL,
                    variety TEXT NOT NULL,
                    predicted_kg_total REAL,
                    predicted_kg_par_rangee REAL,
                    confidence_min_kg_total REAL,
                    confidence_max_kg_total REAL,
                    temperature_max REAL,
                    temperature_min REAL,
                    precipitation_sum REAL,
                    sunshine_duration REAL,
                    relative_humidity_mean REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(forecast_date, date, parcelle, variety)
                )
            """)
            
            # Index pour améliorer les performances
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recoltes_date ON recoltes(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_recoltes_variety ON recoltes(variety)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_parametres_variety ON parametres(variety)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jour_courant_date ON jour_courant(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_forecast_date ON forecasts(forecast_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_date ON forecasts(date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_forecasts_parcelle_variety ON forecasts(parcelle, variety)")
        
        logger.info(f"Base de données initialisée : {DB_PATH}")
        print(f"✅ Base de données initialisée : {DB_PATH}")
    except Exception as e:
        logger.error(f"Erreur lors de l'initialisation de la base de données : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR PARAMETRES =====

def get_parametres() -> pd.DataFrame:
    """Récupère tous les paramètres."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM parametres ORDER BY parcelle, variety", conn)
    return df

def add_parametre(parcelle: str, variety: str, nb_rangees: int = 10, 
                  saison_debut: Optional[int] = None, saison_fin: Optional[int] = None) -> int:
    """Ajoute un paramètre. Retourne l'ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO parametres (parcelle, variety, nb_rangees, saison_debut, saison_fin)
                VALUES (?, ?, ?, ?, ?)
            """, (parcelle.strip().lower(), variety.strip().lower(), nb_rangees, saison_debut, saison_fin))
            return cursor.lastrowid
    except sqlite3.IntegrityError as e:
        logger.error(f"Erreur d'intégrité lors de l'ajout du paramètre : {e}")
        raise ValueError(f"Un paramètre avec cette parcelle/variété existe déjà") from e
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout du paramètre : {e}", exc_info=True)
        raise

def update_parametre(id: int, parcelle: Optional[str] = None, variety: Optional[str] = None,
                     nb_rangees: Optional[int] = None, saison_debut: Optional[int] = None,
                     saison_fin: Optional[int] = None, 
                     update_saison_debut: bool = False, update_saison_fin: bool = False) -> bool:
    """Met à jour un paramètre.
    
    Args:
        update_saison_debut: Si True, met à jour saison_debut même si None (pour effacer)
        update_saison_fin: Si True, met à jour saison_fin même si None (pour effacer)
    """
    updates = []
    params = []
    
    if parcelle is not None:
        updates.append("parcelle = ?")
        params.append(parcelle.strip().lower())
    if variety is not None:
        updates.append("variety = ?")
        params.append(variety.strip().lower())
    if nb_rangees is not None:
        updates.append("nb_rangees = ?")
        params.append(nb_rangees)
    
    # Pour saison_debut et saison_fin, on peut vouloir les mettre à None
    # On utilise un flag pour indiquer qu'on veut les mettre à jour même si None
    if update_saison_debut:
        updates.append("saison_debut = ?")
        params.append(saison_debut)
    elif saison_debut is not None:
        updates.append("saison_debut = ?")
        params.append(saison_debut)
    
    if update_saison_fin:
        updates.append("saison_fin = ?")
        params.append(saison_fin)
    elif saison_fin is not None:
        updates.append("saison_fin = ?")
        params.append(saison_fin)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(id)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE parametres SET {', '.join(updates)} WHERE id = ?", params)
            success = cursor.rowcount > 0
        return success
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du paramètre {id} : {e}", exc_info=True)
        raise

def delete_parametre(id: int) -> bool:
    """Supprime un paramètre."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM parametres WHERE id = ?", (id,))
            success = cursor.rowcount > 0
        return success
    except Exception as e:
        logger.error(f"Erreur lors de la suppression du paramètre {id} : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR RECOLTES =====

def get_recoltes(start_date: Optional[str] = None, end_date: Optional[str] = None,
                 variety: Optional[str] = None) -> pd.DataFrame:
    """Récupère les récoltes avec filtres optionnels."""
    query = "SELECT * FROM recoltes WHERE 1=1"
    params = []
    
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if variety:
        query += " AND variety = ?"
        params.append(variety.strip().lower())
    
    query += " ORDER BY date DESC, variety"
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params, parse_dates=["date"])
    return df

def add_recolte(date: str, variety: str, kg_total: float, commentaires: Optional[str] = None) -> int:
    """Ajoute une récolte. Retourne l'ID."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recoltes (date, variety, kg_total, commentaires)
                VALUES (?, ?, ?, ?)
            """, (date, variety.strip().lower(), kg_total, commentaires))
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Erreur lors de l'ajout de la récolte : {e}", exc_info=True)
        raise

def update_recolte(id: int, date: Optional[str] = None, variety: Optional[str] = None,
                   kg_total: Optional[float] = None, commentaires: Optional[str] = None) -> bool:
    """Met à jour une récolte."""
    updates = []
    params = []
    
    if date is not None:
        updates.append("date = ?")
        params.append(date)
    if variety is not None:
        updates.append("variety = ?")
        params.append(variety.strip().lower())
    if kg_total is not None:
        updates.append("kg_total = ?")
        params.append(kg_total)
    if commentaires is not None:
        updates.append("commentaires = ?")
        params.append(commentaires)
    
    if not updates:
        return False
    
    updates.append("updated_at = CURRENT_TIMESTAMP")
    params.append(id)
    
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"UPDATE recoltes SET {', '.join(updates)} WHERE id = ?", params)
            success = cursor.rowcount > 0
        return success
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la récolte {id} : {e}", exc_info=True)
        raise

def delete_recolte(id: int) -> bool:
    """Supprime une récolte."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM recoltes WHERE id = ?", (id,))
            success = cursor.rowcount > 0
        return success
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la récolte {id} : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR JOUR_COURANT =====

def get_jour_courant(date: Optional[str] = None) -> pd.DataFrame:
    """Récupère les données du jour courant."""
    with get_db_connection() as conn:
        if date:
            query = "SELECT * FROM jour_courant WHERE date = ? ORDER BY variety"
            df = pd.read_sql_query(query, conn, params=(date,), parse_dates=["date"])
        else:
            query = "SELECT * FROM jour_courant ORDER BY date DESC, variety"
            df = pd.read_sql_query(query, conn, parse_dates=["date"])
    return df

def set_jour_courant(date: str, variety: str, kg_premiere_rangee: Optional[float] = None,
                     commentaires: Optional[str] = None) -> int:
    """Ajoute ou met à jour les données du jour courant."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO jour_courant (date, variety, kg_premiere_rangee, commentaires)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(date, variety) DO UPDATE SET
                    kg_premiere_rangee = excluded.kg_premiere_rangee,
                    commentaires = excluded.commentaires,
                    updated_at = CURRENT_TIMESTAMP
            """, (date, variety.strip().lower(), kg_premiere_rangee, commentaires))
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour du jour courant : {e}", exc_info=True)
        raise

def clear_jour_courant(date: Optional[str] = None):
    """Efface les données du jour courant (pour une date spécifique ou toutes)."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            if date:
                cursor.execute("DELETE FROM jour_courant WHERE date = ?", (date,))
            else:
                cursor.execute("DELETE FROM jour_courant")
    except Exception as e:
        logger.error(f"Erreur lors de l'effacement du jour courant : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR PLANTS_PAR_ANNEE =====

def get_plants_par_annee(annee: Optional[int] = None) -> pd.DataFrame:
    """Récupère les données de plants par année."""
    with get_db_connection() as conn:
        if annee:
            query = "SELECT * FROM plants_par_annee WHERE annee = ? ORDER BY variety"
            df = pd.read_sql_query(query, conn, params=(annee,))
        else:
            query = "SELECT * FROM plants_par_annee ORDER BY annee DESC, variety"
            df = pd.read_sql_query(query, conn)
    return df

def set_plants_par_annee(variety: str, annee: int, nb_plants: int) -> int:
    """Ajoute ou met à jour les plants par année."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO plants_par_annee (variety, annee, nb_plants)
                VALUES (?, ?, ?)
                ON CONFLICT(variety, annee) DO UPDATE SET
                    nb_plants = excluded.nb_plants,
                    updated_at = CURRENT_TIMESTAMP
            """, (variety.strip().lower(), annee, nb_plants))
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour des plants par année : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR RECOLTE_QUOTIDIENNE =====

def get_recolte_quotidienne() -> pd.DataFrame:
    """Récupère la configuration de récolte quotidienne."""
    with get_db_connection() as conn:
        df = pd.read_sql_query("SELECT * FROM recolte_quotidienne ORDER BY jour_semaine_num", conn)
    return df

def set_recolte_quotidienne(jour_semaine: str, jour_semaine_num: int, 
                           fraction_fraiseraie: float, description: Optional[str] = None) -> int:
    """Ajoute ou met à jour la configuration de récolte quotidienne."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO recolte_quotidienne (jour_semaine, jour_semaine_num, fraction_fraiseraie, description)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(jour_semaine_num) DO UPDATE SET
                    jour_semaine = excluded.jour_semaine,
                    fraction_fraiseraie = excluded.fraction_fraiseraie,
                    description = excluded.description,
                    updated_at = CURRENT_TIMESTAMP
            """, (jour_semaine, jour_semaine_num, fraction_fraiseraie, description))
            return cursor.lastrowid
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la récolte quotidienne : {e}", exc_info=True)
        raise

# ===== FONCTIONS UTILITAIRES =====

def get_recoltes_with_params() -> pd.DataFrame:
    """Récupère les récoltes fusionnées avec les paramètres (compatible avec l'ancien code)."""
    query = """
        SELECT r.*, p.parcelle, p.nb_rangees
        FROM recoltes r
        LEFT JOIN parametres p ON r.variety = p.variety
        ORDER BY r.date DESC, r.variety
    """
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, parse_dates=["date"])
    return df

def export_to_excel(output_path: str = "recoltes_export.xlsx"):
    """Exporte toutes les données vers un fichier Excel (pour compatibilité)."""
    try:
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            # Paramètres
            params_df = get_parametres()
            if not params_df.empty:
                cols = ['parcelle', 'variety', 'nb_rangees']
                if 'saison_debut' in params_df.columns:
                    cols.append('saison_debut')
                if 'saison_fin' in params_df.columns:
                    cols.append('saison_fin')
                params_df = params_df[[c for c in cols if c in params_df.columns]].copy()
                # Remplacer NaN par None pour éviter les erreurs
                params_df = params_df.where(pd.notnull(params_df), None)
            params_df.to_excel(writer, sheet_name='Paramètres', index=False)
            
            # Récoltes
            recoltes_df = get_recoltes()
            if not recoltes_df.empty:
                cols = ['date', 'variety', 'kg_total']
                if 'commentaires' in recoltes_df.columns:
                    cols.append('commentaires')
                recoltes_df = recoltes_df[[c for c in cols if c in recoltes_df.columns]].copy()
                # Convertir les dates en string pour éviter les erreurs Excel
                if 'date' in recoltes_df.columns:
                    if pd.api.types.is_datetime64_any_dtype(recoltes_df['date']):
                        recoltes_df['date'] = recoltes_df['date'].dt.strftime('%Y-%m-%d')
                    else:
                        recoltes_df['date'] = recoltes_df['date'].astype(str)
                # Remplacer NaN par None
                recoltes_df = recoltes_df.where(pd.notnull(recoltes_df), None)
            recoltes_df.to_excel(writer, sheet_name='Recoltes', index=False)
            
            # Jour courant
            jour_df = get_jour_courant()
            if not jour_df.empty:
                cols = ['date', 'variety']
                if 'kg_premiere_rangee' in jour_df.columns:
                    cols.append('kg_premiere_rangee')
                if 'commentaires' in jour_df.columns:
                    cols.append('commentaires')
                jour_df = jour_df[[c for c in cols if c in jour_df.columns]].copy()
                # Convertir les dates en string
                if 'date' in jour_df.columns:
                    if pd.api.types.is_datetime64_any_dtype(jour_df['date']):
                        jour_df['date'] = jour_df['date'].dt.strftime('%Y-%m-%d')
                    else:
                        jour_df['date'] = jour_df['date'].astype(str)
                # Remplacer NaN par None
                jour_df = jour_df.where(pd.notnull(jour_df), None)
            jour_df.to_excel(writer, sheet_name='Jour_courant', index=False)
            
            # Plants par année - adapter les noms de colonnes
            plants_df = get_plants_par_annee()
            if not plants_df.empty:
                plants_df = plants_df[['variety', 'annee', 'nb_plants']].copy()
                plants_df.rename(columns={'annee': 'Année', 'nb_plants': 'Nb_plants'}, inplace=True)
                # Remplacer NaN par None
                plants_df = plants_df.where(pd.notnull(plants_df), None)
            plants_df.to_excel(writer, sheet_name='Plants_par_annee', index=False)
            
            # Récolte quotidienne
            recolte_quot_df = get_recolte_quotidienne()
            if not recolte_quot_df.empty:
                cols = ['jour_semaine', 'jour_semaine_num', 'fraction_fraiseraie']
                if 'description' in recolte_quot_df.columns:
                    cols.append('description')
                recolte_quot_df = recolte_quot_df[[c for c in cols if c in recolte_quot_df.columns]].copy()
                # Remplacer NaN par None
                recolte_quot_df = recolte_quot_df.where(pd.notnull(recolte_quot_df), None)
            recolte_quot_df.to_excel(writer, sheet_name='Recolte_quotidienne', index=False)
        
        print(f"✅ Export Excel créé : {output_path}")
    except Exception as e:
        logger.error(f"Erreur lors de l'export Excel : {e}", exc_info=True)
        raise

# ===== FONCTIONS CRUD POUR FORECASTS =====

def save_forecast(forecast_date: str, forecasts_df: pd.DataFrame) -> int:
    """
    Sauvegarde une prévision dans la base de données.
    
    Args:
        forecast_date: Date de génération de la prévision (format YYYY-MM-DD)
        forecasts_df: DataFrame avec les colonnes: date, parcelle, variety, predicted_kg_total,
                     predicted_kg_par_rangee, confidence_min_kg_total, confidence_max_kg_total,
                     temperature_max, temperature_min, precipitation_sum, sunshine_duration,
                     relative_humidity_mean
    
    Returns:
        Nombre de lignes insérées
    """
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Supprimer les anciennes prévisions de la même date
            cursor.execute("DELETE FROM forecasts WHERE forecast_date = ?", (forecast_date,))
            
            # Insérer les nouvelles prévisions
            count = 0
            for _, row in forecasts_df.iterrows():
                cursor.execute("""
                    INSERT OR REPLACE INTO forecasts (
                        forecast_date, date, parcelle, variety,
                        predicted_kg_total, predicted_kg_par_rangee,
                        confidence_min_kg_total, confidence_max_kg_total,
                        temperature_max, temperature_min,
                        precipitation_sum, sunshine_duration, relative_humidity_mean
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    forecast_date,
                    row.get('date'),
                    row.get('parcelle'),
                    row.get('variety'),
                    row.get('predicted_kg_total'),
                    row.get('predicted_kg_par_rangee'),
                    row.get('confidence_min_kg_total'),
                    row.get('confidence_max_kg_total'),
                    row.get('temperature_max'),
                    row.get('temperature_min'),
                    row.get('precipitation_sum'),
                    row.get('sunshine_duration'),
                    row.get('relative_humidity_mean')
                ))
                count += 1
            
            logger.info(f"✅ {count} prévisions sauvegardées pour la date {forecast_date}")
            return count
    except Exception as e:
        logger.error(f"Erreur lors de la sauvegarde des prévisions : {e}", exc_info=True)
        raise

def get_forecasts(forecast_date: Optional[str] = None, 
                 start_date: Optional[str] = None,
                 end_date: Optional[str] = None,
                 parcelle: Optional[str] = None,
                 variety: Optional[str] = None) -> pd.DataFrame:
    """
    Récupère les prévisions depuis la base de données.
    
    Args:
        forecast_date: Date de génération de la prévision (pour obtenir une prévision spécifique)
        start_date: Date de début pour filtrer les dates prévues
        end_date: Date de fin pour filtrer les dates prévues
        parcelle: Filtrer par parcelle
        variety: Filtrer par variété
    
    Returns:
        DataFrame avec les prévisions
    """
    query = "SELECT * FROM forecasts WHERE 1=1"
    params = []
    
    if forecast_date:
        query += " AND forecast_date = ?"
        params.append(forecast_date)
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if parcelle:
        query += " AND parcelle = ?"
        params.append(parcelle.lower())
    if variety:
        query += " AND variety = ?"
        params.append(variety.lower())
    
    query += " ORDER BY forecast_date DESC, date ASC, parcelle, variety"
    
    with get_db_connection() as conn:
        df = pd.read_sql_query(query, conn, params=params)
        if not df.empty and 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'])
        if not df.empty and 'forecast_date' in df.columns:
            df['forecast_date'] = pd.to_datetime(df['forecast_date'])
    
    return df

def get_latest_forecast_date() -> Optional[str]:
    """Retourne la date de la dernière prévision générée."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT MAX(forecast_date) as max_date FROM forecasts")
        result = cursor.fetchone()
        if result and result['max_date']:
            return result['max_date']
    return None

def get_latest_forecast() -> pd.DataFrame:
    """Récupère la dernière prévision générée."""
    latest_date = get_latest_forecast_date()
    if latest_date:
        return get_forecasts(forecast_date=latest_date)
    return pd.DataFrame()

def delete_forecast(forecast_date: str) -> bool:
    """Supprime une prévision par sa date de génération."""
    try:
        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM forecasts WHERE forecast_date = ?", (forecast_date,))
            return cursor.rowcount > 0
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la prévision : {e}", exc_info=True)
        return False

def export_forecast_to_excel(forecast_date: Optional[str] = None, output_path: Optional[str] = None) -> str:
    """
    Exporte une prévision vers un fichier Excel.
    
    Args:
        forecast_date: Date de génération de la prévision (si None, utilise la dernière)
        output_path: Chemin de sortie (si None, génère automatiquement)
    
    Returns:
        Chemin du fichier créé
    """
    if forecast_date is None:
        forecast_date = get_latest_forecast_date()
        if not forecast_date:
            raise ValueError("Aucune prévision trouvée dans la base de données")
    
    forecasts_df = get_forecasts(forecast_date=forecast_date)
    if forecasts_df.empty:
        raise ValueError(f"Aucune prévision trouvée pour la date {forecast_date}")
    
    if output_path is None:
        # Utiliser get_base_path() si disponible (pour PyInstaller)
        try:
            from pyinstaller_utils import get_base_path
            base_path = get_base_path()
        except ImportError:
            base_path = Path(__file__).parent
        
        date_str = forecast_date
        output_path = str(base_path / "forecasts" / f"forecast_next3days_{date_str}.xlsx")
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        forecasts_df.to_excel(writer, sheet_name='Prévisions', index=False)
    
    logger.info(f"✅ Prévision exportée vers : {output_path}")
    return output_path

if __name__ == "__main__":
    # Initialisation de la base de données
    init_database()
    print("✅ Module database.py prêt à l'emploi")

