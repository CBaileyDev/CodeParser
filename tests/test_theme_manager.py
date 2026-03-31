from __future__ import annotations

import importlib

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QColor, QPalette


def test_theme_manager_defaults_to_dark_mode_when_unconfigured(tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")

    app = bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "default-theme.ini"), QSettings.Format.IniFormat)
    manager = theme_module.ThemeManager(app, settings=settings)

    assert manager.mode == theme_module.ThemeMode.DARK
    assert manager.apply() == theme_module.DARK_TOKENS


def test_theme_manager_applies_dark_tokens_to_palette_and_stylesheet(tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")

    app = bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    manager = theme_module.ThemeManager(app, settings=settings)

    tokens = manager.set_mode(theme_module.ThemeMode.DARK)

    assert tokens == theme_module.DARK_TOKENS
    assert app.palette().color(QPalette.ColorRole.Window) == QColor(tokens.bg_window)
    assert app.palette().color(QPalette.ColorRole.Highlight) == QColor(tokens.accent)
    assert 'QFrame#appSurface' in app.styleSheet()
    assert 'QPushButton[variant="primary"]' in app.styleSheet()
    assert 'QTabWidget#workbenchTabs QTabBar::tab:selected' in app.styleSheet()


def test_theme_manager_persists_selected_mode(tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")

    app = bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)

    manager = theme_module.ThemeManager(app, settings=settings)
    manager.set_mode(theme_module.ThemeMode.LIGHT)

    reloaded = theme_module.ThemeManager(app, settings=settings)
    assert reloaded.mode == theme_module.ThemeMode.LIGHT
