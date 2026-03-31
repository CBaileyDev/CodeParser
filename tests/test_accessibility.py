from __future__ import annotations

from codeparser_ui.utils.accessibility import contrast_ratio


def test_contrast_ratio_matches_validated_dark_theme_value() -> None:
    ratio = contrast_ratio("#E8EEF5", "#0B1016")

    assert ratio >= 15.0
