#!/usr/bin/env python3
"""
Script pour créer les icônes .icns (macOS) et .ico (Windows) à partir du SVG.
Utilise cairosvg ou PIL pour convertir le SVG en PNG, puis crée les icônes.
"""
import sys
import subprocess
from pathlib import Path

def check_dependencies():
    """Vérifie les dépendances nécessaires."""
    missing = []
    
    # Vérifier cairosvg (pour convertir SVG en PNG)
    try:
        import cairosvg
    except ImportError:
        missing.append("cairosvg")
    
    # Vérifier PIL/Pillow (pour manipuler les images)
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    return missing

def install_dependencies(missing):
    """Propose d'installer les dépendances manquantes."""
    print("⚠️  Dépendances manquantes:", ", ".join(missing))
    print("\n👉 Installez-les avec:")
    print(f"   pip install {' '.join(missing)}")
    print("\nOu utilisez un outil en ligne pour convertir le SVG:")
    print("   - https://convertio.co/svg-ico/")
    print("   - https://cloudconvert.com/svg-to-icns")
    return False

def create_icon_from_svg():
    """Crée les icônes à partir du SVG."""
    script_dir = Path(__file__).parent
    project_dir = script_dir.parent
    assets_dir = project_dir / "assets"
    icon_svg = assets_dir / "icon.svg"
    
    if not icon_svg.exists():
        print(f"❌ Erreur: {icon_svg} introuvable")
        return False
    
    print(f"🎨 Création des icônes à partir de {icon_svg}")
    
    # Vérifier les dépendances
    missing = check_dependencies()
    if missing:
        return install_dependencies(missing)
    
    try:
        import cairosvg
        from PIL import Image
        import io
    except ImportError as e:
        print(f"❌ Erreur d'import: {e}")
        return False
    
    # Créer un dossier temporaire
    temp_dir = project_dir / ".icon_temp"
    temp_dir.mkdir(exist_ok=True)
    
    try:
        # Tailles nécessaires pour les icônes
        sizes = [16, 32, 64, 128, 256, 512, 1024]
        
        print("📐 Génération des tailles d'icône...")
        for size in sizes:
            # Convertir SVG en PNG avec cairosvg
            png_path = temp_dir / f"icon_{size}x{size}.png"
            cairosvg.svg2png(url=str(icon_svg), write_to=str(png_path), output_width=size, output_height=size)
            print(f"   ✓ {size}x{size}")
        
        # Créer l'icône Windows (.ico)
        print("\n🪟 Création de l'icône Windows (.ico)...")
        ico_images = []
        for size in [16, 32, 64, 128, 256]:
            img_path = temp_dir / f"icon_{size}x{size}.png"
            if img_path.exists():
                ico_images.append(Image.open(img_path))
        
        if ico_images:
            ico_path = assets_dir / "icon.ico"
            ico_images[0].save(
                ico_path,
                format='ICO',
                sizes=[(img.width, img.height) for img in ico_images]
            )
            print(f"✅ Icône Windows créée: {ico_path}")
        
        # Créer l'icône macOS (.icns)
        print("\n🍎 Création de l'icône macOS (.icns)...")
        # Pour macOS, on a besoin d'un fichier .iconset
        iconset_dir = temp_dir / "PepiniereValbray.iconset"
        iconset_dir.mkdir(exist_ok=True)
        
        # Copier les fichiers avec les noms requis par iconutil
        icon_mapping = [
            (16, "icon_16x16.png"),
            (32, "icon_16x16.png"),  # 16@2x
            (32, "icon_32x32.png"),
            (64, "icon_32x32.png"),  # 32@2x
            (128, "icon_128x128.png"),
            (256, "icon_128x128.png"),  # 128@2x
            (256, "icon_256x256.png"),
            (512, "icon_256x256.png"),  # 256@2x
            (512, "icon_512x512.png"),
            (1024, "icon_512x512.png"),  # 512@2x
        ]
        
        # Créer les fichiers @2x si nécessaire
        for target_size, source_name in icon_mapping:
            source_path = temp_dir / source_name
            if source_name.endswith("@2x.png"):
                # Créer une version @2x en redimensionnant
                base_name = source_name.replace("@2x.png", ".png")
                base_path = temp_dir / base_name
                if base_path.exists():
                    img = Image.open(base_path)
                    img_2x = img.resize((target_size, target_size), Image.Resampling.LANCZOS)
                    source_path = temp_dir / f"icon_{target_size}x{target_size}.png"
                    img_2x.save(source_path)
            
            if source_path.exists():
                # Nommer selon les conventions macOS
                if target_size == 16:
                    dest_name = "icon_16x16.png"
                elif target_size == 32 and "16x16" in source_name:
                    dest_name = "icon_16x16@2x.png"
                elif target_size == 32:
                    dest_name = "icon_32x32.png"
                elif target_size == 64:
                    dest_name = "icon_32x32@2x.png"
                elif target_size == 128:
                    dest_name = "icon_128x128.png"
                elif target_size == 256 and "128x128" in source_name:
                    dest_name = "icon_128x128@2x.png"
                elif target_size == 256:
                    dest_name = "icon_256x256.png"
                elif target_size == 512 and "256x256" in source_name:
                    dest_name = "icon_256x256@2x.png"
                elif target_size == 512:
                    dest_name = "icon_512x512.png"
                elif target_size == 1024:
                    dest_name = "icon_512x512@2x.png"
                else:
                    continue
                
                import shutil
                shutil.copy2(source_path, iconset_dir / dest_name)
        
        # Convertir en .icns avec iconutil (macOS uniquement)
        if sys.platform == "darwin":
            try:
                icns_path = assets_dir / "icon.icns"
                subprocess.run(
                    ["iconutil", "-c", "icns", str(iconset_dir), "-o", str(icns_path)],
                    check=True,
                    capture_output=True
                )
                print(f"✅ Icône macOS créée: {icns_path}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("⚠️  iconutil non disponible, création de l'icône .icns ignorée")
                print("   Vous pouvez créer le .icns manuellement avec:")
                print(f"   iconutil -c icns {iconset_dir} -o {assets_dir / 'icon.icns'}")
        else:
            print("⚠️  macOS requis pour créer le .icns")
            print(f"   Le dossier .iconset est disponible dans: {iconset_dir}")
            print("   Copiez-le sur macOS et utilisez iconutil pour créer le .icns")
        
        print("\n✨ Icônes créées avec succès !")
        return True
        
    except Exception as e:
        print(f"❌ Erreur lors de la création des icônes: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Nettoyer (garder iconset_dir pour référence)
        # shutil.rmtree(temp_dir, ignore_errors=True)
        pass

if __name__ == "__main__":
    success = create_icon_from_svg()
    sys.exit(0 if success else 1)

