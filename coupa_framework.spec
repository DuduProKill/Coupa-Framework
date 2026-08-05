# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec para Coupa Framework - Automação de Suprimentos

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

datas = []
datas += collect_data_files('fitz')         # PyMuPDF
datas += collect_data_files('PIL')
datas += collect_data_files('numpy')
datas += collect_data_files('pandas')
datas += collect_data_files('openpyxl')
datas += collect_data_files('docx')
datas += collect_data_files('pptx')
datas += collect_data_files('cryptography')
datas += collect_data_files('keyring')

# Inclui arquivos do projeto
datas += [
    ('modules', 'modules'),
]

hiddenimports = []
hiddenimports += collect_submodules('PyQt6')
hiddenimports += collect_submodules('cryptography')
hiddenimports += collect_submodules('keyring')
hiddenimports += collect_submodules('PIL')
hiddenimports += collect_submodules('numpy')
hiddenimports += [
    'requests',
    'numpy',
    'pandas',
    'openpyxl',
    'openpyxl.styles',
    'openpyxl.utils',
    'docx',
    'pptx',
    'fitz',
    'filelock',
    'win32com',
    'win32com.client',
    'pythoncom',
    'pywintypes',
    'pypdf',
    'asyncio',
    'playwright',
    'playwright.async_api',
    'playwright.sync_api',
    'email.mime.multipart',
    'email.mime.text',
    'email.mime.base',
    'email.encoders',
    'logging.handlers',
    'logging.config',
]

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'IPython',
        'jupyter',
        'notebook',
        'wx',
        'gi',
        'gtk',
        'test',
        'unittest',
        'xmlrpc',
        'ftplib',
        'imaplib',
        'poplib',
        'telnetlib',
        'turtle',
        'curses',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CoupaFramework',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    icon='assets/icon.ico',
    # UPX pode corromper DLLs do Qt e do Playwright — excluir explicitamente
    upx_exclude=[
        'Qt6*.dll',
        'PyQt6*.dll',
        '*.pyd',
        'node.exe',          # driver do Playwright
        'msedge*.dll',
    ],
    console=False,            # Sem janela de console
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[
        'Qt6*.dll',
        'PyQt6*.dll',
        '*.pyd',
        'node.exe',
        'msedge*.dll',
    ],
    name='CoupaFramework',
)