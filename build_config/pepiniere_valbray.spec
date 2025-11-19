# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de configuration PyInstaller pour l'application Pépinière Valbray.
Utilisez ce fichier pour personnaliser la construction de l'exécutable.

IMPORTANT: Avant de générer l'exécutable, compilez le frontend React:
    cd frontend
    npm run build
"""

import os
from pathlib import Path

block_cipher = None

# Vérifier que le frontend est compilé
# Les chemins sont relatifs à la racine du projet (où PyInstaller est exécuté)
base_dir = Path(__file__).parent.parent
frontend_build = base_dir / 'frontend' / 'build'
if not frontend_build.exists() or not (frontend_build / 'index.html').exists():
    print("[WARNING] ATTENTION: Le frontend React n'est pas compile!")
    print("   Veuillez executer: cd frontend && npm run build")
    print("   Poursuite de la generation sans le frontend...")

# Scripts Python à inclure (chemins relatifs à la racine du projet)
scripts = [
    str(base_dir / 'app.py'),  # Point d'entrée principal (serveur Flask)
    str(base_dir / 'scripts' / 'run_daily_cycle.py'),
    str(base_dir / 'scripts' / 'forecast_next3days_v3.py'),
    str(base_dir / 'scripts' / 'auto_update_model_v4.py'),
    str(base_dir / 'scripts' / 'train_model.py'),
]

# Fichiers de données à inclure (chemins relatifs à la racine du projet)
datas = [
    # Fichiers de données essentiels (depuis data/)
    (str(base_dir / 'data' / 'recoltes_fraises.xlsx'), '.'),
    (str(base_dir / 'data' / 'meteo_dataset.csv'), '.'),
    (str(base_dir / 'assets' / 'splash.png'), 'assets'),
    # Scripts Python appelés dynamiquement (depuis scripts/)
    (str(base_dir / 'scripts' / 'run_daily_cycle.py'), '.'),
    (str(base_dir / 'scripts' / 'forecast_next3days_v3.py'), '.'),
    (str(base_dir / 'scripts' / 'auto_update_model_v4.py'), '.'),
    (str(base_dir / 'scripts' / 'train_model.py'), '.'),
    (str(base_dir / 'scripts' / 'update_meteo_dataset.py'), '.'),
    # Modules Python nécessaires
    (str(base_dir / 'database.py'), '.'),
    (str(base_dir / 'data_loader.py'), '.'),
    (str(base_dir / 'logger_config.py'), '.'),
    (str(base_dir / 'validators.py'), '.'),
    (str(base_dir / 'pyinstaller_utils.py'), '.'),
    (str(base_dir / 'system_tray.py'), '.'),
]

# Ajouter les fichiers optionnels s'ils existent
optional_files = [
    # Base de données SQLite (créée au runtime si absente)
    (base_dir / 'recoltes.db', '.'),
    # Modèle ML (peut être généré au runtime) - depuis models/
    (base_dir / 'models' / 'model_fraises_v2.pkl', '.'),
    # Modules optionnels
    (base_dir / 'cache_utils.py', '.'),
    (base_dir / 'config.py', '.'),
]

for file_path, dest in optional_files:
    if file_path.exists():
        datas.append((str(file_path), dest))
        print(f"[OK] Fichier optionnel inclus : {file_path.name}")
    else:
        print(f"[WARNING] Fichier optionnel non trouve (sera cree au runtime si necessaire) : {file_path.name}")

# Inclure le frontend React compilé si disponible
if frontend_build.exists() and (frontend_build / 'index.html').exists():
    # Inclure tous les fichiers du dossier build
    frontend_files = []
    for root, dirs, files in os.walk(frontend_build):
        for file in files:
            src_path = Path(root) / file
            # Chemin relatif depuis frontend/build
            rel_path = src_path.relative_to(frontend_build)
            # Destination dans l'exécutable: frontend/build/...
            dest_path = 'frontend/build' / rel_path.parent
            frontend_files.append((str(src_path), str(dest_path)))
    datas.extend(frontend_files)
    print(f"[OK] Frontend React inclus ({len(frontend_files)} fichiers)")
else:
    print("[WARNING] Frontend React non inclus (non compile)")

# Modules cachés nécessaires
hiddenimports = [
    'pandas',
    'numpy',
    'sklearn',
    'sklearn.ensemble',
    'sklearn.tree',
    'sklearn.model_selection',
    'sklearn.metrics',
    'joblib',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'requests',
    'flask',
    'flask_cors',
    'werkzeug',
    'werkzeug.serving',
    'werkzeug.utils',
    # Modules de l'application
    'database',
    'data_loader',
    'logger_config',
    'validators',
    'pyinstaller_utils',
    'system_tray',
    'cache_utils',  # Optionnel
    'config',  # Optionnel
    # Utilitaires Python
    'importlib.util',  # Pour l'import dynamique
    'sqlite3',  # Pour la base de données SQLite
    # Icône système
    'pystray',
    'PIL',
    'PIL.Image',
    'PIL.ImageDraw',
]

a = Analysis(
    [str(base_dir / 'app.py')],  # Point d'entrée: serveur Flask avec interface web
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# Mode --onedir (recommandé, plus rapide et plus fiable)
# Pour utiliser --onefile, décommentez la section EXE ci-dessous et commentez COLLECT
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Mode --onedir
    name='PepiniereValbray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,  # Désactivé pour éviter les problèmes avec lipo
    console=False,  # Mode fenêtré pour masquer la console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Vous pouvez ajouter un fichier .ico ici pour Windows ou .icns pour macOS
    splash=str(base_dir / 'assets' / 'splash.png'),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,  # Désactivé pour éviter les problèmes avec lipo
    upx_exclude=[],
    name='PepiniereValbray',
)

app = BUNDLE(
    coll,
    name='PepiniereValbray.app',
    icon=None,
    bundle_identifier='com.pepiniere.valbray',
)

# Pour utiliser --onefile, décommentez ceci et commentez la section COLLECT ci-dessus
# exe = EXE(
#     pyz,
#     a.scripts,
#     a.binaries,
#     a.zipfiles,
#     a.datas,
#     [],
#     name='PepiniereValbray',
#     debug=False,
#     bootloader_ignore_signals=False,
#     strip=False,
#     upx=True,
#     upx_exclude=[],
#     runtime_tmpdir=None,
#     console=False,
#     disable_windowed_traceback=False,
#     argv_emulation=False,
#     target_arch=None,
#     codesign_identity=None,
#     entitlements_file=None,
#     icon=None,
# )

