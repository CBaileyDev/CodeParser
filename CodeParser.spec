# CodeParser.spec
# PyInstaller spec for building a single-file executable that supports
# both GUI mode and CLI mode. The application hides the console window
# itself when launching the GUI.

import pathlib
from importlib.util import find_spec

from PyInstaller.utils.hooks import collect_submodules

block_cipher = None

hiddenimports = [
    "tiktoken",
    "detect_secrets",
    "detect_secrets.core.scan",
] + collect_submodules("detect_secrets")

if find_spec("tiktoken_ext") is not None:
    hiddenimports += collect_submodules("tiktoken_ext")

if find_spec("tree_sitter") is not None:
    hiddenimports.append("tree_sitter")

if find_spec("tree_sitter_languages") is not None:
    hiddenimports.append("tree_sitter_languages")

icon_path = pathlib.Path("assets") / "codeparser.ico"


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
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(icon_path) if icon_path.exists() else None,
)
