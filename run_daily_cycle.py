import subprocess
import argparse
import sys
import importlib.util
from datetime import datetime
from pathlib import Path

# Import de l'utilitaire PyInstaller
try:
    from pyinstaller_utils import is_pyinstaller, get_script_path
except ImportError:
    # Si le module n'est pas disponible, définir des fonctions de repli
    def is_pyinstaller():
        return False
    def get_script_path(script_name):
        return script_name

def run_script(script_name):
    """Exécute un script Python et affiche les logs en temps réel."""
    print(f"🚀 Exécution de {script_name} ...")
    
    # Dans un exécutable PyInstaller, importer directement le module
    if is_pyinstaller():
        try:
            script_path = get_script_path(script_name)
            if Path(script_path).exists():
                # Charger et exécuter le module directement
                spec = importlib.util.spec_from_file_location(
                    script_name.replace('.py', '').replace('-', '_'),
                    script_path
                )
                if spec and spec.loader:
                    module = importlib.util.module_from_spec(spec)
                    # Exécuter le module (cela exécutera tout le code au niveau du module)
                    spec.loader.exec_module(module)
                    print(f"✅ {script_name} terminé avec succès.\n")
                    return
        except Exception as e:
            import traceback
            print(f"⚠️  Erreur lors de l'import direct : {e}")
            print(traceback.format_exc())
            print("   Tentative avec subprocess...")
    
    # Méthode normale avec subprocess (pour le développement)
    try:
        script_path = get_script_path(script_name)
        result = subprocess.run(
            [sys.executable, script_path],
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        print(f"✅ {script_name} terminé avec succès.\n")
    except subprocess.CalledProcessError as e:
        print(f"❌ Erreur lors de l'exécution de {script_name}. Code retour : {e.returncode}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Pipeline quotidien de la Pépinière Valbray")
    parser.add_argument(
        "--mode",
        choices=["forecast", "update"],
        required=True,
        help="Mode à exécuter : 'forecast' pour les prévisions du matin, 'update' pour le réentraînement du soir"
    )
    args = parser.parse_args()

    print(f"\n🌾 === PÉPINIÈRE VALBRAY — LANCEMENT DU PIPELINE {args.mode.upper()} ===")
    print(f"🕓 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

    if args.mode == "forecast":
        run_script("forecast_next3days_v3.py")

    elif args.mode == "update":
        run_script("auto_update_model_v4.py")

    print("\n🌱 Fin du processus.\n")

if __name__ == "__main__":
    main()
