# 🚀 Packaging Rapide - Pépinière Valbray

## Utilisation Rapide

### Pour Windows

```bash
python build_windows.py
```

**Résultat** : `dist/PepiniereValbray/PepiniereValbray.exe`

### Pour macOS

```bash
python build_macos.py
```

**Résultat** : `dist/PepiniereValbray.app`

### Script Universel (détecte automatiquement la plateforme)

```bash
python build_executable.py
```

## 📋 Prérequis

1. Python 3.8+ installé
2. Dépendances installées : `pip install -r requirements.txt`
3. Node.js et npm (pour compiler le frontend React)

## 📦 Distribution

### Windows
- Distribuez le dossier `dist/PepiniereValbray/` complet
- Ou créez un installateur avec Inno Setup ou NSIS

### macOS
- Distribuez le fichier `dist/PepiniereValbray.app`
- Ou créez un fichier DMG avec `create-dmg` ou `hdiutil`

## ☁️ Build Automatique avec GitHub Actions (Recommandé)

**Pas besoin de deux machines !** Utilisez GitHub Actions pour construire automatiquement :

1. Poussez votre code sur GitHub
2. Créez un tag : `git tag v1.0.0 && git push origin v1.0.0`
3. Les exécutables sont construits automatiquement
4. Une release GitHub est créée avec les fichiers

**Voir** : `GUIDE_GITHUB_ACTIONS.md` pour les détails

## 📖 Documentation Complète

- `GUIDE_PACKAGING.md` - Guide complet de packaging
- `GUIDE_GITHUB_ACTIONS.md` - Build automatique avec GitHub Actions

---

**Note** : Les scripts compilent automatiquement le frontend React avant de créer l'exécutable.

