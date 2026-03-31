from __future__ import annotations

import importlib


def test_parse_github_url_supports_branch_and_subdirectory() -> None:
    module = importlib.import_module("codeparser.remote")

    parsed = module.parse_github_url(
        "https://github.com/example/project/tree/main/src/app"
    )

    assert parsed.owner == "example"
    assert parsed.repo == "project"
    assert parsed.ref == "main"
    assert parsed.subdirectory == "src/app"
