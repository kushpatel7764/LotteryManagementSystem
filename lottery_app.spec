# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\lottery_app\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('src/lottery_app/templates', 'lottery_app/templates'), ('src/lottery_app/static', 'lottery_app/static'), ('src/lottery_app/database', 'lottery_app/database'), ('src/lottery_app/*.json', 'lottery_app')],
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
    [],
    exclude_binaries=True,
    name='lottery_app',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='lottery_app',
)
