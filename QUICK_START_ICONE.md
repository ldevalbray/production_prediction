# 🎨 Génération Rapide des Icônes

## Option la plus simple : Outil en ligne

### Pour Windows (.ico)
1. Allez sur : **https://convertio.co/svg-ico/**
2. Cliquez sur "Choisir les fichiers"
3. Sélectionnez `assets/icon.svg`
4. Cliquez sur "Convertir"
5. Téléchargez `icon.ico`
6. Placez-le dans `assets/icon.ico`

### Pour macOS (.icns)
1. Allez sur : **https://cloudconvert.com/svg-to-icns**
2. Cliquez sur "Select File"
3. Sélectionnez `assets/icon.svg`
4. Cliquez sur "Convert"
5. Téléchargez `icon.icns`
6. Placez-le dans `assets/icon.icns`

## Vérification

```bash
ls -lh assets/icon.*
```

Vous devriez voir :
- ✅ `icon.svg` (source)
- ✅ `icon.ico` (Windows)
- ✅ `icon.icns` (macOS)

## C'est tout !

Les icônes seront automatiquement utilisées lors du prochain build. 🎉

