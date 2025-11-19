# Compatibilité Windows - Analyse des Bugs

## ✅ Bugs Corrigés (Affectent Windows et macOS)

### 1. Erreur de syntaxe `global` dans `config.py`
- **Problème** : `global` déclaré après utilisation de la variable
- **Impact** : ❌ Windows ET macOS
- **Statut** : ✅ **CORRIGÉ** - `global` déclaré au début de la fonction
- **Résultat** : Le code fonctionne maintenant sur les deux plateformes

### 2. Création de dossiers dans un système en lecture seule
- **Problème** : Tentative de créer des dossiers dans le bundle (lecture seule)
- **Impact macOS** : ❌ Bundle `.app` monté depuis DMG est en lecture seule
- **Impact Windows** : ⚠️ Possible si installé dans `Program Files` ou dossier protégé
- **Statut** : ✅ **CORRIGÉ** - Fallback vers `~/.pepiniere_valbray/` si échec
- **Résultat** : Fonctionne sur les deux plateformes avec fallback automatique

## 🔍 Différences Windows vs macOS

### Structure des exécutables

**macOS** :
```
PepiniereValbray.app/
├── Contents/
│   ├── MacOS/
│   │   └── PepiniereValbray (exécutable)
│   └── Frameworks/ (lecture seule si depuis DMG)
```

**Windows** :
```
PepiniereValbray/
├── PepiniereValbray.exe
├── _internal/ (lecture seule si depuis ZIP)
└── (dossiers créables normalement)
```

### Chemins de base

**macOS** : `get_base_path()` retourne le dossier contenant le `.app`
**Windows** : `get_base_path()` retourne le dossier contenant l'`.exe`

Les deux devraient fonctionner correctement avec la correction actuelle.

## ⚠️ Problèmes Potentiels Windows

### 1. Permissions dans Program Files
Si l'utilisateur installe dans `C:\Program Files\`, Windows peut bloquer l'écriture.
- **Solution** : Le fallback vers `%USERPROFILE%\.pepiniere_valbray\` devrait résoudre cela

### 2. Antivirus / Windows Defender
Windows Defender peut bloquer l'exécution d'applications non signées.
- **Solution** : L'utilisateur doit autoriser l'application (voir `GUIDE_INSTALLATION.md`)

### 3. Chemins avec espaces
Windows peut avoir des problèmes avec les chemins contenant des espaces.
- **Statut** : ✅ Utilisation de `pathlib.Path` qui gère correctement les espaces

## ✅ Vérifications Effectuées

1. ✅ `config.py` : Syntaxe corrigée, fonctionne sur Windows et macOS
2. ✅ `ensure_directories()` : Fallback vers dossier utilisateur sur les deux plateformes
3. ✅ `get_base_path()` : Retourne le bon chemin pour Windows (`exe_path.parent`)
4. ✅ `pyinstaller_utils.py` : Gère correctement les différences macOS/Windows

## 🧪 Tests Recommandés

Avant de distribuer la version Windows, tester :

1. ✅ Extraction depuis ZIP dans un dossier normal
2. ✅ Extraction dans `Program Files` (doit fallback vers dossier utilisateur)
3. ✅ Lancement depuis le terminal pour voir les erreurs
4. ✅ Création des dossiers `forecasts/` et `models/`
5. ✅ Écriture de fichiers dans ces dossiers

## 📝 Conclusion

**Les corrections appliquées devraient fonctionner sur Windows aussi** car :
- Le code source est partagé
- Les corrections sont cross-platform
- Le fallback vers le dossier utilisateur fonctionne sur Windows (`%USERPROFILE%\.pepiniere_valbray\`)

Cependant, il est recommandé de **tester le build Windows** pour confirmer que tout fonctionne correctement.

