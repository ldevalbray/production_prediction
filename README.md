# Pépinière Valbray - Application de Gestion et Prédiction

Application de gestion et de prédiction des récoltes de fraises avec interface web moderne.

## 📁 Structure du Projet

```
Pepiniere valbray/
├── app.py                    # Application Flask principale
├── config.py                 # Configuration centralisée
├── database.py               # Gestion de la base de données SQLite
├── data_loader.py            # Chargement des données (Excel/SQLite)
├── validators.py             # Validation des données
├── logger_config.py          # Configuration des logs
├── pyinstaller_utils.py      # Utilitaires PyInstaller
├── system_tray.py            # Icône système (tray icon)
├── launcher_gui.py           # Interface graphique alternative
├── cache_utils.py            # Gestion du cache
├── requirements.txt          # Dépendances Python
│
├── docs/                     # Documentation
│   ├── README_UTILISATEUR.md
│   ├── README_TECHNIQUE.md
│   ├── README_DATABASE.md
│   ├── README_PACKAGING.md
│   ├── GUIDE_BUILD.md
│   ├── GUIDE_PACKAGING.md
│   ├── GUIDE_GITHUB_ACTIONS.md
│   ├── AMELIORATIONS.md
│   └── RAPPORT_VERIFICATION_MODELE.md
│
├── scripts/                  # Scripts utilitaires
│   ├── build_executable.py
│   ├── build_macos.py
│   ├── build_windows.py
│   ├── auto_update_model_v4.py
│   ├── forecast_next3days_v3.py
│   ├── train_model.py
│   ├── update_meteo_dataset.py
│   ├── migrate_excel_to_db.py
│   ├── run_daily_cycle.py
│   ├── check_and_configure_xcode.sh
│   └── start_web.sh
│
├── models/                   # Modèles ML
│   ├── model_fraises_v2.pkl
│   └── models_archive/       # Archives des modèles
│
├── data/                     # Fichiers de données
│   ├── recoltes_fraises.xlsx
│   ├── meteo_dataset.csv
│   └── dataset_ready_for_model.csv
│
├── build_config/             # Configuration PyInstaller
│   ├── pepiniere_valbray.spec
│   ├── pepiniere_valbray_macos.spec
│   └── pepiniere_valbray_windows.spec
│
├── frontend/                 # Interface web React
│   ├── src/
│   ├── public/
│   └── package.json
│
├── assets/                   # Ressources
│   └── splash.png
│
├── forecasts/                # Prévisions générées
├── dist/                     # Exécutables compilés
└── recoltes.db               # Base de données SQLite
```

## 🚀 Démarrage Rapide

### Installation

1. Installer les dépendances Python :
```bash
pip install -r requirements.txt
```

2. Installer les dépendances frontend (optionnel) :
```bash
cd frontend
npm install
npm run build
cd ..
```

3. Lancer l'application :
```bash
python app.py
```

L'application sera accessible sur `http://127.0.0.1:5000`

## 📚 Documentation

- **Utilisateur** : `docs/README_UTILISATEUR.md`
- **Technique** : `docs/README_TECHNIQUE.md`
- **Base de données** : `docs/README_DATABASE.md`
- **Packaging** : `docs/README_PACKAGING.md`
- **Build** : `docs/GUIDE_BUILD.md`
- **Mise en production** : `docs/FLOW_MISE_EN_PRODUCTION.md` ⭐
- **Mise à jour automatique** : `docs/GUIDE_MISE_A_JOUR.md`

## 🔧 Configuration

La configuration se fait via `config.py` ou via des variables d'environnement. Voir `config.py` pour les options disponibles.

## 📦 Compilation

Pour créer un exécutable standalone :

```bash
# macOS
python scripts/build_macos.py

# Windows
python scripts/build_windows.py

# Linux / Générique
python scripts/build_executable.py
```

## 🗂️ Organisation des Fichiers

- **`docs/`** : Toute la documentation du projet
- **`scripts/`** : Scripts Python utilitaires (build, ML, migration, etc.)
- **`models/`** : Modèles d'apprentissage machine et leurs archives
- **`data/`** : Fichiers de données (Excel, CSV)
- **`build_config/`** : Fichiers de configuration PyInstaller (.spec)
- **`frontend/`** : Application React (interface web)
- **`assets/`** : Ressources statiques (images, etc.)

## 🔄 Migration des Données

Pour migrer les données Excel vers SQLite :

```bash
python scripts/migrate_excel_to_db.py
```

## 🤖 Modèle ML

- **Entraînement** : `python scripts/train_model.py`
- **Mise à jour automatique** : `python scripts/auto_update_model_v4.py`
- **Génération de prévisions** : `python scripts/forecast_next3days_v3.py`

## 📝 Notes

- Les fichiers de données sont recherchés dans `data/` en priorité, puis à la racine (compatibilité)
- Les modèles sont recherchés dans `models/` en priorité, puis à la racine
- Les scripts utilisent `config.py` pour les chemins, avec fallback automatique

