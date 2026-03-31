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


from codeparser.markdown_builder import build_markdown
from codeparser.parser_core import GenerationStats


def test_build_markdown_includes_file_contents():
    stats = GenerationStats(total_files=1, total_tokens=100)
    files = [{"path": "src/main.py", "content": "print('hello')", "lines": 1, "tokens": 5, "secrets": 0}]
    result = build_markdown(
        processed_files=files,
        directory_tree="src/\n  main.py",
        stats=stats,
        repository_name="test-repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    assert "# test-repo" in result
    assert "```" in result
    assert "print('hello')" in result
    assert "src/main.py" in result


def test_build_markdown_includes_directory_tree():
    stats = GenerationStats(total_files=1)
    files = [{"path": "a.py", "content": "x=1", "lines": 1, "tokens": None, "secrets": 0}]
    result = build_markdown(
        processed_files=files,
        directory_tree="a.py",
        stats=stats,
        repository_name="repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    assert "## Directory Structure" in result
    assert "a.py" in result
