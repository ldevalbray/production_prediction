# Guide de construction d'exécutable standalone

Ce guide explique comment créer un exécutable standalone de l'application Pépinière Valbray qui fonctionne sur n'importe quel ordinateur (Windows, Mac, Linux) sans nécessiter Python ou des dépendances.

## 📋 Prérequis

### Pour construire l'exécutable (une seule fois)

1. **Python 3.8+** installé sur votre machine
2. **Toutes les dépendances** installées (voir ci-dessous)

### Installation des dépendances

```bash
# Installer toutes les dépendances nécessaires
pip install -r requirements.txt
```

## 🔨 Construction de l'exécutable

### Méthode 1 : Script automatique (recommandé)

```bash
python build_executable.py
```

Le script va :
- Vérifier que PyInstaller est installé
- Créer l'exécutable avec toutes les configurations nécessaires
- Vous indiquer où se trouve l'exécutable créé

### Méthode 2 : Utilisation directe de PyInstaller

```bash
# Avec le fichier .spec (recommandé)
pyinstaller pepiniere_valbray.spec

# Ou directement avec les options
# Mode --onedir (recommandé, plus rapide)
pyinstaller --name PepiniereValbray --onedir --windowed --clean launcher_gui.py

# Mode --onefile (un seul fichier, plus lent au démarrage)
pyinstaller --name PepiniereValbray --onefile --windowed --clean launcher_gui.py
```

### Choix entre --onedir et --onefile

- **--onedir** (recommandé) : Crée un dossier avec plusieurs fichiers
  - ✅ Démarrage plus rapide
  - ✅ Plus facile à déboguer
  - ❌ Plusieurs fichiers à distribuer

- **--onefile** : Crée un seul fichier exécutable
  - ✅ Un seul fichier à distribuer
  - ❌ Démarrage plus lent (extraction temporaire)
  - ❌ Plus difficile à déboguer

## 📦 Résultat

Après la construction, vous trouverez l'exécutable dans le dossier `dist/` :

### Mode --onedir (recommandé)
- **Windows** : `dist/PepiniereValbray/PepiniereValbray.exe`
- **macOS** : `dist/PepiniereValbray.app` (application macOS)
- **Linux** : `dist/PepiniereValbray/PepiniereValbray`

### Mode --onefile
- **Windows** : `dist/PepiniereValbray.exe`
- **macOS** : `dist/PepiniereValbray.app` (application macOS)
- **Linux** : `dist/PepiniereValbray`

## 📁 Distribution de l'application

### Structure recommandée pour la distribution

**Mode --onedir :**
```
PepiniereValbray/
├── PepiniereValbray.exe (ou tous les fichiers du dossier)
├── [autres fichiers PyInstaller]
├── recoltes_fraises.xlsx
├── meteo_dataset.csv
├── model_fraises_v2.pkl (optionnel, sera créé au premier lancement)
├── forecasts/ (sera créé automatiquement)
└── models_archive/ (sera créé automatiquement)
```

**Mode --onefile :**
```
PepiniereValbray/
├── PepiniereValbray.exe (ou .app sur Mac)
├── recoltes_fraises.xlsx
├── meteo_dataset.csv
├── model_fraises_v2.pkl (optionnel, sera créé au premier lancement)
├── forecasts/ (sera créé automatiquement)
└── models_archive/ (sera créé automatiquement)
```

### Instructions pour l'utilisateur final

1. **Copiez tout le dossier** sur l'ordinateur cible
2. **Double-cliquez** sur l'exécutable pour lancer l'application
3. **Aucune installation** n'est nécessaire !

## ⚠️ Notes importantes

### Fichiers nécessaires

L'exécutable doit être dans le même dossier que :
- `recoltes_fraises.xlsx` (fichier de données principal)
- `meteo_dataset.csv` (données météo historiques)
- `model_fraises_v2.pkl` (sera créé automatiquement si absent)

### Compatibilité

- **Windows** : Testé sur Windows 10/11
- **macOS** : Testé sur macOS 10.15+
- **Linux** : Testé sur Ubuntu 20.04+

### Taille de l'exécutable

L'exécutable sera assez volumineux (100-200 MB) car il inclut :
- Python et toutes les bibliothèques
- Tous les modules nécessaires (pandas, numpy, scikit-learn, etc.)

C'est normal et nécessaire pour fonctionner sans dépendances.

## 🐛 Résolution de problèmes

### Erreur "Module not found"

Si vous obtenez des erreurs de modules manquants lors de l'exécution :

1. Ajoutez le module dans `hiddenimports` du fichier `.spec`
2. Reconstruisez l'exécutable

### L'exécutable ne démarre pas

1. Vérifiez que tous les fichiers nécessaires sont présents
2. Sur macOS, vous devrez peut-être autoriser l'application dans les paramètres de sécurité
3. Sur Windows, l'antivirus peut bloquer l'exécutable (ajoutez une exception)

### L'application plante au démarrage

1. Vérifiez les logs dans le terminal (si disponible)
2. Assurez-vous que `recoltes_fraises.xlsx` est valide
3. Vérifiez que `meteo_dataset.csv` existe

## 🔄 Mise à jour de l'application

Pour créer une nouvelle version :

1. Modifiez le code si nécessaire
2. Reconstruisez l'exécutable avec `python build_executable.py`
3. Remplacez l'ancien exécutable par le nouveau
4. **Conservez** les fichiers de données (`recoltes_fraises.xlsx`, etc.)

## 📝 Personnalisation

### Ajouter une icône

1. Créez ou trouvez un fichier d'icône :
   - Windows : `.ico`
   - macOS : `.icns`
   - Linux : `.png`

2. Modifiez le fichier `.spec` :
   ```python
   exe = EXE(
       ...
       icon='chemin/vers/votre/icone.ico',  # ou .icns pour Mac
       ...
   )
   ```

3. Reconstruisez l'exécutable

### Modifier le nom de l'application

Modifiez la ligne `name='PepiniereValbray'` dans le fichier `.spec`.

## 🚀 Optimisations (optionnel)

### Réduire la taille

Vous pouvez exclure des modules non utilisés dans le fichier `.spec` :

```python
excludes=[
    'matplotlib',  # Si non utilisé
    'scipy',       # Si non utilisé
    # etc.
]
```

### Améliorer les performances

L'option `--onefile` crée un seul fichier mais peut être plus lent au démarrage. Pour de meilleures performances :

1. Utilisez `--onedir` au lieu de `--onefile`
2. Distribuez tout le dossier créé dans `dist/`

---

**Bon build ! 🔨**

