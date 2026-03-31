from __future__ import annotations

import importlib

from PyQt6.QtCore import QSettings, Qt
from PyQt6.QtWidgets import QApplication

from codeparser.output_format import OutputFormat


def test_create_workbench_uses_native_workbench_for_fallback(qtbot, tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")
    workbench_module = importlib.import_module("codeparser_ui.workbench")

    app = QApplication.instance() or bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    theme_manager = theme_module.ThemeManager(app, settings=settings)

    window = workbench_module.create_workbench(
        theme_manager=theme_manager,
        initial_target="",
        use_custom_shell=False,
    )
    qtbot.addWidget(window)
    window.show()

    assert window.uses_custom_shell is False
    assert window.tab_widget.tabText(0) == "Generate"
    assert window.tab_widget.tabText(1) == "Build"
    assert window.generate_tab.generate_btn.property("variant") == "primary"
    assert window.generate_tab.format_combo.currentData() == OutputFormat.MARKDOWN
    assert window.build_tab.build_button.property("variant") == "primary"
    assert window.tab_widget.cornerWidget(Qt.Corner.TopRightCorner) is not None


def test_workbench_theme_controls_switch_between_dark_and_light(qtbot, tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")
    workbench_module = importlib.import_module("codeparser_ui.workbench")

    app = QApplication.instance() or bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    theme_manager = theme_module.ThemeManager(app, settings=settings)

    window = workbench_module.NativeCodeParserWorkbench(
        theme_manager=theme_manager,
        initial_target="",
    )
    qtbot.addWidget(window)
    window.show()

    assert theme_manager.mode == theme_module.ThemeMode.DARK
    assert window.system_theme_switch.isChecked() is True
    assert getattr(window, "theme_mode_combo", None) is None

    window.system_theme_switch.setChecked(False)
    assert theme_manager.mode == theme_module.ThemeMode.LIGHT

    window.system_theme_switch.setChecked(True)
    assert window.system_theme_switch.isChecked() is True
    assert theme_manager.mode == theme_module.ThemeMode.DARK


def test_workbench_persists_target_and_active_tab(qtbot, tmp_path) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")
    workbench_module = importlib.import_module("codeparser_ui.workbench")

    app = QApplication.instance() or bootstrap_module.create_application([])
    settings = QSettings(str(tmp_path / "persist.ini"), QSettings.Format.IniFormat)
    theme_manager = theme_module.ThemeManager(app, settings=settings)

    window = workbench_module.NativeCodeParserWorkbench(
        theme_manager=theme_manager,
        initial_target="C:/repo",
        settings=settings,
    )
    qtbot.addWidget(window)
    window.show()

    window.tab_widget.setCurrentIndex(1)
    window.target_edit.setText("C:/another-repo")
    window._save_persistent_state()
    window.close()

    restored = workbench_module.NativeCodeParserWorkbench(
        theme_manager=theme_manager,
        initial_target=None,
        settings=settings,
    )
    qtbot.addWidget(restored)

    assert restored.tab_widget.currentIndex() == 1
    assert restored.target_edit.text() == "C:/another-repo"
