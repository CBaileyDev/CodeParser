# CodeParser.spec
# PyInstaller spec for building a single-file, windowed executable.

import pathlib

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = [
    "tiktoken",
    "detect_secrets",
    "detect_secrets.core.scan",
    "tree_sitter",
    "tree_sitter_languages",
] + collect_submodules("detect_secrets")


a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=hiddenimports,
    hookspath=["hooks"],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name="CodeParser",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # windowed mode; CLI still works with arguments
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(pathlib.Path("assets") / "codeparser.ico"),
)
