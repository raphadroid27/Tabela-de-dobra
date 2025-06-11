a = Analysis(
    ['src\\app.py'],
    pathex=[],
    binaries=[],
    datas=[('assets\\icone.ico', 'assets'), ('src\\__init__.py', 'src')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Excluir dialetos SQLAlchemy não utilizados para reduzir tamanho
        'sqlalchemy.dialects.mysql',
        'sqlalchemy.dialects.postgresql', 
        'sqlalchemy.dialects.oracle',
        'sqlalchemy.dialects.mssql',
        'sqlalchemy.dialects.sybase',
        'sqlalchemy.dialects.firebird',
        # Excluir outros módulos desnecessários
        'pandas',
        'numpy',
        'matplotlib',
        'PIL',
        'selenium',
        'requests',
        'urllib3',
        'cryptography',
        'pytest',
        'setuptools',
        'distutils',
        # Excluir módulos de desenvolvimento/teste
        'unittest',
        'doctest',
        'pdb',
        'cProfile',
        'profile',
        'pstats',
        # Excluir suporte a outros GUIs
        'PyQt5',
        'PyQt6', 
        'PySide2',
        'PySide6',
        'wx',
        'kivy',
        # Excluir compiladores
        'compiler',
        'py_compile',
        'compileall'
    ],
    noarchive=False,
    optimize=2,  # Otimização máxima do bytecode Python
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='Cálculo de Dobra',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets\\icone.ico',
    version='version_info.txt', # Adicionando o arquivo de versão (gerado dinamicamente)
)