from __future__ import annotations

from typing import Optional

try:  # pragma: no cover - import guard
    import tiktoken  # type: ignore
except ImportError:  # pragma: no cover
    tiktoken = None  # type: ignore


def _get_encoding(model_name: str):
    if tiktoken is None:
        return None
    try:
        return tiktoken.encoding_for_model(model_name)
    except Exception:
        # Fall back to a generic encoding if the specific model is unknown.
        return tiktoken.get_encoding("cl100k_base")


def count_tokens(text: str, model_name: str = "gpt-4o-mini") -> Optional[int]:
    """Count tokens in the given text using tiktoken.

    Returns None if tiktoken is not available or encoding fails.
    """

    enc = _get_encoding(model_name)
    if enc is None:
        return None
    try:
        return len(enc.encode(text))
    except Exception:
        return None
