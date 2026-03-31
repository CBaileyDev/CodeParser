"""accessibility.py -- WCAG 2.1 contrast validation and widget helpers."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget


def setup_accessible_widget(
    widget: QWidget,
    name: str,
    description: str = "",
) -> None:
    """Set accessibility metadata on a widget."""
    widget.setAccessibleName(name)
    if description:
        widget.setAccessibleDescription(description)
    widget.setFocusPolicy(Qt.FocusPolicy.StrongFocus)


def contrast_ratio(fg_hex: str, bg_hex: str) -> float:
    """
    WCAG 2.1 contrast ratio between two hex colors.

    AA normal text: >= 4.5    AA large text: >= 3.0
    AAA normal text: >= 7.0   AAA large text: >= 4.5
    """

    def _luminance(hex_color: str) -> float:
        value = hex_color.lstrip("#")
        red, green, blue = (int(value[index:index + 2], 16) / 255 for index in (0, 2, 4))

        def _linearize(component: float) -> float:
            return component / 12.92 if component <= 0.04045 else ((component + 0.055) / 1.055) ** 2.4

        return (
            0.2126 * _linearize(red)
            + 0.7152 * _linearize(green)
            + 0.0722 * _linearize(blue)
        )

    luminance_one = _luminance(fg_hex)
    luminance_two = _luminance(bg_hex)
    lighter = max(luminance_one, luminance_two)
    darker = min(luminance_one, luminance_two)
    return (lighter + 0.05) / (darker + 0.05)


def validate_theme_contrast(tokens) -> dict[str, float]:
    """Return validated contrast ratios for the primary theme text tokens."""
    return {
        "text_primary": contrast_ratio(tokens.text_primary, tokens.bg_window),
        "text_secondary": contrast_ratio(tokens.text_secondary, tokens.bg_window),
        "text_muted": contrast_ratio(tokens.text_muted, tokens.bg_window),
        "accent": contrast_ratio(tokens.accent, tokens.bg_window),
    }
