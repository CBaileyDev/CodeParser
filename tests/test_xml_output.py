from __future__ import annotations

import importlib


def test_generate_xml_matches_repomix_style_sections_and_tree(tmp_path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "src").mkdir()
    (root / "src" / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (root / "README.md").write_text("# Demo\n", encoding="utf-8")
    (root / ".gitignore").write_text("ignored.txt\n", encoding="utf-8")
    (root / "ignored.txt").write_text("ignore me\n", encoding="utf-8")

    config_module = importlib.import_module("codeparser.config")
    parser_module = importlib.import_module("codeparser.parser_core")

    xml_text, stats = parser_module.generate_xml(
        config_module.CodeParserConfig(root_path=root)
    )

    assert stats.total_files == 3
    assert xml_text.startswith(
        "This file is a merged representation of the entire codebase, combined into a single document by CodeParser."
    )
    assert "<file_summary>" in xml_text
    assert "<directory_structure>" in xml_text
    assert "<files>" in xml_text
    assert "<user_provided_header>\nThis repository is demo\n</user_provided_header>" in xml_text
    assert "src/\n  main.py" in xml_text
    assert '<file path="src/main.py">' in xml_text
    assert '<file path=".gitignore">' in xml_text
    assert '<file path="ignored.txt">' not in xml_text


def test_generate_xml_excludes_selected_output_file_from_packed_files(tmp_path) -> None:
    root = tmp_path / "demo"
    root.mkdir()
    (root / "main.py").write_text("print('hi')\n", encoding="utf-8")
    (root / "review.xml").write_text("<stale />\n", encoding="utf-8")

    config_module = importlib.import_module("codeparser.config")
    parser_module = importlib.import_module("codeparser.parser_core")

    xml_text, stats = parser_module.generate_xml(
        config_module.CodeParserConfig(
            root_path=root,
            output_path=root / "review.xml",
        )
    )

    assert stats.total_files == 1
    assert '<file path="main.py">' in xml_text
    assert '<file path="review.xml">' not in xml_text
    assert "Repository Structure section for a complete list of file paths" not in xml_text
