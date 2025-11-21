import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys
import os

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# === PARAMÈTRES ===
# Utiliser config.py si disponible, sinon fallback
try:
    from config import WEATHER_PATH as WEATHER_PATH_CONFIG, LAT, LON, TIMEZONE
    WEATHER_PATH = WEATHER_PATH_CONFIG
except ImportError:
    # Fallback: chercher dans data/ puis à la racine
    BASE_DIR = Path(__file__).parent.parent.resolve()
    data_path = BASE_DIR / "data" / "meteo_dataset.csv"
    root_path = BASE_DIR / "meteo_dataset.csv"
    WEATHER_PATH = str(data_path if data_path.exists() else root_path)
    LAT, LON = 43.12, 6.14  # Hyères
    TIMEZONE = "Europe/Paris"

def get_day_of_year(date):
    """Calcule le jour de l'année (1-365/366)"""
    return date.timetuple().tm_yday

def fetch_weather_data(start_date, end_date):
    """
    Récupère les données météo historiques via l'API Open-Meteo
    
    Args:
        start_date: date de début (datetime)
        end_date: date de fin (datetime)
    
    Returns:
        DataFrame avec les colonnes formatées
    """
    print(f"📡 Récupération des données météo du {start_date.date()} au {end_date.date()}...")
    
    # Utiliser l'endpoint forecast avec des dates passées pour les données historiques
    # Open-Meteo permet d'utiliser forecast avec des dates passées jusqu'à quelques jours
    # Pour des données plus anciennes, on pourrait utiliser l'endpoint archive, mais forecast
    # fonctionne bien pour les données récentes (derniers jours/semaines)
    url = (
        f"https://api.open-meteo.com/v1/forecast?"
        f"latitude={LAT}&longitude={LON}"
        f"&start_date={start_date.strftime('%Y-%m-%d')}"
        f"&end_date={end_date.strftime('%Y-%m-%d')}"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_sum,"
        "sunshine_duration,relative_humidity_2m_mean,wind_speed_10m_mean,wind_gusts_10m_max,"
        "shortwave_radiation_sum"
        f"&timezone={TIMEZONE}"
    )
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if "daily" not in data or not data["daily"]["time"]:
            print("⚠️ Aucune donnée retournée par l'API")
            return pd.DataFrame()
        
        # Création du DataFrame
        # Gérer shortwave_radiation_sum qui peut ne pas être disponible dans toutes les régions
        shortwave_data = data["daily"].get("shortwave_radiation_sum")
        if shortwave_data is None:
            shortwave_data = [np.nan] * len(data["daily"]["time"])
        
        df_new = pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp_max": data["daily"]["temperature_2m_max"],
            "temp_min": data["daily"]["temperature_2m_min"],
            "rain_mm": data["daily"]["precipitation_sum"],
            "sun_hours": np.array(data["daily"]["sunshine_duration"]) / 3600.0,  # Conversion secondes -> heures
            "humidity": data["daily"]["relative_humidity_2m_mean"],
            "wind_avg": data["daily"]["wind_speed_10m_mean"],
            "wind_gust": data["daily"]["wind_gusts_10m_max"],
            "shortwave_radiation": shortwave_data  # W/m² (rayonnement solaire global)
        })
        
        # Calcul de temp_mean
        df_new["temp_mean"] = (df_new["temp_max"] + df_new["temp_min"]) / 2
        
        # Calcul de day_of_year
        df_new["day_of_year"] = df_new["date"].apply(get_day_of_year)
        
        # Réorganiser les colonnes dans l'ordre attendu
        df_new = df_new[[
            "date", "rain_mm", "temp_min", "temp_max", "temp_mean",
            "humidity", "wind_avg", "wind_gust", "sun_hours", "shortwave_radiation", "day_of_year"
        ]]
        
        print(f"✅ {len(df_new)} jours de données récupérés")
        return df_new
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erreur lors de la récupération des données météo : {e}")
        return pd.DataFrame()
    except Exception as e:
        print(f"❌ Erreur inattendue : {e}")
        return pd.DataFrame()

def update_meteo_dataset():
    """
    Met à jour le fichier meteo_dataset.csv avec les données manquantes
    """
    print("🌤️ Mise à jour du fichier météo...")
    
    # Vérifier que le fichier existe
    if not Path(WEATHER_PATH).exists():
        print(f"⚠️ Le fichier {WEATHER_PATH} n'existe pas. Création d'un nouveau fichier...")
        # Créer un fichier vide avec les bonnes colonnes
        df_existing = pd.DataFrame(columns=[
            "date", "rain_mm", "temp_min", "temp_max", "temp_mean",
            "humidity", "wind_avg", "wind_gust", "sun_hours", "shortwave_radiation", "day_of_year"
        ])
        last_date = None
    else:
        # Lire le fichier existant
        try:
            df_existing = pd.read_csv(WEATHER_PATH, parse_dates=["date"])
            if df_existing.empty:
                print("⚠️ Le fichier météo est vide")
                last_date = None
            else:
                # Trouver la dernière date
                last_date = df_existing["date"].max()
                print(f"📅 Dernière date dans le fichier : {last_date.date()}")
        except Exception as e:
            print(f"❌ Erreur lors de la lecture du fichier : {e}")
            return False
    
    # Déterminer la période à récupérer
    if last_date is None:
        # Si pas de données, récupérer les 30 derniers jours
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now() - timedelta(days=1)  # Jusqu'à hier
        print(f"📅 Aucune date trouvée. Récupération des 30 derniers jours...")
    else:
        # Récupérer depuis la dernière date + 1 jour jusqu'à hier
        start_date = pd.Timestamp(last_date).to_pydatetime() + timedelta(days=1)
        end_date = datetime.now() - timedelta(days=1)  # Jusqu'à hier
        
        # Vérifier s'il y a des données à récupérer
        if start_date.date() > end_date.date():
            print(f"✅ Le fichier est déjà à jour (dernière date : {last_date.date()})")
            return True
    
    # Récupérer les nouvelles données
    df_new = fetch_weather_data(start_date, end_date)
    
    if df_new.empty:
        print("⚠️ Aucune nouvelle donnée récupérée")
        return False
    
    # Fusionner avec les données existantes
    if df_existing.empty:
        df_new_filtered = df_new
        df_combined = df_new
    else:
        # Vérifier si le fichier existant a la colonne shortwave_radiation
        # Si elle manque, l'ajouter avec des valeurs NaN pour compatibilité
        if "shortwave_radiation" not in df_existing.columns:
            print("⚠️ Colonne 'shortwave_radiation' manquante dans le fichier existant. Ajout avec valeurs NaN pour les données anciennes.")
            df_existing["shortwave_radiation"] = np.nan
        
        # Éviter les doublons en supprimant les dates qui existent déjà
        # MAIS : remplacer les valeurs estimées par les valeurs réelles si disponibles
        df_existing_dates = set(df_existing["date"].dt.date)
        
        # Séparer les nouvelles dates et les dates existantes avec valeurs réelles
        new_dates = df_new[~df_new["date"].dt.date.isin(df_existing_dates)]
        existing_dates_with_real_data = df_new[df_new["date"].dt.date.isin(df_existing_dates)]
        
        # Pour les dates existantes, remplacer si on a des données réelles (non NaN)
        # Cela permet de remplacer les valeurs estimées par les valeurs réelles quand disponibles
        replaced_count = 0
        if not existing_dates_with_real_data.empty:
            for _, new_row in existing_dates_with_real_data.iterrows():
                date_match = df_existing["date"].dt.date == new_row["date"].date()
                if date_match.any():
                    idx = df_existing[date_match].index[0]
                    # Remplacer seulement si la nouvelle valeur n'est pas NaN
                    if not pd.isna(new_row.get("shortwave_radiation")):
                        df_existing.loc[idx, "shortwave_radiation"] = new_row["shortwave_radiation"]
                        replaced_count += 1
        
        if replaced_count > 0:
            print(f"   ✅ {replaced_count} valeur(s) estimée(s) remplacée(s) par des données réelles")
        
        df_new_filtered = new_dates
        
        if df_new_filtered.empty:
            print("✅ Aucune nouvelle donnée à ajouter (toutes les dates existent déjà)")
            # Même si pas de nouvelles données, s'assurer que la colonne existe
            if "shortwave_radiation" not in df_existing.columns:
                df_existing["shortwave_radiation"] = np.nan
                df_existing.to_csv(WEATHER_PATH, index=False)
                print("   ✅ Colonne 'shortwave_radiation' ajoutée au fichier existant")
            return True
        
        # Concaténer et trier par date
        df_combined = pd.concat([df_existing, df_new_filtered], ignore_index=True)
        df_combined = df_combined.sort_values("date").reset_index(drop=True)
    
    # Sauvegarder
    try:
        df_combined.to_csv(WEATHER_PATH, index=False)
        new_count = len(df_new_filtered)
        print(f"✅ Fichier mis à jour : {new_count} nouvelles lignes ajoutées")
        print(f"   Total : {len(df_combined)} lignes")
        print(f"   Plage : {df_combined['date'].min().date()} à {df_combined['date'].max().date()}")
        return True
    except Exception as e:
        print(f"❌ Erreur lors de la sauvegarde : {e}")
        return False

if __name__ == "__main__":
    success = update_meteo_dataset()
    sys.exit(0 if success else 1)

