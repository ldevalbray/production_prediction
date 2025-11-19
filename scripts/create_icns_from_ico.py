#!/usr/bin/env python3
"""
Script pour créer un fichier .icns à partir d'un fichier .ico ou .png.
Utilise PIL pour redimensionner et iconutil (macOS) pour créer le .icns.
"""
import sys
import subprocess
from pathlib import Path
from PIL import Image

def create_icns_from_ico():
    """Crée un fichier .icns à partir d'un fichier .ico."""
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    assets_dir = project_dir / "assets"
    
    # Chercher le fichier source (.ico ou .png)
    ico_path = assets_dir / "icon.ico"
    png_path = assets_dir / "icon.png"
    svg_path = assets_dir / "icon.svg"
    
    source_path = None
    if ico_path.exists():
        source_path = ico_path
        print(f"📦 Utilisation de {ico_path}")
    elif png_path.exists():
        source_path = png_path
        print(f"📦 Utilisation de {png_path}")
    else:
        print(f"❌ Aucun fichier source trouvé (icon.ico ou icon.png)")
        print(f"   Créez d'abord icon.ico ou icon.png dans {assets_dir}")
        return False
    
    if sys.platform != "darwin":
        print("⚠️  Ce script nécessite macOS pour créer un fichier .icns")
        print("   Sur Linux/Windows, créez le .iconset manuellement puis utilisez iconutil sur macOS")
        return False
    
    # Utiliser iconutil (disponible sur macOS)
    iconutil_path = "/usr/bin/iconutil"
    if not Path(iconutil_path).exists():
        # Essayer sans chemin absolu
        iconutil_path = "iconutil"
    
    # Créer un dossier temporaire pour le .iconset
    temp_dir = project_dir / ".icon_temp"
    temp_dir.mkdir(exist_ok=True)
    iconset_dir = temp_dir / "PepiniereValbray.iconset"
    
    # Nettoyer si existe déjà
    import shutil
    if iconset_dir.exists():
        shutil.rmtree(iconset_dir)
    iconset_dir.mkdir()
    
    try:
        # Ouvrir l'image source
        print(f"📐 Ouverture de {source_path}...")
        img = Image.open(source_path)
        
        # Tailles nécessaires pour macOS .icns
        sizes = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16@2x.png"),  # 16@2x = 32
            (32, "icon_32x32.png"),
            (64, "icon_32x32@2x.png"),  # 32@2x = 64
            (128, "icon_128x128.png"),
            (256, "icon_128x128@2x.png"),  # 128@2x = 256
            (256, "icon_256x256.png"),
            (512, "icon_256x256@2x.png"),  # 256@2x = 512
            (512, "icon_512x512.png"),
            (1024, "icon_512x512@2x.png"),  # 512@2x = 1024
        ]
        
        print("🔄 Génération des tailles d'icône...")
        for size, filename in sizes:
            # Redimensionner l'image
            resized = img.resize((size, size), Image.Resampling.LANCZOS)
            output_path = iconset_dir / filename
            resized.save(output_path, "PNG")
            print(f"   ✓ {filename} ({size}x{size})")
        
        # Convertir le .iconset en .icns avec iconutil
        print("\n🍎 Conversion en .icns...")
        icns_path = assets_dir / "icon.icns"
        
        result = subprocess.run(
            [iconutil_path, "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print(f"✅ Icône macOS créée: {icns_path}")
            print(f"   Taille: {icns_path.stat().st_size / 1024:.1f} KB")
            return True
        else:
            print(f"❌ Erreur lors de la conversion:")
            print(result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Garder le .iconset pour référence (optionnel)
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass

if __name__ == "__main__":
    success = create_icns_from_ico()
    sys.exit(0 if success else 1)

