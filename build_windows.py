#!/usr/bin/env python3
"""
Script pour créer un exécutable Windows de l'application Pépinière Valbray.
À exécuter sur une machine Windows avec Python installé.

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
    """Construit l'exécutable Windows avec PyInstaller."""
    print("🔨 Construction de l'exécutable Windows...")
    print("=" * 60)
    
    # Vérifier que nous sommes sur Windows
    if sys.platform != "win32":
        print("❌ Ce script doit être exécuté sur Windows.")
        print("   Pour macOS, utilisez build_macos.py")
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
    
    # Utiliser le fichier .spec pour Windows
    spec_file = "pepiniere_valbray_windows.spec"
    
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
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        
        # Vérifier que l'exécutable a bien été créé
        exe_path = Path("dist") / app_name / f"{app_name}.exe"
        if not exe_path.exists():
            raise FileNotFoundError(f"L'exécutable n'a pas été créé : {exe_path}")
        
        print()
        print("=" * 60)
        print("✅ Exécutable Windows créé avec succès !")
        print()
        
        print(f"📦 Exécutable Windows : {exe_path}")
        
        print()
        print("📋 IMPORTANT pour la distribution :")
        print("   1. Distribuez TOUT le dossier 'dist/PepiniereValbray/'")
        print("   2. L'utilisateur doit double-cliquer sur PepiniereValbray.exe")
        print("   3. Les fichiers de données sont inclus dans l'exécutable")
        if frontend_built:
            print("   4. ✅ Le frontend React est inclus")
        else:
            print("   4. ⚠️  Le frontend React n'est PAS inclus (non compilé)")
        print("   5. L'application démarre un serveur web local sur http://127.0.0.1:5000")
        print("   6. Testez l'exécutable avant de le distribuer")
        print()
        print("💡 Pour créer un installateur Windows, vous pouvez utiliser:")
        print("   - Inno Setup (gratuit): https://jrsoftware.org/isinfo.php")
        print("   - NSIS (gratuit): https://nsis.sourceforge.io/")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print()
        print("❌ Erreur lors de la construction de l'exécutable")
        print(f"   Code retour : {e.returncode}")
        if e.stdout:
            print("   Sortie standard :")
            print(e.stdout)
        if e.stderr:
            print("   Erreur standard :")
            print(e.stderr)
        raise  # Lever l'exception pour que GitHub Actions détecte l'échec
    except Exception as e:
        print()
        print(f"❌ Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        raise  # Lever l'exception pour que GitHub Actions détecte l'échec

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)

