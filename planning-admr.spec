# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build for Planning ADMR. Works on macOS and Windows."""
import os
import sys

from PyInstaller.utils.hooks import copy_metadata

APP_NAME = "Planning ADMR"
APP_VERSION = "1.0.0"

if sys.platform == "darwin":
    ICON = "assets/icon.icns"
elif sys.platform == "win32":
    ICON = "assets/icon.ico"
else:
    ICON = None

a = Analysis(
    ["admr.py"],
    pathex=[],
    binaries=[],
    datas=copy_metadata("keyring"),
    hiddenimports=[
        "keyring.backends.macOS",
        "keyring.backends.Windows",
        "keyring.backends.SecretService",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["weasyprint"],
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
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
    name=APP_NAME,
)
app = BUNDLE(
    coll,
    name=f"{APP_NAME}.app",
    icon=ICON,
    bundle_identifier="fr.planningadmr.app",
    info_plist={
        "CFBundleShortVersionString": APP_VERSION,
        "CFBundleVersion": APP_VERSION,
        "NSHighResolutionCapable": True,
        "NSHumanReadableCopyright": "MIT License - Planning ADMR contributors",
    },
)
