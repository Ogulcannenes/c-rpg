# -*- mode: python ; coding: utf-8 -*-
# PyInstaller build for the Windows desktop app (build-windows.bat runs this).
# Phase 11: UPX is off (packed executables trigger antivirus false positives and gain little),
# and the exe carries a version resource read from server.APP_VERSION.
import re
from pathlib import Path

from PyInstaller.utils.win32.versioninfo import (FixedFileInfo, StringFileInfo, StringStruct, StringTable,
                                                 VarFileInfo, VarStruct, VSVersionInfo)

ROOT = Path(SPECPATH)
APP_VERSION = re.search(r'^APP_VERSION = "(\d+)\.(\d+)\.(\d+)"', (ROOT / "server.py").read_text(encoding="utf-8"), re.M)
VERSION = tuple(int(part) for part in APP_VERSION.groups()) + (0,)
VERSION_TEXT = ".".join(str(part) for part in VERSION[:3])

version_info = VSVersionInfo(
    ffi=FixedFileInfo(filevers=VERSION, prodvers=VERSION, mask=0x3F, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
    kids=[
        StringFileInfo([StringTable("041F04B0", [
            StringStruct("CompanyName", "C++ Adventure"),
            StringStruct("FileDescription", "C++ Adventure - C++ öğrenme macerası"),
            StringStruct("FileVersion", VERSION_TEXT),
            StringStruct("InternalName", "CppAdventure"),
            StringStruct("OriginalFilename", "CppAdventure.exe"),
            StringStruct("ProductName", "C++ Adventure"),
            StringStruct("ProductVersion", VERSION_TEXT),
        ])]),
        VarFileInfo([VarStruct("Translation", [0x041F, 1200])]),
    ],
)

a = Analysis(
    ['desktop.py'],
    pathex=[],
    binaries=[],
    datas=[('web', 'web'), ('plugins', 'plugins')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest', 'pydoc'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='CppAdventure',
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
    version=version_info,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='CppAdventure',
)
