# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build definition for vColor.

The onedir build is intentional: it starts substantially faster than a
one-file executable because nothing has to be unpacked into a temp folder.
"""

from pathlib import Path
import sys

ROOT = Path(SPECPATH).resolve().parent
RESOURCES = ROOT / "vcolor" / "resources"

if sys.platform == "win32":
    ICON = str(RESOURCES / "icon.ico")
elif sys.platform == "darwin":
    ICON = str(RESOURCES / "icon.icns")
else:
    ICON = None

a = Analysis(
    [str(ROOT / "run.py")],
    pathex=[str(ROOT)],
    binaries=[],
    datas=[(str(RESOURCES), "vcolor/resources")],
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
    [],
    exclude_binaries=True,
    name="vColor",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=ICON,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="vColor",
)

if sys.platform == "darwin":
    app = BUNDLE(
        coll,
        name="vColor.app",
        icon=ICON,
        bundle_identifier="app.vcolor.desktop",
        info_plist={
            "CFBundleName": "vColor",
            "CFBundleDisplayName": "vColor",
            "CFBundleShortVersionString": "1.1.0",
            "CFBundleVersion": "1.1.0",
            "NSHighResolutionCapable": True,
            "LSMinimumSystemVersion": "11.0",
        },
    )
