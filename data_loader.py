"""
Module utilitaire pour charger les données depuis SQLite ou Excel
Permet une transition progressive d'Excel vers SQLite
"""
import pandas as pd
from pathlib import Path
import os

# Utiliser config.py si disponible, sinon fallback
try:
    from config import EXCEL_PATH, DB_PATH
    _DB_PATH = Path(DB_PATH)
except ImportError:
    # Fallback: chercher dans data/ puis à la racine
    BASE_DIR = Path(__file__).parent.resolve()
    data_path = BASE_DIR / "data" / "recoltes_fraises.xlsx"
    root_path = BASE_DIR / "recoltes_fraises.xlsx"
    EXCEL_PATH = str(data_path if data_path.exists() else root_path)
    _DB_PATH = Path("recoltes.db")
USE_DB = os.environ.get("USE_DB", "true").lower() == "true"

def _try_db():
    """Essaie d'utiliser la base de données."""
    try:
        from database import (
            get_parametres, get_recoltes, get_jour_courant,
            get_plants_par_annee, get_recolte_quotidienne
        )
        return True, {
            'get_parametres': get_parametres,
            'get_recoltes': get_recoltes,
            'get_jour_courant': get_jour_courant,
            'get_plants_par_annee': get_plants_par_annee,
            'get_recolte_quotidienne': get_recolte_quotidienne
        }
    except ImportError:
        return False, None

def load_parametres():
    """Charge les paramètres depuis SQLite ou Excel."""
    if USE_DB:
        db_available, db_funcs = _try_db()
        if db_available and _DB_PATH.exists():
            df = db_funcs['get_parametres']()
            if not df.empty:
                # Normaliser les colonnes pour compatibilité
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
                if 'parcelle' in df.columns:
                    df['parcelle'] = df['parcelle'].astype(str).str.strip().str.lower()
                return df
    
    # Fallback vers Excel
    if Path(EXCEL_PATH).exists():
        df = pd.read_excel(EXCEL_PATH, sheet_name="Paramètres")
        if 'variety' in df.columns:
            df['variety'] = df['variety'].astype(str).str.strip().str.lower()
        if 'parcelle' in df.columns:
            df['parcelle'] = df['parcelle'].astype(str).str.strip().str.lower()
        return df
    return pd.DataFrame()

def load_recoltes():
    """Charge les récoltes depuis SQLite ou Excel."""
    if USE_DB:
        db_available, db_funcs = _try_db()
        if db_available and _DB_PATH.exists():
            df = db_funcs['get_recoltes']()
            if not df.empty:
                # Normaliser
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
                return df
    
    # Fallback vers Excel
    if Path(EXCEL_PATH).exists():
        df = pd.read_excel(EXCEL_PATH, sheet_name="Recoltes", parse_dates=["date"])
        if 'variety' in df.columns:
            df['variety'] = df['variety'].astype(str).str.strip().str.lower()
        return df
    return pd.DataFrame()

def load_jour_courant():
    """Charge les données du jour courant depuis SQLite ou Excel."""
    if USE_DB:
        db_available, db_funcs = _try_db()
        if db_available and _DB_PATH.exists():
            df = db_funcs['get_jour_courant']()
            if not df.empty:
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
                return df
    
    # Fallback vers Excel
    if Path(EXCEL_PATH).exists():
        try:
            df = pd.read_excel(EXCEL_PATH, sheet_name="Jour_courant", parse_dates=["date"])
            if 'variety' in df.columns:
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
            return df
        except:
            return pd.DataFrame(columns=["date", "variety", "kg_premiere_rangee"])
    return pd.DataFrame(columns=["date", "variety", "kg_premiere_rangee"])

def load_plants_par_annee():
    """Charge les plants par année depuis SQLite ou Excel."""
    if USE_DB:
        db_available, db_funcs = _try_db()
        if db_available and _DB_PATH.exists():
            df = db_funcs['get_plants_par_annee']()
            if not df.empty:
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
                # Renommer pour compatibilité avec l'ancien code (qui attend "Année" et "Nb_plants")
                if 'annee' in df.columns:
                    df['Année'] = df['annee']
                if 'nb_plants' in df.columns:
                    df['Nb_plants'] = df['nb_plants']
                return df
    
    # Fallback vers Excel
    if Path(EXCEL_PATH).exists():
        try:
            df = pd.read_excel(EXCEL_PATH, sheet_name="Plants_par_annee")
            if 'variety' in df.columns:
                df['variety'] = df['variety'].astype(str).str.strip().str.lower()
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def load_recolte_quotidienne():
    """Charge la configuration de récolte quotidienne depuis SQLite ou Excel."""
    if USE_DB:
        db_available, db_funcs = _try_db()
        if db_available and _DB_PATH.exists():
            df = db_funcs['get_recolte_quotidienne']()
            if not df.empty:
                return df
    
    # Fallback vers Excel
    if Path(EXCEL_PATH).exists():
        try:
            df = pd.read_excel(EXCEL_PATH, sheet_name="Recolte_quotidienne")
            return df
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def load_recoltes_with_params():
    """Charge les récoltes fusionnées avec les paramètres (compatible avec l'ancien code)."""
    df_recoltes = load_recoltes()
    params = load_parametres()
    
    if df_recoltes.empty:
        return pd.DataFrame()
    if params.empty:
        return df_recoltes
    
    # Fusion sur variety uniquement
    df_merged = df_recoltes.merge(params, on=["variety"], how="left")
    
    # Gestion des colonnes nb_rangees après fusion
    if "nb_rangees_x" in df_merged.columns and "nb_rangees_y" in df_merged.columns:
        df_merged["nb_rangees"] = df_merged["nb_rangees_x"].fillna(df_merged["nb_rangees_y"])
        df_merged.drop(columns=["nb_rangees_x", "nb_rangees_y"], inplace=True)
    elif "nb_rangees_x" in df_merged.columns:
        df_merged.rename(columns={"nb_rangees_x": "nb_rangees"}, inplace=True)
    elif "nb_rangees_y" in df_merged.columns:
        df_merged.rename(columns={"nb_rangees_y": "nb_rangees"}, inplace=True)
    
    # Valeur par défaut si nb_rangees est vide
    if "nb_rangees" in df_merged.columns:
        df_merged["nb_rangees"] = df_merged["nb_rangees"].fillna(10)
    
    return df_merged

