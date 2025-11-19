#!/usr/bin/env python3
"""
Script pour créer un exécutable standalone de l'application Pépinière Valbray.
Utilise PyInstaller pour créer un exécutable qui fonctionne sans Python installé.

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
    """Construit l'exécutable avec PyInstaller."""
    print("🔨 Construction de l'exécutable standalone...")
    print("=" * 60)
    
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
    
    # Sélectionner le fichier .spec selon la plateforme (depuis build_config/)
    if sys.platform == "win32":
        spec_file = "build_config/pepiniere_valbray_windows.spec"
        print("🪟 Plateforme détectée : Windows")
    elif sys.platform == "darwin":
        spec_file = "build_config/pepiniere_valbray_macos.spec"
        print("🍎 Plateforme détectée : macOS")
    else:
        # Linux ou autre - utiliser le fichier .spec générique
        spec_file = "build_config/pepiniere_valbray.spec"
        print(f"🐧 Plateforme détectée : {sys.platform}")
    
    if not Path(spec_file).exists():
        print(f"❌ Fichier .spec introuvable : {spec_file}")
        print("   Utilisez build_windows.py pour Windows ou build_macos.py pour macOS")
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
        print("✅ Exécutable créé avec succès !")
        print()
        
        # Le fichier .spec utilise le mode --onedir par défaut
        if sys.platform == "darwin":  # macOS
            exe_path = Path("dist") / f"{app_name}.app"
            print(f"📦 Application macOS : {exe_path}")
        elif sys.platform == "win32":  # Windows
            exe_path = Path("dist") / f"{app_name}" / f"{app_name}.exe"
            print(f"📦 Exécutable Windows : {exe_path}")
        else:  # Linux
            exe_path = Path("dist") / app_name / app_name
            print(f"📦 Exécutable Linux : {exe_path}")
        
        print()
        print("📋 IMPORTANT :")
        print("   1. Distribuez TOUT le dossier créé dans dist/")
        print("   2. Dans ce dossier, placez également :")
        print("      - recoltes_fraises.xlsx")
        print("      - meteo_dataset.csv")
        print("      - model_fraises_v2.pkl (si disponible)")
        print("   3. Les dossiers 'forecasts' et 'models_archive' seront créés automatiquement")
        if frontend_built:
            print("   4. Le frontend React est inclus dans l'exécutable")
            print("   5. L'application démarre un serveur web local sur http://127.0.0.1:5000")
        else:
            print("   4. ⚠️  Le frontend React n'est PAS inclus (non compilé)")
            print("      L'application fonctionnera mais l'interface web ne sera pas disponible")
        print("   6. Testez l'exécutable avant de le distribuer")
        print()
        
        return True
        
    except subprocess.CalledProcessError as e:
        print()
        print("❌ Erreur lors de la construction de l'exécutable")
        print(f"   Code retour : {e.returncode}")
        return False
    except Exception as e:
        print()
        print(f"❌ Erreur inattendue : {e}")
        return False

if __name__ == "__main__":
    success = build_executable()
    sys.exit(0 if success else 1)

