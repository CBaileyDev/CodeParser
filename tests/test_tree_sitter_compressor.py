from __future__ import annotations

import importlib
from pathlib import Path


def test_compress_source_falls_back_when_tree_sitter_languages_is_missing() -> None:
    module = importlib.import_module("codeparser.tree_sitter_compressor")

    original = "def hello():\n    return 'world'\n"
    compressed = module.compress_source_with_tree_sitter(original, Path("hello.py"))

    assert compressed == original


def test_count_tokens_returns_none_when_tiktoken_encodings_are_unavailable(monkeypatch) -> None:
    module = importlib.import_module("codeparser.token_counter")

    class BrokenTikToken:
        @staticmethod
        def encoding_for_model(_model_name: str):
            raise ValueError("missing model")

        @staticmethod
        def get_encoding(_encoding_name: str):
            raise ValueError("missing encoding")

    monkeypatch.setattr(module, "tiktoken", BrokenTikToken)

    assert module.count_tokens("hello world") is None
