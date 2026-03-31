"""OutputFormat enum for CodeParser output targets."""

from __future__ import annotations

from enum import Enum


class OutputFormat(Enum):
    """Supported output formats for parsed repository content."""

    XML = (".xml", "XML")
    MARKDOWN = (".md", "Markdown")
    JSON = (".json", "JSON")
    TEXT = (".txt", "Plain Text")

    def __init__(self, extension: str, display_name: str) -> None:
        self._extension = extension
        self._display_name = display_name

    @property
    def extension(self) -> str:
        """File extension including the leading dot (e.g. '.xml')."""
        return self._extension

    @property
    def display_name(self) -> str:
        """Human-readable name for display in the UI."""
        return self._display_name


def build_output(
    fmt: OutputFormat,
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    kwargs = dict(
        processed_files=processed_files,
        directory_tree=directory_tree,
        stats=stats,
        repository_name=repository_name,
        include_git_logs=include_git_logs,
        git_log_commits=git_log_commits,
    )
    if fmt == OutputFormat.XML:
        from .xml_builder import build_repomix_xml
        return build_repomix_xml(**kwargs)
    if fmt == OutputFormat.MARKDOWN:
        from .markdown_builder import build_markdown
        return build_markdown(**kwargs)
    if fmt == OutputFormat.JSON:
        from .json_builder import build_json
        return build_json(**kwargs)
    if fmt == OutputFormat.TEXT:
        from .text_builder import build_text
        return build_text(**kwargs)
    raise ValueError(f"Unsupported output format: {fmt}")
