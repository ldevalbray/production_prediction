# README Technique - Système de Prédiction de Récoltes de Fraises

## 📋 Vue d'ensemble

Ce projet implémente un système de prédiction de récoltes de fraises basé sur l'apprentissage automatique. Il utilise un modèle Random Forest pour prédire les récoltes futures en se basant sur les données historiques, les conditions météorologiques, et l'organisation hebdomadaire des récoltes.

## 🏗️ Architecture

### Structure des fichiers

```
Pepiniere valbray/
├── recoltes_fraises.xlsx          # Fichier Excel principal (données maîtres)
├── auto_update_model_v4.py        # Script de mise à jour et entraînement du modèle
├── forecast_next3days_v3.py       # Script de génération de prévisions
├── train_model.py                 # Script d'entraînement du modèle ML
├── launcher_gui.py                # Interface graphique utilisateur
├── run_daily_cycle.py             # Script de pipeline quotidien
├── transform_excel.py             # Script de transformation de données
├── meteo_dataset.csv              # Données météorologiques historiques
├── dataset_ready_for_model.csv    # Dataset préparé pour l'entraînement
├── model_fraises_v2.pkl          # Modèle entraîné (Random Forest)
├── forecasts/                     # Dossier des prévisions générées
└── models_archive/                # Archive des modèles et datasets
```

### Fichier Excel principal : `recoltes_fraises.xlsx`

#### Onglet "Recoltes"
- **Colonnes** : `date`, `variety`, `kg_total`, `commentaires`
- **Description** : Historique des récoltes par date et variété
- **Note** : Pas de colonne `parcelle` car elle est déduite depuis "Paramètres"

#### Onglet "Paramètres"
- **Colonnes** : `parcelle`, `variety`, `nb_rangees`
- **Description** : Paramètres de chaque combinaison parcelle/variété
- **Note** : `nb_rangees` peut être vide (valeur par défaut : 10)

#### Onglet "Jour_courant"
- **Colonnes** : `date`, `variety`, `kg_premiere_rangee`, `commentaires`
- **Description** : Données du jour en cours (peut être vide le matin)
- **Usage** : Améliore les prévisions si renseigné

#### Onglet "Plants_par_annee"
- **Colonnes** : `variety`, `Année`, `Nb_plants`
- **Description** : Nombre de plants par variété et par année
- **Usage** : Feature supplémentaire pour le modèle

#### Onglet "Recolte_quotidienne"
- **Colonnes** : `jour_semaine`, `jour_semaine_num`, `fraction_fraiseraie`, `description`
- **Description** : Paramètres de récolte par jour de la semaine
- **Usage** : Configuration de la fraction de fraiseraie récoltée chaque jour

## 🔧 Scripts principaux

### `auto_update_model_v4.py`

**Fonction** : Mise à jour du dataset et réentraînement du modèle

**Processus** :
1. Lecture des données depuis `recoltes_fraises.xlsx`
2. Fusion avec les paramètres (parcelle, nb_rangees)
3. Calcul de `kg_par_rangee` = `kg_total / nb_rangees`
4. Ajout des features d'organisation hebdomadaire :
   - `jour_semaine` : Jour de la semaine (0=Lundi, 6=Dimanche)
   - `fraction_fraiseraie` : Fraction récoltée (depuis "Recolte_quotidienne")
   - `jours_since_last_recolte` : Jours depuis dernière récolte (par parcelle/variété)
   - `jours_since_last_recolte_globale` : Jours depuis dernière récolte globale
5. Fusion avec les données météorologiques (`meteo_dataset.csv`)
6. Intégration de `nb_plants` depuis "Plants_par_annee"
7. Sauvegarde du dataset dans `dataset_ready_for_model.csv`
8. Appel de `train_model.py` pour l'entraînement
9. Archivage du modèle et du dataset

**Dépendances** :
- `pandas`, `numpy`, `joblib`
- Fichiers requis : `recoltes_fraises.xlsx`, `meteo_dataset.csv`

### `forecast_next3days_v3.py`

**Fonction** : Génération de prévisions pour les 3 prochains jours

**Processus** :
1. Chargement du modèle entraîné (`model_fraises_v2.pkl`)
2. Lecture des paramètres depuis "Paramètres"
3. Lecture optionnelle de "Jour_courant" (peut être vide)
4. Lecture de l'historique depuis "Recoltes"
5. Téléchargement des prévisions météo via API Open-Meteo
6. Génération des combinaisons parcelle/variété × dates
7. Ajout des features :
   - Données météorologiques
   - `nb_plants` depuis "Plants_par_annee"
   - Features d'organisation hebdomadaire
   - Contexte de production (dernières récoltes)
8. Prédiction avec le modèle
9. Calcul des intervalles de confiance
10. Export Excel dans `forecasts/` avec :
    - Données météorologiques prévues
    - Prédictions de récolte (par rangée et total)
    - Intervalles de confiance

**Dépendances** :
- `pandas`, `numpy`, `joblib`, `requests`, `openpyxl`
- Fichiers requis : `recoltes_fraises.xlsx`, `model_fraises_v2.pkl`
- API : Open-Meteo (https://api.open-meteo.com)

### `train_model.py`

**Fonction** : Entraînement du modèle Random Forest

**Processus** :
1. Lecture du dataset (`dataset_ready_for_model.csv`)
2. Préparation des features :
   - Features numériques : `temp_mean`, `temp_min`, `temp_max`, `rain_mm`, `humidity`, `sun_hours`, `kg_par_rangee_prev_day`
   - Features optionnelles : `nb_plants`, `jour_semaine`, `fraction_fraiseraie`, `jours_since_last_recolte`, `jours_since_last_recolte_globale`
   - Encodage one-hot : `parcelle`, `variety`
3. Division train/test (80/20)
4. Entraînement Random Forest :
   - `n_estimators=300`
   - `max_depth=15`
   - `random_state=42`
5. Évaluation (RMSE, R²)
6. Sauvegarde du modèle

**Dépendances** :
- `pandas`, `numpy`, `sklearn`, `joblib`
- Fichier requis : `dataset_ready_for_model.csv`

### `launcher_gui.py`

**Fonction** : Interface graphique utilisateur

**Fonctionnalités** :
- Bouton "Mettre à jour le modèle" → exécute `auto_update_model_v4.py`
- Bouton "Générer prévisions" → exécute `forecast_next3days_v3.py`
- Affichage de l'historique des exécutions
- Ouverture des fichiers générés
- Indicateurs visuels de progression

**Dépendances** :
- `ttkbootstrap`, `tkinter`
- Scripts : `auto_update_model_v4.py`, `forecast_next3days_v3.py`

### `run_daily_cycle.py`

**Fonction** : Pipeline quotidien automatisé

**Usage** :
```bash
python run_daily_cycle.py --mode forecast  # Matin : prévisions
python run_daily_cycle.py --mode update    # Soir : réentraînement
```

## 📊 Features du modèle

### Features météorologiques
- `temp_mean` : Température moyenne
- `temp_min` : Température minimale
- `temp_max` : Température maximale
- `rain_mm` : Précipitations (mm)
- `humidity` : Humidité relative (%)
- `sun_hours` : Heures d'ensoleillement

### Features de production
- `kg_par_rangee_prev_day` : Récolte précédente (kg par rangée)
- `nb_plants` : Nombre de plants (depuis "Plants_par_annee")
- `parcelle_*` : Encodage one-hot des parcelles
- `variety_*` : Encodage one-hot des variétés

### Features d'organisation hebdomadaire
- `jour_semaine` : Jour de la semaine (0-6)
- `fraction_fraiseraie` : Fraction de fraiseraie récoltée (depuis "Recolte_quotidienne")
- `jours_since_last_recolte` : Jours depuis dernière récolte (par parcelle/variété)
- `jours_since_last_recolte_globale` : Jours depuis dernière récolte globale

## 🔄 Flux de données

```
recoltes_fraises.xlsx
    ↓
auto_update_model_v4.py
    ├─→ Fusion avec Paramètres
    ├─→ Calcul kg_par_rangee
    ├─→ Ajout features hebdomadaires
    ├─→ Fusion avec météo
    ├─→ Intégration Plants_par_annee
    ↓
dataset_ready_for_model.csv
    ↓
train_model.py
    ├─→ Préparation features
    ├─→ Entraînement Random Forest
    ↓
model_fraises_v2.pkl
    ↓
forecast_next3days_v3.py
    ├─→ Chargement modèle
    ├─→ Prévisions météo (API)
    ├─→ Génération prévisions
    ├─→ Export avec données météo
    ↓
forecasts/forecast_next3days_YYYY-MM-DD.xlsx
    (contient : météo + prédictions + intervalles de confiance)
```

## 🛠️ Configuration

### Paramètres modifiables dans Excel

1. **"Recolte_quotidienne"** : Fractions de récolte par jour
2. **"Paramètres"** : Nombre de rangées par parcelle/variété
3. **"Plants_par_annee"** : Nombre de plants par année

### Paramètres dans le code

- **`auto_update_model_v4.py`** :
  - `EXCEL_PATH` : Chemin du fichier Excel
  - `WEATHER_PATH` : Chemin du fichier météo
  - `MODEL_OUTPUT` : Nom du modèle

- **`forecast_next3days_v3.py`** :
  - `LAT, LON` : Coordonnées GPS (Hyères : 43.12, 6.14)
  - `FORECAST_DAYS` : Nombre de jours de prévision (3)
  - `TIMEZONE` : Fuseau horaire ("Europe/Paris")

## 🐛 Gestion des erreurs

### Cas gérés automatiquement

1. **"Jour_courant" vide** : Utilise uniquement les données historiques
2. **`nb_rangees` vide** : Valeur par défaut = 10
3. **`nb_plants` manquant** : Utilise la moyenne par variété ou globale
4. **Onglet "Recolte_quotidienne" manquant** : Valeurs par défaut codées en dur
5. **Données météo manquantes** : Avertissement affiché

### Logs et archivage

- Les modèles sont archivés dans `models_archive/` avec date
- Les logs d'entraînement sont sauvegardés
- L'historique des exécutions est dans `last_runs.json`

## 📦 Dépendances Python

```python
pandas>=1.5.0
numpy>=1.20.0
scikit-learn>=1.0.0
joblib>=1.0.0
openpyxl>=3.0.0
requests>=2.25.0
ttkbootstrap>=1.10.0
```

## 🔍 Points d'attention

1. **Format des dates** : Doit être compatible avec `pd.to_datetime()`
2. **Noms de variétés** : Insensibles à la casse, normalisés en minuscules
3. **Fichier météo** : Doit contenir toutes les dates des récoltes
4. **Modèle** : Le modèle doit être réentraîné si les features changent
5. **API météo** : Nécessite une connexion internet pour les prévisions

## 📤 Format du fichier de prévisions

Le fichier Excel généré (`forecasts/forecast_next3days_YYYY-MM-DD.xlsx`) contient :

### Colonnes d'information
- `date`, `horizon`, `parcelle`, `variety`

### Données météorologiques prévues
- `temp_mean`, `temp_min`, `temp_max` : Températures (°C)
- `rain_mm` : Précipitations (mm)
- `humidity` : Humidité relative (%)
- `sun_hours` : Heures d'ensoleillement

### Prédictions
- `predicted_kg_par_rangee` : Prédiction par rangée (kg)
- `predicted_std_par_rangee` : Écart-type par rangée
- `nb_rangees` : Nombre de rangées
- `predicted_kg_total` : Prédiction totale (kg)
- `predicted_std_kg_total` : Écart-type total
- `confidence_min_kg_total` : Minimum de l'intervalle de confiance
- `confidence_max_kg_total` : Maximum de l'intervalle de confiance

## 🚀 Améliorations futures possibles

- Ajout de features saisonnières (mois, jour de l'année)
- Support de plusieurs modèles (par variété)
- Interface web au lieu de GUI desktop
- Automatisation complète (cron jobs)
- Intégration de données supplémentaires (irrigation, traitements)

