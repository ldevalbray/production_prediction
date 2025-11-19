#!/usr/bin/env python3
"""
Script pour créer un exécutable macOS (.app) de l'application Pépinière Valbray.
À exécuter sur une machine macOS avec Python installé.

Ce script compile automatiquement le frontend React avant de générer l'exécutable.
"""
import subprocess
import sys
import os
from pathlib import Path

def check_pyinstaller():
    """Vérifie si PyInstaller est installé."""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False

def check_node():
    """Vérifie si Node.js et npm sont installés."""
    try:
        subprocess.run(["node", "--version"], check=True, capture_output=True)
        subprocess.run(["npm", "--version"], check=True, capture_output=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def build_frontend():
    """Compile le frontend React."""
    frontend_dir = Path("frontend")
    build_dir = frontend_dir / "build"
    
    if not frontend_dir.exists():
        print("⚠️  Dossier frontend/ introuvable. Poursuite sans frontend...")
        return False
    
    print("📦 Compilation du frontend React...")
    
    if not check_node():
        print("⚠️  Node.js/npm non installé. Le frontend ne sera pas inclus.")
        print("   Installez Node.js depuis https://nodejs.org/")
        return False
    
    try:
        # Installer les dépendances si nécessaire
        if not (frontend_dir / "node_modules").exists():
            print("   Installation des dépendances npm...")
            subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                check=True,
                capture_output=True
            )
        
        # Compiler le frontend
        print("   Compilation en cours...")
        result = subprocess.run(
            ["npm", "run", "build"],
            cwd=frontend_dir,
            check=True,
            capture_output=True,
            text=True
        )
        
        if build_dir.exists() and (build_dir / "index.html").exists():
            print("✅ Frontend compilé avec succès!")
            return True
        else:
            print("⚠️  La compilation a réussi mais index.html est introuvable.")
            return False
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de la compilation du frontend:")
        print(f"   {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Erreur inattendue: {e}")
        return False

def build_executable():
    """Construit l'application macOS (.app) avec PyInstaller."""
    print("🔨 Construction de l'application macOS...")
    print("=" * 60)
    
    # Vérifier que nous sommes sur macOS
    if sys.platform != "darwin":
        print("❌ Ce script doit être exécuté sur macOS.")
        print("   Pour Windows, utilisez build_windows.py")
        print("   Pour Linux, utilisez build_executable.py")
        return False
    
    # Vérifier PyInstaller
    if not check_pyinstaller():
        print("❌ PyInstaller n'est pas installé.")
        print("👉 Installez-le avec : pip install pyinstaller")
        return False
    
    # Compiler le frontend React
    print()
    frontend_built = build_frontend()
    print()
    
    # Nom de l'application
    app_name = "PepiniereValbray"
    
    # Utiliser le fichier .spec pour macOS
    spec_file = "pepiniere_valbray_macos.spec"
    
    if not Path(spec_file).exists():
        print(f"❌ Fichier .spec introuvable : {spec_file}")
        return False
    
    if not Path("app.py").exists():
        print(f"❌ Fichier principal introuvable : app.py")
        return False
    
    # Options PyInstaller avec le fichier .spec
    options = [
        "--clean",  # Nettoyer le cache
        "--noconfirm",  # Ne pas demander confirmation
    ]
    
    # Commande complète avec le fichier .spec
    cmd = ["pyinstaller"] + options + [spec_file]
    
    print(f"📦 Commande PyInstaller :")
    print(" ".join(cmd))
    print("=" * 60)
    print()
    
    try:
        # Exécuter PyInstaller
        result = subprocess.run(cmd, check=True, capture_output=False)
        
        print()
        print("=" * 60)
        print("✅ Application macOS créée avec succès !")
        print()
        
        app_path = Path("dist") / f"{app_name}.app"
        print(f"📦 Application macOS : {app_path}")
        
        print()
        print("📋 IMPORTANT pour la distribution :")
        print("   1. Distribuez le fichier 'dist/PepiniereValbray.app'")
        print("   2. L'utilisateur peut double-cliquer sur l'application pour la lancer")
        print("   3. Les fichiers de données sont inclus dans l'application")
        if frontend_built:
            print("   4. ✅ Le frontend React est inclus")
        else:
            print("   4. ⚠️  Le frontend React n'est PAS inclus (non compilé)")
        print("   5. L'application démarre un serveur web local sur http://127.0.0.1:5000")
        print("   6. Testez l'application avant de la distribuer")
        print()
        print("⚠️  Note sur la signature de code (optionnel mais recommandé) :")
        print("   Pour distribuer l'application sans avertissements de sécurité,")
        print("   vous pouvez signer l'application avec votre certificat Apple Developer :")
        print("   codesign --deep --force --verify --verbose --sign 'Developer ID Application: Votre Nom' dist/PepiniereValbray.app")
        print()
        print("💡 Pour créer un installateur macOS (.dmg), vous pouvez utiliser:")
        print("   - create-dmg (gratuit): npm install -g create-dmg")
        print("   - hdiutil (intégré macOS): hdiutil create -volname 'PepiniereValbray' -srcfolder dist/PepiniereValbray.app -ov -format UDZO dist/PepiniereValbray.dmg")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print()
        print("❌ Erreur lors de la construction de l'application")
        print(f"   Code retour : {e.returncode}")
        return False
    except Exception as e:
        print()
        print(f"❌ Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)

