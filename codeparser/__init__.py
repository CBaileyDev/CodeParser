from __future__ import annotations

from typing import TYPE_CHECKING, Any

__all__ = ["CodeParserConfig", "GenerationStats", "generate_xml"]

if TYPE_CHECKING:
    from .config import CodeParserConfig
    from .parser_core import GenerationStats


def __getattr__(name: str) -> Any:
    if name == "CodeParserConfig":
        from .config import CodeParserConfig

        return CodeParserConfig

    if name in {"GenerationStats", "generate_xml"}:
        from .parser_core import GenerationStats, generate_xml

        if name == "GenerationStats":
            return GenerationStats
        return generate_xml

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
