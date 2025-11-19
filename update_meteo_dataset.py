import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
from pathlib import Path
import sys

# === PARAMÈTRES ===
WEATHER_PATH = "meteo_dataset.csv"
LAT, LON = 43.12, 6.14  # Hyères (cohérent avec forecast_next3days_v3.py)
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
        "sunshine_duration,relative_humidity_2m_mean,wind_speed_10m_mean,wind_gusts_10m_max"
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
        df_new = pd.DataFrame({
            "date": pd.to_datetime(data["daily"]["time"]),
            "temp_max": data["daily"]["temperature_2m_max"],
            "temp_min": data["daily"]["temperature_2m_min"],
            "rain_mm": data["daily"]["precipitation_sum"],
            "sun_hours": np.array(data["daily"]["sunshine_duration"]) / 3600.0,  # Conversion secondes -> heures
            "humidity": data["daily"]["relative_humidity_2m_mean"],
            "wind_avg": data["daily"]["wind_speed_10m_mean"],
            "wind_gust": data["daily"]["wind_gusts_10m_max"]
        })
        
        # Calcul de temp_mean
        df_new["temp_mean"] = (df_new["temp_max"] + df_new["temp_min"]) / 2
        
        # Calcul de day_of_year
        df_new["day_of_year"] = df_new["date"].apply(get_day_of_year)
        
        # Réorganiser les colonnes dans l'ordre attendu
        df_new = df_new[[
            "date", "rain_mm", "temp_min", "temp_max", "temp_mean",
            "humidity", "wind_avg", "wind_gust", "sun_hours", "day_of_year"
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
            "humidity", "wind_avg", "wind_gust", "sun_hours", "day_of_year"
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
        # Éviter les doublons en supprimant les dates qui existent déjà
        df_existing_dates = set(df_existing["date"].dt.date)
        df_new_filtered = df_new[~df_new["date"].dt.date.isin(df_existing_dates)]
        
        if df_new_filtered.empty:
            print("✅ Aucune nouvelle donnée à ajouter (toutes les dates existent déjà)")
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

