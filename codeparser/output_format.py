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
