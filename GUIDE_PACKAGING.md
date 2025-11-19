# Guide de Packaging et Distribution

Ce guide explique comment packager et distribuer l'application Pépinière Valbray pour Windows et macOS.

## 📋 Prérequis

### Pour construire les exécutables

1. **Python 3.8+** installé
2. **Toutes les dépendances** installées :
   ```bash
   pip install -r requirements.txt
   ```
3. **Node.js et npm** (pour compiler le frontend React)
4. **PyInstaller** installé :
   ```bash
   pip install pyinstaller
   ```

### Plateformes requises

⚠️ **IMPORTANT** : PyInstaller ne peut pas cross-compiler. Vous devez construire l'exécutable sur chaque plateforme cible :
- **Windows** : Construire sur une machine Windows
- **macOS** : Construire sur une machine macOS

### 💡 Solution : GitHub Actions (Recommandé)

**Vous n'avez pas besoin de deux machines physiques !** Utilisez GitHub Actions pour construire automatiquement sur les deux plateformes dans le cloud :

1. Poussez votre code sur GitHub
2. Créez un tag de version : `git tag v1.0.0 && git push origin v1.0.0`
3. GitHub Actions construit automatiquement les exécutables
4. Une release GitHub est créée avec les fichiers téléchargeables

**Voir** : `GUIDE_GITHUB_ACTIONS.md` pour les détails complets.

## 🔨 Construction des Exécutables

### Windows

1. Sur une machine **Windows**, ouvrez PowerShell ou CMD
2. Naviguez vers le dossier du projet
3. Exécutez :
   ```bash
   python build_windows.py
   ```

Le script va :
- Compiler automatiquement le frontend React
- Créer l'exécutable Windows dans `dist/PepiniereValbray/PepiniereValbray.exe`

**Résultat** : Dossier `dist/PepiniereValbray/` contenant tous les fichiers nécessaires

### macOS

1. Sur une machine **macOS**, ouvrez Terminal
2. Naviguez vers le dossier du projet
3. Exécutez :
   ```bash
   python build_macos.py
   ```

Le script va :
- Compiler automatiquement le frontend React
- Créer l'application macOS dans `dist/PepiniereValbray.app`

**Résultat** : Application macOS `dist/PepiniereValbray.app`

## 📦 Distribution

### Windows

#### Option 1 : Distribution directe (simple)

1. Compressez le dossier `dist/PepiniereValbray/` en ZIP
2. Distribuez le fichier ZIP
3. L'utilisateur doit :
   - Extraire le ZIP
   - Double-cliquer sur `PepiniereValbray.exe`

#### Option 2 : Créer un installateur (recommandé)

**Avec Inno Setup (gratuit)** :

1. Téléchargez Inno Setup : https://jrsoftware.org/isinfo.php
2. Créez un script `.iss` :
   ```iss
   [Setup]
   AppName=Pepiniere Valbray
   AppVersion=1.0
   DefaultDirName={pf}\PepiniereValbray
   DefaultGroupName=Pepiniere Valbray
   OutputDir=installer
   OutputBaseFilename=PepiniereValbray-Setup
   Compression=lzma
   SolidCompression=yes

   [Files]
   Source: "dist\PepiniereValbray\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs

   [Icons]
   Name: "{group}\Pepiniere Valbray"; Filename: "{app}\PepiniereValbray.exe"
   Name: "{commondesktop}\Pepiniere Valbray"; Filename: "{app}\PepiniereValbray.exe"
   ```
3. Compilez avec Inno Setup Compiler

**Avec NSIS (gratuit)** :

1. Téléchargez NSIS : https://nsis.sourceforge.io/
2. Créez un script `.nsi` similaire

### macOS

#### Option 1 : Distribution directe (simple)

1. Compressez `dist/PepiniereValbray.app` en ZIP
2. Distribuez le fichier ZIP
3. L'utilisateur doit :
   - Extraire le ZIP
   - Double-cliquer sur `PepiniereValbray.app`
   - Si macOS bloque l'application : Clic droit → Ouvrir → Ouvrir

#### Option 2 : Créer un fichier DMG (recommandé)

**Avec create-dmg** :

```bash
npm install -g create-dmg
create-dmg dist/PepiniereValbray.app dist/
```

**Avec hdiutil (intégré macOS)** :

```bash
hdiutil create -volname "PepiniereValbray" \
  -srcfolder dist/PepiniereValbray.app \
  -ov -format UDZO \
  dist/PepiniereValbray.dmg
```

#### Option 3 : Signature de code (optionnel mais recommandé)

Pour éviter les avertissements de sécurité sur macOS :

1. Obtenez un certificat Apple Developer (gratuit ou payant)
2. Signez l'application :
   ```bash
   codesign --deep --force --verify --verbose \
     --sign "Developer ID Application: Votre Nom" \
     dist/PepiniereValbray.app
   ```
3. Vérifiez la signature :
   ```bash
   codesign --verify --verbose dist/PepiniereValbray.app
   ```

## 📁 Structure des Fichiers Distribués

### Windows

```
PepiniereValbray/
├── PepiniereValbray.exe
├── _internal/
│   ├── (tous les fichiers Python et dépendances)
│   └── ...
└── (fichiers de données inclus dans l'exécutable)
```

### macOS

```
PepiniereValbray.app/
└── Contents/
    ├── MacOS/
    │   └── PepiniereValbray
    ├── Resources/
    │   └── (tous les fichiers Python et dépendances)
    └── ...
```

## ✅ Checklist de Distribution

Avant de distribuer, vérifiez :

- [ ] Le frontend React est compilé et inclus
- [ ] L'exécutable démarre correctement
- [ ] L'interface web s'ouvre dans le navigateur
- [ ] Les fonctionnalités principales fonctionnent
- [ ] Les fichiers de données sont accessibles
- [ ] L'application fonctionne sur un ordinateur sans Python installé
- [ ] (Windows) L'antivirus ne bloque pas l'exécutable
- [ ] (macOS) L'application peut être ouverte (ou signée)

## 🐛 Résolution de Problèmes

### L'exécutable ne démarre pas

1. Vérifiez les logs dans le terminal (si console=True dans le .spec)
2. Vérifiez que tous les fichiers nécessaires sont présents
3. Testez sur une machine propre sans Python

### Module non trouvé

1. Ajoutez le module dans `hiddenimports` du fichier `.spec`
2. Reconstruisez l'exécutable

### Frontend non chargé

1. Vérifiez que `frontend/build/index.html` existe
2. Recompilez le frontend : `cd frontend && npm run build`
3. Reconstruisez l'exécutable

### macOS : "L'application est endommagée"

1. Signez l'application avec un certificat Apple Developer
2. Ou indiquez à l'utilisateur de faire : Clic droit → Ouvrir

### Windows : Antivirus bloque l'exécutable

1. Ajoutez une exception dans l'antivirus
2. Signez l'exécutable avec un certificat de code (nécessite un certificat payant)

## 📝 Notes Importantes

1. **Taille** : Les exécutables seront volumineux (100-200 MB) car ils incluent Python et toutes les dépendances. C'est normal.

2. **Performance** : Le mode `--onedir` (dossier) est plus rapide au démarrage que `--onefile` (fichier unique).

3. **Mise à jour** : Pour mettre à jour l'application, reconstruisez l'exécutable et redistribuez-le. Les données utilisateur (recoltes.db, etc.) sont stockées dans le dossier de l'application.

4. **Compatibilité** :
   - Windows : Windows 10/11 (64-bit)
   - macOS : macOS 10.15+ (Catalina et plus récent)

## 🚀 Automatisation (Optionnel)

Vous pouvez créer des scripts CI/CD pour automatiser le build :

- **GitHub Actions** : Créez des workflows pour Windows et macOS
- **GitLab CI** : Utilisez des runners Windows et macOS
- **AppVeyor** : Pour Windows
- **Travis CI** : Pour macOS

---

**Bon packaging ! 📦**

