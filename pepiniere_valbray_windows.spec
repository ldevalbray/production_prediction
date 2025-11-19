# -*- mode: python ; coding: utf-8 -*-
"""
Fichier de configuration PyInstaller pour Windows - Application Pépinière Valbray.
Utilisez ce fichier pour construire l'exécutable Windows.

IMPORTANT: Avant de générer l'exécutable, compilez le frontend React:
    cd frontend
    npm run build
"""

import os
import sys
from pathlib import Path

block_cipher = None

# Vérifier que le frontend est compilé
frontend_build = Path('frontend/build')
if not frontend_build.exists() or not (frontend_build / 'index.html').exists():
    print("⚠️  ATTENTION: Le frontend React n'est pas compilé!")
    print("   Veuillez exécuter: cd frontend && npm run build")
    print("   Poursuite de la génération sans le frontend...")

# Scripts Python à inclure
scripts = [
    'app.py',  # Point d'entrée principal (serveur Flask)
    'run_daily_cycle.py',
    'forecast_next3days_v3.py',
    'auto_update_model_v4.py',
    'train_model.py',
]

# Fichiers de données à inclure
datas = [
    # Fichiers de données essentiels
    ('recoltes_fraises.xlsx', '.'),
    ('meteo_dataset.csv', '.'),
    ('assets/splash.png', 'assets'),
    # Scripts Python appelés dynamiquement
    ('run_daily_cycle.py', '.'),
    ('forecast_next3days_v3.py', '.'),
    ('auto_update_model_v4.py', '.'),
    ('train_model.py', '.'),
    ('update_meteo_dataset.py', '.'),
    # Modules Python nécessaires
    ('database.py', '.'),
    ('data_loader.py', '.'),
    ('logger_config.py', '.'),
    ('validators.py', '.'),
    ('pyinstaller_utils.py', '.'),
    ('system_tray.py', '.'),
]

# Ajouter les fichiers optionnels s'ils existent
optional_files = [
    # Base de données SQLite (créée au runtime si absente)
    ('recoltes.db', '.'),
    # Modèle ML (peut être généré au runtime)
    ('model_fraises_v2.pkl', '.'),
    # Modules optionnels
    ('cache_utils.py', '.'),
    ('config.py', '.'),
]

for file_path, dest in optional_files:
    if Path(file_path).exists():
        datas.append((file_path, dest))
        print(f"✅ Fichier optionnel inclus : {file_path}")
    else:
        print(f"⚠️  Fichier optionnel non trouvé (sera créé au runtime si nécessaire) : {file_path}")

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
    print(f"✅ Frontend React inclus ({len(frontend_files)} fichiers)")
else:
    print("⚠️  Frontend React non inclus (non compilé)")

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
    ['app.py'],  # Point d'entrée: serveur Flask avec interface web
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

# Mode --onedir pour Windows (recommandé)
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,  # Mode --onedir
    name='PepiniereValbray',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,  # Mode fenêtré pour masquer la console
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Ajoutez un fichier .ico ici si vous en avez un
    splash='assets/splash.png',
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='PepiniereValbray',
)

