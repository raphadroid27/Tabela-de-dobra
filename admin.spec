# -*- mode: python ; coding: utf-8 -*-


a = Analysis(
    ['src\\admin.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets\\icone_2.ico', 'assets'),
        ('src\\__init__.py', 'src'),
        ('src\\forms\\common\\help_content', 'forms/common/help_content'),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=1,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='admin',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['assets\\icone_2.ico'],
)
