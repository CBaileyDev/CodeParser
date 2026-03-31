from __future__ import annotations

import importlib

from PyQt6.QtCore import QCoreApplication, QSettings, Qt
from PyQt6.QtGui import QGuiApplication


def test_create_application_applies_metadata_dpi_and_fusion() -> None:
    module = importlib.import_module("codeparser_ui.bootstrap")

    app = module.create_application([])

    assert app.style().objectName().lower() == "fusion"
    assert QCoreApplication.organizationName() == "CBaileyDev"
    assert QCoreApplication.applicationName() == "CodeParser"
    assert (
        QGuiApplication.highDpiScaleFactorRoundingPolicy()
        == Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )


def test_use_custom_shell_defaults_false_and_round_trips(tmp_path) -> None:
    module = importlib.import_module("codeparser_ui.bootstrap")
    settings = QSettings(str(tmp_path / "phase0.ini"), QSettings.Format.IniFormat)

    module.ensure_phase_zero_settings(settings)
    assert module.get_use_custom_shell(settings) is False

    module.set_use_custom_shell(settings, True)
    assert module.get_use_custom_shell(settings) is True
