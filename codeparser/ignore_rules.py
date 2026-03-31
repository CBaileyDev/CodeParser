from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Optional

from pathspec import PathSpec

# Built-in patterns for directories and files that should not be
# included in the packed XML.
BUILTIN_IGNORE_PATTERNS = [
    ".git/",
    ".hg/",
    ".svn/",
    ".DS_Store",
    "node_modules/",
    "dist/",
    "build/",
    ".venv/",
    "venv/",
    "ENV/",
    "__pycache__",
    "__pycache__/*",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "*.so",
    "*.dylib",
    "*.dll",
    "*.exe",
    "*.obj",
    "*.class",
    "*.jar",
    "*.zip",
    "*.tar",
    "*.tar.gz",
    "*.tgz",
    "*.7z",
    "*.iso",
    "*.png",
    "*.jpg",
    "*.jpeg",
    "*.gif",
    "*.bmp",
    "*.ico",
    "*.mp3",
    "*.mp4",
    "*.avi",
    "*.mov",
    "*.pdf",
    "*.doc",
    "*.docx",
    "*.xls",
    "*.xlsx",
    "*.ppt",
    "*.pptx",
    "*.log",
]


def _load_patterns_from_file(path: Path) -> Iterable[str]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return [
        line.strip()
        for line in lines
        if line.strip() and not line.strip().startswith("#")
    ]


def build_ignore_spec(root: Path) -> Optional[PathSpec]:
    patterns = list(BUILTIN_IGNORE_PATTERNS)
    patterns.extend(_load_patterns_from_file(root / ".gitignore"))
    patterns.extend(_load_patterns_from_file(root / ".codeparserignore"))
    if not patterns:
        return None
    return PathSpec.from_lines("gitignore", patterns)


def is_binary_file(path: Path, sample_size: int = 1024) -> bool:
    try:
        with path.open("rb") as f:
            chunk = f.read(sample_size)
        if not chunk:
            return False
        # Heuristic: if there are null bytes, treat as binary.
        return b"\x00" in chunk
    except OSError:
        return True


def iter_included_files(root: Path, ignore_spec: Optional[PathSpec]):
    """Yield (absolute_path, relative_path) pairs for included files.

    Directories and files that match the ignore spec are skipped.
    """

    root = root.resolve()
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root)
        if rel_dir == ".":
            rel_dir = ""

        # Filter directories in-place so os.walk does not descend into them.
        for d in list(dirnames):
            rel_path = os.path.join(rel_dir, d) if rel_dir else d
            if ignore_spec and ignore_spec.match_file(rel_path):
                dirnames.remove(d)

        for filename in filenames:
            rel_path = os.path.join(rel_dir, filename) if rel_dir else filename
            if ignore_spec and ignore_spec.match_file(rel_path):
                continue
            full_path = Path(dirpath) / filename
            yield full_path, rel_path.replace("\\", "/")
