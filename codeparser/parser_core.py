from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from tqdm import tqdm

from .config import CodeParserConfig
from .ignore_rules import build_ignore_spec, iter_included_files, is_binary_file
from .secret_scanner import scan_path_for_secrets
from .token_counter import count_tokens
from .tree_sitter_compressor import compress_source_with_tree_sitter
from .xml_builder import build_repomix_xml


@dataclass
class GenerationStats:
    total_files: int = 0
    total_tokens: Optional[int] = None
    secrets_found: int = 0


def _should_skip_file(path: Path, config: CodeParserConfig) -> bool:
    try:
        if path.stat().st_size > config.max_file_size_bytes:
            return True
    except OSError:
        return True
    if is_binary_file(path):
        return True
    return False


def _strip_line_comments(text: str, suffix: str) -> str:
    """Lightweight comment stripping.

    Only removes full-line comments using language-specific prefixes.
    We intentionally avoid complex parsing and block comments to keep
    this fast and robust.
    """

    lines = []
    if suffix in {".py", ".sh", ".bash"}:
        comment_prefixes = ("#",)
    elif suffix in {".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".cpp", ".go"}:
        comment_prefixes = ("//",)
    else:
        comment_prefixes = tuple()

    for line in text.splitlines():
        stripped = line.lstrip()
        if comment_prefixes and stripped.startswith(comment_prefixes):
            continue
        lines.append(line)
    return "\n".join(lines)


def _collect_git_logs(root: Path, max_commits: int = 20) -> list[dict]:
    try:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(root),
                "log",
                f"-n{max_commits}",
                "--date=iso",
                "--pretty=format:%ad%x1f%s%x1e",
                "--name-only",
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return []

    commits: list[dict] = []
    for record in result.stdout.split("\x1e"):
        record = record.strip()
        if not record:
            continue
        header, *lines = record.splitlines()
        try:
            date, message = header.split("\x1f", 1)
        except ValueError:
            date, message = header, ""
        changed_files = [line.strip() for line in lines if line.strip()]
        commits.append(
            {
                "date": date,
                "message": message,
                "files": changed_files,
            }
        )
    return commits


def generate_xml(
    config: CodeParserConfig,
    use_tqdm: bool = False,
    preview: bool = False,
) -> tuple[str, GenerationStats]:
    """Generate a Repomix-style XML document for the configured root.

    When ``preview`` (or ``config.preview_mode``) is True, only a subset
    of files is processed to keep the operation fast for live previews
    in the GUI.
    """

    ignore_spec = build_ignore_spec(config.root_path)
    stats = GenerationStats()
    processed_files: list[dict] = []

    # Limit the work done during preview mode to keep the GUI responsive.
    max_files = 40 if preview or config.preview_mode else None

    all_files = list(iter_included_files(config.root_path, ignore_spec))
    if max_files is not None:
        all_files = all_files[: max_files]

    iterator = all_files
    progress_iter = (
        tqdm(iterator, desc="Packing files", unit="file")
        if use_tqdm
        else iterator
    )

    total_tokens: Optional[int] = 0 if config.count_tokens else None
    total_secrets = 0

    for path, rel_path in progress_iter:
        if _should_skip_file(path, config):
            continue

        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue

        if config.remove_comments:
            text = _strip_line_comments(text, path.suffix)

        if config.compress:
            text = compress_source_with_tree_sitter(text, path)

        file_tokens = count_tokens(text, config.model_name) if config.count_tokens else None
        if file_tokens is not None and total_tokens is not None:
            total_tokens += file_tokens

        secret_count = scan_path_for_secrets(path) if config.secret_scan else 0
        total_secrets += secret_count

        processed_files.append(
            {
                "path": rel_path,
                "content": text,
                "lines": text.count("\n") + 1 if text else 0,
                "tokens": file_tokens,
                "secrets": secret_count,
            }
        )

    stats.total_files = len(processed_files)
    stats.total_tokens = total_tokens
    stats.secrets_found = total_secrets

    # Build a simple directory tree representation.
    directory_tree_lines: list[str] = [config.root_path.name]
    for rel_path in sorted({f["path"] for f in processed_files}):
        depth = rel_path.count("/")
        indent = "  " * depth
        name = Path(rel_path).name
        directory_tree_lines.append(f"{indent}{name}")

    directory_tree = "\n".join(directory_tree_lines)

    git_log_commits = (
        _collect_git_logs(config.root_path) if config.include_git_history else []
    )

    xml_text = build_repomix_xml(
        processed_files=processed_files,
        directory_tree=directory_tree,
        stats=stats,
        include_git_logs=config.include_git_history,
        git_log_commits=git_log_commits,
    )

    return xml_text, stats
