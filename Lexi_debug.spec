# -*- mode: python ; coding: utf-8 -*-
# Debug spec — console ON, upx OFF, outputs Lexi_debug.exe
# Entry: debug_launcher.py wraps gui with click logging + call tracing + exception hooks

a = Analysis(
    ['debug_launcher.py'],
    pathex=[],
    binaries=[],
    datas=[('data/categories_full.json', 'data'), ('data/stopwords.txt', 'data')],
    hiddenimports=['nltk', 'lemminflect', 'wordfreq', 'flet', 'openai', 'genanki'],
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
    name='Lexi_debug',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
