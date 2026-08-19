# -*- mode: python ; coding: utf-8 -*-

import os
import sys


PROJECT_ROOT = os.path.abspath(".")

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)


from version import APP_VERSION_SHORT


a = Analysis(
    ['main.py'],
    pathex=[PROJECT_ROOT],
    binaries=[
        (
            '.venv/Lib/site-packages/discord/bin/libopus-0.x64.dll',
            'discord/bin'
        )
    ],
    datas=[
        ('assets/zelvik.ico', 'assets'),
        ('assets/discord_setup', 'assets/discord_setup'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name=f'Zelvik{APP_VERSION_SHORT}Debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets/zelvik.ico'],
)