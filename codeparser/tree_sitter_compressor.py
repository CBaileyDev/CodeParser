from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

try:  # pragma: no cover - import guard
    from tree_sitter_languages import get_parser  # type: ignore

    HAS_TREE_SITTER = True
except Exception:  # pragma: no cover
    HAS_TREE_SITTER = False
    logger.info(
        "tree-sitter-languages not installed; structural compression will be disabled.",
    )


EXTENSION_LANGUAGE_MAP = {
    ".py": "python",
    ".js": "javascript",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".jsx": "javascript",
    ".java": "java",
    ".go": "go",
    ".rs": "rust",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
}


def _guess_language_from_extension(path: Path) -> Optional[str]:
    return EXTENSION_LANGUAGE_MAP.get(path.suffix.lower())


def is_advanced_compression_available() -> bool:
    return HAS_TREE_SITTER


def compress_source_with_tree_sitter(source: str, path: Path) -> str:
    """Best-effort structural compression using Tree-sitter.

    Keeps imports and top-level class / function definitions while dropping
    low-value implementation details. Falls back to the original source
    if Tree-sitter is unavailable or parsing fails.
    """

    if not HAS_TREE_SITTER:
        return source

    language = _guess_language_from_extension(path)
    if not language:
        return source

    try:
        parser = get_parser(language)
    except Exception:
        return source

    try:
        source_bytes = source.encode("utf-8", errors="ignore")
        tree = parser.parse(source_bytes)
    except Exception:
        return source

    root = tree.root_node
    important_chunks: list[str] = []

    for child in root.children:
        node_type = child.type
        if node_type in {
            "import_statement",
            "import_from_statement",
            "import_declaration",
            "class_definition",
            "function_definition",
            "method_definition",
        }:
            segment = source_bytes[child.start_byte : child.end_byte].decode(
                "utf-8", errors="ignore"
            )
            important_chunks.append(segment)

    if not important_chunks:
        return source

    compressed = "\n\n".join(important_chunks)

    # Only accept the compressed form if it is significantly smaller.
    if len(compressed) < 0.7 * len(source):
        return compressed

    return source
