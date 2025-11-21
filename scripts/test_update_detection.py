#!/usr/bin/env python3
"""
Script de test pour vérifier la détection des mises à jour.
Utilisez ce script pour déboguer les problèmes de détection de mises à jour.
"""
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from auto_updater import check_for_updates, get_current_version, get_user_data_dir
from pyinstaller_utils import get_base_path
import logging

# Configurer le logging pour voir tous les messages
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    print("=" * 60)
    print("Test de détection des mises à jour")
    print("=" * 60)
    
    # Afficher les informations de base
    base_path = get_base_path()
    print(f"\n📁 Chemin de base de l'application : {base_path}")
    
    # Afficher la version actuelle
    current_version = get_current_version()
    print(f"📌 Version actuelle : {current_version}")
    
    # Afficher l'emplacement du fichier de version
    import sys as sys_module
    if sys_module.platform == "darwin" and (base_path.suffix == ".app" or (base_path / "Contents").exists()):
        data_dir = get_user_data_dir(base_path)
        version_file = data_dir / "installed_version.txt"
    else:
        version_file = base_path / "installed_version.txt"
    
    print(f"📄 Fichier de version : {version_file}")
    if version_file.exists():
        print(f"   ✅ Existe : {version_file.read_text().strip()}")
    else:
        print(f"   ❌ N'existe pas")
    
    # Vérifier les mises à jour (sans prerelease)
    print("\n🔍 Vérification des mises à jour (releases stables uniquement)...")
    update_info_stable = check_for_updates(include_prerelease=False)
    
    if update_info_stable.get("available"):
        print(f"   ✅ Mise à jour disponible !")
        print(f"   📦 Version disponible : {update_info_stable.get('latest_version')}")
        print(f"   📌 Version actuelle : {update_info_stable.get('current_version')}")
        print(f"   🔗 URL : {update_info_stable.get('release_url')}")
    else:
        print(f"   ℹ️  Aucune mise à jour disponible (releases stables)")
        if 'latest_version' in update_info_stable:
            print(f"   📦 Dernière version : {update_info_stable.get('latest_version')}")
        if 'error' in update_info_stable:
            print(f"   ⚠️  Erreur : {update_info_stable.get('error')}")
    
    # Vérifier les mises à jour (avec prerelease)
    print("\n🔍 Vérification des mises à jour (incluant les prereleases)...")
    update_info_prerelease = check_for_updates(include_prerelease=True)
    
    if update_info_prerelease.get("available"):
        print(f"   ✅ Mise à jour disponible !")
        print(f"   📦 Version disponible : {update_info_prerelease.get('latest_version')}")
        print(f"   📌 Version actuelle : {update_info_prerelease.get('current_version')}")
        print(f"   🔗 URL : {update_info_prerelease.get('release_url')}")
        if update_info_prerelease.get('prerelease'):
            print(f"   ⚠️  C'est une prerelease (build automatique)")
    else:
        print(f"   ℹ️  Aucune mise à jour disponible (incluant prereleases)")
        if 'latest_version' in update_info_prerelease:
            print(f"   📦 Dernière version : {update_info_prerelease.get('latest_version')}")
        if 'error' in update_info_prerelease:
            print(f"   ⚠️  Erreur : {update_info_prerelease.get('error')}")
    
    print("\n" + "=" * 60)
    print("Test terminé")
    print("=" * 60)

if __name__ == "__main__":
    main()

