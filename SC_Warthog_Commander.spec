# -*- mode: python ; coding: utf-8 -*-
import os

block_cipher = None

project_root = os.path.abspath(SPECPATH)
pkg_dir = os.path.join(project_root, "sc_warthog_commander")
web_dir = os.path.join(pkg_dir, "web")
icon_path = os.path.join(web_dir, "app_icon.ico")

# Collect web assets cleanly (skip backup files)
web_datas = []
for fname in os.listdir(web_dir):
    if fname.endswith(".bak") or fname.startswith("."):
        continue
    fpath = os.path.join(web_dir, fname)
    if os.path.isfile(fpath):
        web_datas.append((fpath, "web"))

hidden_imports = [
    "uvicorn.logging",
    "uvicorn.loops",
    "uvicorn.loops.auto",
    "uvicorn.loops.asyncio",
    "uvicorn.protocols",
    "uvicorn.protocols.http",
    "uvicorn.protocols.http.auto",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.protocols.websockets",
    "uvicorn.protocols.websockets.auto",
    "uvicorn.protocols.websockets.websockets_impl",
    "uvicorn.lifespan",
    "uvicorn.lifespan.on",
    "uvicorn.lifespan.off",
    "websockets",
    "websockets.legacy",
    "websockets.legacy.server",
    "anyio._backends._asyncio",
    "win32api",
    "win32con",
    "win32gui",
    "win32timezone",
    "psutil",
    "PIL",
    "PIL.Image",
    "PIL.ImageDraw",
    "PIL.ImageFilter",
    "PIL.ImageFont",
    "numpy",
]

a = Analysis(
    [os.path.join(pkg_dir, "main.py")],
    pathex=[pkg_dir],
    binaries=[],
    datas=web_datas,
    hiddenimports=hidden_imports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["pytest", "IPython", "matplotlib", "scipy", "pandas", "PyQt5", "PyQt6", "PySide6"],
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
    name="SC_Warthog_Commander",
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
    uac_admin=True,
    icon=icon_path,
)
