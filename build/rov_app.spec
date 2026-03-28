# -*- mode: python ; coding: utf-8 -*-
# PyInstaller spec file for ROV Underwater Analyzer v5

import os
import sys

block_cipher = None
app_root = os.path.dirname(os.path.abspath(SPECPATH if 'SPECPATH' in dir() else __file__))

a = Analysis(
    [os.path.join(app_root, 'main.py')],
    pathex=[app_root],
    binaries=[],
    datas=[
        (os.path.join(app_root, 'config.default.json'), '.'),
        (os.path.join(app_root, 'rov_app', 'resources'), 'rov_app/resources'),
    ],
    hiddenimports=[
        # PySide6
        'PySide6.QtWidgets',
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtSvg',
        'PySide6.QtNetwork',
        # OpenCV
        'cv2',
        'numpy',
        'numpy.core._methods',
        'numpy.lib.format',
        # PDF
        'fpdf',
        'fpdf.enums',
        'fpdf.fonts',
        # HTTP
        'requests',
        'urllib3',
        'certifi',
        'charset_normalizer',
        'idna',
        # App modules
        'rov_app',
        'rov_app.core',
        'rov_app.core.config',
        'rov_app.core.constants',
        'rov_app.core.frame_extractor',
        'rov_app.core.opencv_analyzer',
        'rov_app.core.deduplicator',
        'rov_app.core.telemetry',
        'rov_app.core.pdf_generator',
        'rov_app.core.annotations',
        'rov_app.core.job',
        'rov_app.ai',
        'rov_app.ai.base_provider',
        'rov_app.ai.openrouter_provider',
        'rov_app.ai.openai_provider',
        'rov_app.ai.anthropic_provider',
        'rov_app.ai.prompt',
        'rov_app.workers.extraction_worker',
        'rov_app.workers.analysis_worker',
        'rov_app.workers.pdf_worker',
        'rov_app.ui.main_window',
        'rov_app.ui.settings_dialog',
        'rov_app.ui.frame_grid_widget',
        'rov_app.ui.frame_detail_dialog',
        'rov_app.ui.styles',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'tkinter',
        'matplotlib',
        'scipy',
        'pandas',
        'IPython',
        'jupyter',
        'notebook',
        'pytest',
        'setuptools',
        'wheel',
        'pip',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='ROV_Analyzer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,   # No black console window
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=os.path.join(app_root, 'rov_app', 'resources', 'app.ico')
         if os.path.exists(os.path.join(app_root, 'rov_app', 'resources', 'app.ico'))
         else None,
    version_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=['vcruntime140.dll', 'python3*.dll'],
    name='ROV_Analyzer',
)
