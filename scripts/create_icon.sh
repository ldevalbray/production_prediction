#!/bin/bash
# Script pour créer les icônes .icns (macOS) et .ico (Windows) à partir du SVG

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
ASSETS_DIR="$PROJECT_DIR/assets"
ICON_SVG="$ASSETS_DIR/icon.svg"

echo "🎨 Création des icônes à partir de $ICON_SVG"

# Vérifier que le SVG existe
if [ ! -f "$ICON_SVG" ]; then
    echo "❌ Erreur: $ICON_SVG introuvable"
    exit 1
fi

# Vérifier si ImageMagick est installé
if ! command -v convert &> /dev/null; then
    echo "⚠️  ImageMagick n'est pas installé."
    echo "   Installez-le avec: brew install imagemagick"
    echo "   Ou utilisez un outil en ligne pour convertir le SVG"
    exit 1
fi

# Créer un dossier temporaire pour les tailles d'icône
TEMP_DIR=$(mktemp -d)
trap "rm -rf $TEMP_DIR" EXIT

echo "📐 Génération des tailles d'icône..."

# Générer les différentes tailles nécessaires pour macOS .icns
sizes=(16 32 64 128 256 512 1024)
for size in "${sizes[@]}"; do
    convert -background none -resize "${size}x${size}" "$ICON_SVG" "$TEMP_DIR/icon_${size}x${size}.png"
    # Pour macOS, on a besoin aussi des tailles @2x
    convert -background none -resize "$((size * 2))x$((size * 2))" "$ICON_SVG" "$TEMP_DIR/icon_${size}x${size}@2x.png"
done

# Créer l'icône macOS (.icns)
echo "🍎 Création de l'icône macOS (.icns)..."
if command -v iconutil &> /dev/null; then
    # Créer la structure .iconset
    ICONSET_DIR="$TEMP_DIR/PepiniereValbray.iconset"
    mkdir -p "$ICONSET_DIR"
    
    # Copier les fichiers avec les noms requis par iconutil
    cp "$TEMP_DIR/icon_16x16.png" "$ICONSET_DIR/icon_16x16.png"
    cp "$TEMP_DIR/icon_16x16@2x.png" "$ICONSET_DIR/icon_32x32.png"
    cp "$TEMP_DIR/icon_32x32.png" "$ICONSET_DIR/icon_32x32.png"
    cp "$TEMP_DIR/icon_32x32@2x.png" "$ICONSET_DIR/icon_64x64.png"
    cp "$TEMP_DIR/icon_128x128.png" "$ICONSET_DIR/icon_128x128.png"
    cp "$TEMP_DIR/icon_128x128@2x.png" "$ICONSET_DIR/icon_256x256.png"
    cp "$TEMP_DIR/icon_256x256.png" "$ICONSET_DIR/icon_256x256.png"
    cp "$TEMP_DIR/icon_256x256@2x.png" "$ICONSET_DIR/icon_512x512.png"
    cp "$TEMP_DIR/icon_512x512@2x.png" "$ICONSET_DIR/icon_1024x1024.png"
    
    # Convertir en .icns
    iconutil -c icns "$ICONSET_DIR" -o "$ASSETS_DIR/icon.icns"
    echo "✅ Icône macOS créée: $ASSETS_DIR/icon.icns"
else
    echo "⚠️  iconutil non disponible, création de l'icône .icns ignorée"
fi

# Créer l'icône Windows (.ico)
echo "🪟 Création de l'icône Windows (.ico)..."
if command -v convert &> /dev/null; then
    # Créer un fichier .ico avec plusieurs tailles
    convert "$TEMP_DIR/icon_16x16.png" "$TEMP_DIR/icon_32x32.png" \
            "$TEMP_DIR/icon_64x64.png" "$TEMP_DIR/icon_128x128.png" \
            "$TEMP_DIR/icon_256x256.png" "$TEMP_DIR/icon_512x512.png" \
            "$ASSETS_DIR/icon.ico"
    echo "✅ Icône Windows créée: $ASSETS_DIR/icon.ico"
fi

echo ""
echo "✨ Icônes créées avec succès !"
echo "   - macOS: $ASSETS_DIR/icon.icns"
echo "   - Windows: $ASSETS_DIR/icon.ico"
echo ""
echo "📝 Pour utiliser ces icônes:"
echo "   1. macOS: Mettez à jour build_config/pepiniere_valbray_macos.spec avec icon='assets/icon.icns'"
echo "   2. Windows: Mettez à jour build_config/pepiniere_valbray_windows.spec avec icon='assets/icon.ico'"

