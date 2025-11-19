# Guide de Création des Icônes

Ce guide explique comment créer les icônes pour l'application Pépinière Valbray.

## 🎨 Icône SVG

Une icône SVG a été créée dans `assets/icon.svg`. Elle représente une fraise avec des feuilles sur un fond vert, parfait pour une application de pépinière.

## 📦 Méthode 1 : Script Python (Recommandé)

### Installation des dépendances

```bash
pip install cairosvg Pillow
```

### Génération des icônes

```bash
python scripts/create_icon.py
```

Le script va :
- Convertir le SVG en différentes tailles de PNG
- Créer `assets/icon.ico` pour Windows
- Créer `assets/icon.icns` pour macOS (si sur macOS)

## 📦 Méthode 2 : Outils en ligne

Si vous préférez utiliser des outils en ligne :

### Pour Windows (.ico)
1. Allez sur https://convertio.co/svg-ico/
2. Uploadez `assets/icon.svg`
3. Téléchargez `icon.ico`
4. Placez-le dans `assets/icon.ico`

### Pour macOS (.icns)
1. Allez sur https://cloudconvert.com/svg-to-icns
2. Uploadez `assets/icon.svg`
3. Téléchargez `icon.icns`
4. Placez-le dans `assets/icon.icns`

## 📦 Méthode 3 : ImageMagick (macOS/Linux)

Si vous avez ImageMagick installé :

```bash
chmod +x scripts/create_icon.sh
./scripts/create_icon.sh
```

## ✅ Vérification

Une fois les icônes créées, vérifiez qu'elles existent :

```bash
ls -lh assets/icon.*
```

Vous devriez voir :
- `icon.svg` (source)
- `icon.ico` (Windows)
- `icon.icns` (macOS)

## 🔧 Utilisation dans les builds

Les fichiers `.spec` sont déjà configurés pour utiliser automatiquement les icônes si elles existent :

- **macOS** : `build_config/pepiniere_valbray_macos.spec` utilise `assets/icon.icns`
- **Windows** : `build_config/pepiniere_valbray_windows.spec` utilise `assets/icon.ico`

Si les icônes n'existent pas, l'application sera créée sans icône personnalisée (icône par défaut).

## 🎨 Personnalisation

Pour modifier l'icône :

1. Éditez `assets/icon.svg` avec un éditeur de texte ou un outil comme Inkscape
2. Régénérez les icônes avec une des méthodes ci-dessus
3. Rebuild l'application

## 📝 Notes

- Les icônes doivent être dans le dossier `assets/`
- Le SVG source est recommandé pour une qualité optimale à toutes les tailles
- Les icônes sont automatiquement incluses dans les builds PyInstaller

