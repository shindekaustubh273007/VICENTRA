# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for VICENTRA / IBVAP.
Builds a standalone one-directory distribution with bundled static assets and YOLO model.
"""

from pathlib import Path
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect Ultralytics and dependencies
datas = [
    ('static', 'static'),
    ('media', 'media'),
    ('yolov8n.pt', '.'),
]

# Collect any package data files needed by ultralytics
try:
    datas += collect_data_files('ultralytics')
except Exception:
    pass

hiddenimports = [
    # Uvicorn internals
    'uvicorn',
    'uvicorn.logging',
    'uvicorn.loops',
    'uvicorn.loops.auto',
    'uvicorn.loops.asyncio',
    'uvicorn.protocols',
    'uvicorn.protocols.http',
    'uvicorn.protocols.http.auto',
    'uvicorn.protocols.http.h11_impl',
    'uvicorn.protocols.websockets',
    'uvicorn.protocols.websockets.auto',
    'uvicorn.protocols.websockets.wsproto_impl',
    'uvicorn.lifespan',
    'uvicorn.lifespan.on',
    
    # FastAPI & Starlette
    'fastapi',
    'starlette',
    'starlette.routing',
    'starlette.middleware',
    'starlette.responses',
    'starlette.staticfiles',
    'starlette.websockets',
    
    # Pydantic & SQLAlchemy
    'pydantic',
    'pydantic_settings',
    'sqlalchemy',
    'sqlalchemy.dialects.sqlite',
    
    # Computer Vision & Deep Learning
    'cv2',
    'torch',
    'ultralytics',
    'numpy',
    'psutil',
    
    # Internal project modules
    'app',
    'app.main',
    'app.bootstrap',
    'app.core.config',
    'app.core.logging',
    'app.core.paths',
    'app.services.stream_manager',
    'app.services.inference_manager',
    'app.services.tracking_manager',
    'app.services.zone_manager',
    'app.services.event_dispatcher',
    'app.services.ws_manager',
    'app.services.event_store',
    'app.api.cameras',
    'app.api.zones',
    'app.api.events',
    'app.api.ws',
    'app.api.health',
    'app.api.tracking',
    'app.api.detections',
]

a = Analysis(
    ['launcher.py'],
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
        'pytest',
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
    name='VICENTRA',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
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
    upx=False,
    upx_exclude=[],
    name='VICENTRA',
)
