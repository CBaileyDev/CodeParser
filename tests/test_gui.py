from __future__ import annotations

import importlib


def test_main_window_uses_dark_theme_by_default(qtbot) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    window = module.MainWindow()
    qtbot.addWidget(window)

    assert window.dark_mode_cb.isChecked() is True
    assert module.QApplication.instance().styleSheet().strip()
