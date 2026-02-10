# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller specification file for LabelGen

Build with: pyinstaller labelgen.spec
"""

import os
from pathlib import Path

block_cipher = None

# Base directory
base_dir = Path(SPECPATH)

# Collect Django files
django_datas = []

# Add inventory app files (only if they exist)
inventory_dir = base_dir / 'inventory'
templates_dir = inventory_dir / 'templates'
static_dir = inventory_dir / 'static'
migrations_dir = inventory_dir / 'migrations'

if templates_dir.exists():
    django_datas.append((str(templates_dir), 'inventory/templates'))
if static_dir.exists():
    django_datas.append((str(static_dir), 'inventory/static'))
if migrations_dir.exists():
    django_datas.append((str(migrations_dir), 'inventory/migrations'))

# Add labelgen settings
labelgen_dir = base_dir / 'labelgen'
django_datas.append((str(labelgen_dir), 'labelgen'))

# Add database (if exists)
db_path = base_dir / 'db.sqlite3'
if db_path.exists():
    django_datas.append((str(db_path), '.'))

# Hidden imports needed by Django
hidden_imports = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.template.loaders.filesystem',
    'django.template.loaders.app_directories',
    'inventory',
    'inventory.models',
    'inventory.views',
    'inventory.urls',
    'inventory.forms',
    'inventory.services',
    'labelgen.settings',
    'labelgen.urls',
    'pystray._win32',
]

a = Analysis(
    ['tray_app.py'],
    pathex=[str(base_dir)],
    binaries=[],
    datas=django_datas,
    hiddenimports=hidden_imports,
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

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='LabelGen',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # No console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon='icon.ico' if you have one
)
