#!/usr/bin/env python3
"""
Script pour remplir les valeurs manquantes de shortwave_radiation
dans le fichier meteo_dataset.csv pour les dates historiques existantes.
"""
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
import time

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# === PARAMÈTRES ===
try:
    from config import WEATHER_PATH as WEATHER_PATH_CONFIG, LAT, LON, TIMEZONE
    WEATHER_PATH = WEATHER_PATH_CONFIG
except ImportError:
    BASE_DIR = Path(__file__).parent.parent.resolve()
    data_path = BASE_DIR / "data" / "meteo_dataset.csv"
    root_path = BASE_DIR / "meteo_dataset.csv"
    WEATHER_PATH = str(data_path if data_path.exists() else root_path)
    LAT, LON = 43.12, 6.14  # Hyères
    TIMEZONE = "Europe/Paris"

def get_day_of_year(date):
    """Calcule le jour de l'année (1-365/366)"""
    return date.timetuple().tm_yday

def estimate_shortwave_radiation(row):
    """
    Estime shortwave_radiation (W/m²) basé sur sun_hours et autres variables météo.
    
    Formule basée sur :
    - sun_hours : durée d'ensoleillement (heures)
    - day_of_year : pour la position dans l'année (saison)
    
    Estimation : shortwave_radiation ≈ sun_hours * facteur_saisonnier * constante
    
    Args:
        row: ligne du DataFrame avec les colonnes nécessaires
    
    Returns:
        Estimation de shortwave_radiation en W/m²
    """
    sun_hours = row.get("sun_hours", 0)
    
    # Si sun_hours est manquant, retourner NaN
    if pd.isna(sun_hours):
        return np.nan
    
    # Si sun_hours = 0 (pas de soleil), shortwave_radiation = 0
    if sun_hours <= 0:
        return 0.0
    
    # Facteur saisonnier basé sur le jour de l'année
    day_of_year = row.get("day_of_year")
    if pd.isna(day_of_year):
        # Calculer depuis la date si disponible
        if "date" in row and not pd.isna(row["date"]):
            day_of_year = get_day_of_year(pd.Timestamp(row["date"]))
        else:
            day_of_year = 182  # Milieu de l'année par défaut
    
    # Facteur saisonnier : plus élevé en été (jour 172 = 21 juin), plus bas en hiver
    # Utilise une courbe sinusoïdale pour modéliser la variation saisonnière
    seasonal_factor = 0.7 + 0.3 * np.cos(2 * np.pi * (day_of_year - 172) / 365.25)
    
    # Facteur de latitude pour Hyères (43.12°N)
    # Le rayonnement solaire maximal théorique varie avec la latitude
    latitude_factor = 0.85  # Facteur pour ~43°N
    
    # Estimation : W/m² = sun_hours * facteur_conversion * facteurs
    # En moyenne, 1 heure d'ensoleillement ≈ 2.5-3.5 MJ/m² selon la saison
    # Conversion : 1 MJ/m² = 277.78 Wh/m² = 277.78 W/m² pour 1 heure
    # Mais on utilise une moyenne plus réaliste de ~250-300 W/m² par heure d'ensoleillement
    
    base_conversion = 280  # W/m² par heure d'ensoleillement (moyenne)
    
    # Ajustement selon la saison et la latitude
    estimated = sun_hours * base_conversion * seasonal_factor * latitude_factor
    
    # Limites raisonnables : entre 0 et ~1000 W/m² (maximum théorique ~1366 W/m² au niveau de la mer)
    estimated = max(0, min(estimated, 1000))
    
    return estimated

def fetch_shortwave_radiation_for_dates(start_date, end_date):
    """
    Récupère les données de shortwave_radiation pour une plage de dates
    via l'API Open-Meteo (archive ou forecast selon la date)
    
    Args:
        start_date: date de début (datetime)
        end_date: date de fin (datetime)
    
    Returns:
        DataFrame avec date et shortwave_radiation, ou DataFrame vide en cas d'erreur
    """
    # Open-Meteo permet d'utiliser forecast avec des dates passées
    # L'endpoint archive ne supporte pas shortwave_radiation_sum pour les données historiques
    # On essaie d'abord forecast, puis archive en fallback
    
    today = datetime.now().date()
    start_date_only = start_date.date() if isinstance(start_date, datetime) else start_date
    end_date_only = end_date.date() if isinstance(end_date, datetime) else end_date
    
    # Essayer d'abord avec forecast (fonctionne pour les dates passées récentes)
    endpoints_to_try = ["forecast"]
    
    # Si les dates sont très anciennes (> 1 an), essayer aussi archive
    days_ago = (today - end_date_only).days
    if days_ago > 365:
        endpoints_to_try.append("archive")
    
    for endpoint in endpoints_to_try:
        url = (
            f"https://api.open-meteo.com/v1/{endpoint}?"
            f"latitude={LAT}&longitude={LON}"
            f"&start_date={start_date_only.strftime('%Y-%m-%d')}"
            f"&end_date={end_date_only.strftime('%Y-%m-%d')}"
            "&daily=shortwave_radiation_sum"
            f"&timezone={TIMEZONE}"
        )
        
        try:
            print(f"   📡 Récupération via {endpoint} API...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "daily" not in data or not data["daily"]["time"]:
                if len(endpoints_to_try) > 1 and endpoint == endpoints_to_try[0]:
                    continue  # Essayer le prochain endpoint
                print(f"   ⚠️ Aucune donnée retournée par l'API {endpoint}")
                return pd.DataFrame()
            
            # Vérifier si shortwave_radiation_sum est présent
            if "shortwave_radiation_sum" not in data["daily"]:
                if len(endpoints_to_try) > 1 and endpoint == endpoints_to_try[0]:
                    continue  # Essayer le prochain endpoint
                print(f"   ⚠️ shortwave_radiation_sum non disponible via {endpoint}")
                return pd.DataFrame()
            
            # Créer un DataFrame avec les données
            df = pd.DataFrame({
                "date": pd.to_datetime(data["daily"]["time"]),
                "shortwave_radiation": data["daily"]["shortwave_radiation_sum"]
            })
            
            print(f"   ✅ {len(df)} jours récupérés via {endpoint}")
            return df
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404 or e.response.status_code == 400:
                if len(endpoints_to_try) > 1 and endpoint == endpoints_to_try[0]:
                    continue  # Essayer le prochain endpoint
                # Si c'est le dernier endpoint ou une autre erreur, retourner vide
                print(f"   ⚠️ Données non disponibles via {endpoint} pour cette période")
                return pd.DataFrame()
            else:
                print(f"   ❌ Erreur API {endpoint}: {e}")
                return pd.DataFrame()
        except requests.exceptions.RequestException as e:
            if len(endpoints_to_try) > 1 and endpoint == endpoints_to_try[0]:
                continue  # Essayer le prochain endpoint
            print(f"   ❌ Erreur API {endpoint}: {e}")
            return pd.DataFrame()
        except Exception as e:
            print(f"   ❌ Erreur inattendue: {e}")
            return pd.DataFrame()
    
    # Si aucun endpoint n'a fonctionné
    print(f"   ⚠️ Aucune donnée disponible pour cette période")
    return pd.DataFrame()

def fill_missing_shortwave_radiation(min_date=None):
    """
    Remplit les valeurs manquantes de shortwave_radiation dans meteo_dataset.csv
    
    Args:
        min_date: Date minimale à traiter (format 'YYYY-MM-DD' ou datetime).
                  Si None, traite toutes les dates manquantes.
    """
    print("🔧 Remplissage des valeurs manquantes de shortwave_radiation...\n")
    if min_date:
        if isinstance(min_date, str):
            min_date = pd.to_datetime(min_date)
        print(f"📅 Filtrage depuis {min_date.date()}...\n")
    
    # Vérifier que le fichier existe
    if not Path(WEATHER_PATH).exists():
        print(f"❌ Le fichier {WEATHER_PATH} n'existe pas.")
        return False
    
    # Lire le fichier
    try:
        df = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
        if df.empty:
            print("⚠️ Le fichier météo est vide.")
            return False
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier : {e}")
        return False
    
    # Vérifier si la colonne shortwave_radiation existe
    if "shortwave_radiation" not in df.columns:
        print("⚠️ La colonne 'shortwave_radiation' n'existe pas. Ajout de la colonne...")
        df["shortwave_radiation"] = np.nan
    
    # Identifier les lignes avec shortwave_radiation manquant
    missing_mask = df["shortwave_radiation"].isna()
    
    # Filtrer par date minimale si spécifiée
    if min_date:
        missing_mask = missing_mask & (df["date"] >= min_date)
        print(f"📅 Filtrage appliqué : traitement depuis {min_date.date()}")
    
    missing_count = missing_mask.sum()
    
    if missing_count == 0:
        if min_date:
            print(f"✅ Toutes les valeurs de shortwave_radiation sont déjà présentes depuis {min_date.date()}.")
        else:
            print("✅ Toutes les valeurs de shortwave_radiation sont déjà présentes.")
        return True
    
    df_missing_dates = df[missing_mask]["date"]
    print(f"📊 {missing_count} valeurs manquantes trouvées sur {len(df)} lignes totales.")
    print(f"   Plage de dates à traiter : {df_missing_dates.min().date()} à {df_missing_dates.max().date()}")
    if min_date:
        print(f"   (Filtrage depuis {min_date.date()})")
    print()
    
    # Grouper les dates manquantes par périodes continues pour optimiser les appels API
    df_missing = df[missing_mask].copy()
    df_missing = df_missing.sort_values("date")
    
    # Identifier les périodes continues
    # Pour optimiser, on groupe par mois si beaucoup de données
    periods = []
    current_start = None
    current_end = None
    
    # Si beaucoup de données manquantes, grouper par mois pour optimiser
    if len(df_missing) > 1000:
        print("   📦 Beaucoup de données à traiter, regroupement par mois pour optimiser...")
        # Grouper par année-mois
        df_missing["year_month"] = df_missing["date"].dt.to_period("M")
        for year_month, group in df_missing.groupby("year_month"):
            start = group["date"].min()
            end = group["date"].max()
            periods.append((start, end))
    else:
        # Pour moins de données, identifier les périodes continues
        for date in df_missing["date"]:
            if current_start is None:
                current_start = date
                current_end = date
            elif (date - current_end).days <= 1:
                # Continuer la période
                current_end = date
            else:
                # Nouvelle période
                periods.append((current_start, current_end))
                current_start = date
                current_end = date
        
        # Ajouter la dernière période
        if current_start is not None:
            periods.append((current_start, current_end))
    
    print(f"📅 {len(periods)} période(s) à traiter\n")
    
    # Récupérer les données pour chaque période
    updates = []
    total_fetched = 0
    
    for i, (start_date, end_date) in enumerate(periods, 1):
        print(f"Période {i}/{len(periods)}: {start_date.date()} à {end_date.date()}")
        
        df_fetched = fetch_shortwave_radiation_for_dates(start_date, end_date)
        
        if not df_fetched.empty:
            # Fusionner avec les dates manquantes de cette période
            period_dates = df_missing[
                (df_missing["date"] >= start_date) & (df_missing["date"] <= end_date)
            ]["date"].values
            
            for date in period_dates:
                matching = df_fetched[df_fetched["date"].dt.date == pd.Timestamp(date).date()]
                if not matching.empty and not pd.isna(matching.iloc[0]["shortwave_radiation"]):
                    updates.append({
                        "date": date,
                        "shortwave_radiation": matching.iloc[0]["shortwave_radiation"]
                    })
                    total_fetched += 1
            
            # Petite pause pour éviter de surcharger l'API
            if i < len(periods):
                time.sleep(0.5)
        
        print()
    
    # Mettre à jour le DataFrame avec les données réelles récupérées
    if updates:
        print(f"💾 Mise à jour de {total_fetched} valeurs réelles depuis l'API...")
        updates_df = pd.DataFrame(updates)
        updates_df["date"] = pd.to_datetime(updates_df["date"])
        
        # Créer un index de date pour faciliter la mise à jour
        df["date_index"] = pd.to_datetime(df["date"]).dt.date
        updates_df["date_index"] = pd.to_datetime(updates_df["date"]).dt.date
        
        # Mettre à jour les valeurs réelles
        for _, row in updates_df.iterrows():
            mask = df["date_index"] == row["date_index"]
            df.loc[mask, "shortwave_radiation"] = row["shortwave_radiation"]
        
        df = df.drop(columns=["date_index"])
    
    # Pour les valeurs encore manquantes, utiliser l'estimation
    still_missing = df["shortwave_radiation"].isna()
    estimated_count = 0
    if still_missing.sum() > 0:
        print(f"\n📊 Estimation des {still_missing.sum()} valeurs manquantes restantes...")
        print("   (Basée sur sun_hours et facteurs saisonniers)")
        
        # S'assurer que day_of_year existe
        if "day_of_year" not in df.columns:
            df["day_of_year"] = df["date"].apply(get_day_of_year)
        
        # Estimer les valeurs manquantes
        for idx in df[still_missing].index:
            row = df.loc[idx]
            estimated = estimate_shortwave_radiation(row)
            if not pd.isna(estimated):
                df.loc[idx, "shortwave_radiation"] = estimated
                estimated_count += 1
        
        print(f"   ✅ {estimated_count} valeurs estimées")
        if estimated_count < still_missing.sum():
            print(f"   ⚠️ {still_missing.sum() - estimated_count} valeurs n'ont pas pu être estimées (sun_hours manquant)")
    
    # Sauvegarder
    try:
        df.to_csv(WEATHER_PATH, index=False)
        final_missing = df["shortwave_radiation"].isna().sum()
        print(f"\n✅ Fichier mis à jour :")
        print(f"   - {total_fetched} valeurs réelles depuis l'API")
        print(f"   - {estimated_count} valeurs estimées")
        print(f"   - {final_missing} valeurs encore manquantes (sun_hours manquant)")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Remplit les valeurs manquantes de shortwave_radiation dans meteo_dataset.csv"
    )
    parser.add_argument(
        "--since",
        type=str,
        help="Date minimale à traiter (format YYYY-MM-DD, ex: 2000-01-01)",
        default=None
    )
    
    args = parser.parse_args()
    
    min_date = None
    if args.since:
        try:
            min_date = pd.to_datetime(args.since)
            print(f"📅 Mode filtré : traitement depuis {min_date.date()}\n")
        except:
            print(f"❌ Format de date invalide : {args.since}")
            print("   Utilisez le format YYYY-MM-DD (ex: 2000-01-01)")
            sys.exit(1)
    
    success = fill_missing_shortwave_radiation(min_date=min_date)
    sys.exit(0 if success else 1)

