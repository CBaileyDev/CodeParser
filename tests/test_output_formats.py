"""Tests for OutputFormat enum and its integration with CodeParserConfig."""

from __future__ import annotations

from pathlib import Path

from codeparser.output_format import OutputFormat
from codeparser.config import CodeParserConfig


class TestOutputFormatVariants:
    def test_output_format_has_four_variants(self) -> None:
        members = set(OutputFormat.__members__)
        assert members == {"XML", "MARKDOWN", "JSON", "TEXT"}

    def test_output_format_file_extensions(self) -> None:
        assert OutputFormat.XML.extension == ".xml"
        assert OutputFormat.MARKDOWN.extension == ".md"
        assert OutputFormat.JSON.extension == ".json"
        assert OutputFormat.TEXT.extension == ".txt"

    def test_output_format_display_names(self) -> None:
        assert OutputFormat.XML.display_name == "XML"
        assert OutputFormat.MARKDOWN.display_name == "Markdown"
        assert OutputFormat.JSON.display_name == "JSON"
        assert OutputFormat.TEXT.display_name == "Plain Text"


class TestConfigOutputFormat:
    def test_config_defaults_to_xml(self) -> None:
        config = CodeParserConfig(root_path=Path("."))
        assert config.output_format == OutputFormat.XML
