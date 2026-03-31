"""bootstrap.py -- Process-level setup. Call before creating any widgets."""

from __future__ import annotations

import logging
import sys
from typing import Sequence

from PyQt6.QtCore import QCoreApplication, QSettings, Qt
from PyQt6.QtGui import QGuiApplication
from PyQt6.QtWidgets import QApplication

USE_CUSTOM_SHELL_KEY = "window/use_custom_shell"
USE_CUSTOM_SHELL_MIGRATION_KEY = "window/use_custom_shell_migrated_v3"


def install_exception_hook() -> None:
    """Log uncaught exceptions before delegating to Python's default hook."""
    original_hook = sys.excepthook

    def _hook(exc_type, exc_value, exc_traceback):
        logging.getLogger("CodeParser").exception(
            "Unhandled exception",
            exc_info=(exc_type, exc_value, exc_traceback),
        )
        original_hook(exc_type, exc_value, exc_traceback)

    sys.excepthook = _hook


def ensure_phase_zero_settings(settings: QSettings | None = None) -> QSettings:
    """Seed the Phase 0 feature flags used by the premium shell migration."""
    target = settings or QSettings()
    migrated = target.value(USE_CUSTOM_SHELL_MIGRATION_KEY)

    if migrated is None:
        target.setValue(USE_CUSTOM_SHELL_KEY, True)
        target.setValue(USE_CUSTOM_SHELL_MIGRATION_KEY, True)
    elif target.value(USE_CUSTOM_SHELL_KEY) is None:
        target.setValue(USE_CUSTOM_SHELL_KEY, True)

    return target


def get_use_custom_shell(settings: QSettings | None = None) -> bool:
    """Return the native-titlebar fallback flag for the premium shell rollout."""
    value = ensure_phase_zero_settings(settings).value(USE_CUSTOM_SHELL_KEY, True)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "on"}
    return bool(value)


def set_use_custom_shell(
    settings: QSettings | None = None,
    enabled: bool = True,
) -> None:
    """Persist the premium-shell feature flag in QSettings."""
    target = settings or QSettings()
    target.setValue(USE_CUSTOM_SHELL_KEY, bool(enabled))
    target.setValue(USE_CUSTOM_SHELL_MIGRATION_KEY, True)


def create_application(argv: Sequence[str]) -> QApplication:
    """
    Construct QApplication with metadata, DPI policy, and base style.
    Call this before creating any top-level widgets.
    """
    QCoreApplication.setOrganizationName("CBaileyDev")
    QCoreApplication.setApplicationName("CodeParser")

    if QApplication.instance() is None:
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )
    install_exception_hook()

    app = QApplication.instance()
    if app is None:
        app = QApplication(list(argv))

    app.setStyle("Fusion")
    app.setQuitOnLastWindowClosed(True)
    ensure_phase_zero_settings()
    return app
