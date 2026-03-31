from __future__ import annotations

import importlib
from pathlib import Path

from PyQt6.QtCore import QSettings
from PyQt6.QtWidgets import QApplication


def test_main_window_uses_theme_selector_with_system_default(qtbot, tmp_path) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")

    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    app = QApplication.instance() or bootstrap_module.create_application([])
    theme_manager = theme_module.ThemeManager(app, settings=settings)
    window = module.MainWindow(theme_manager=theme_manager)
    qtbot.addWidget(window)

    assert window.theme_mode_combo.count() == 3
    assert window.theme_mode_combo.currentData() == theme_module.ThemeMode.SYSTEM
    assert module.QApplication.instance().styleSheet().strip()


def test_main_window_theme_selector_updates_manager_mode(qtbot, tmp_path) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")
    theme_module = importlib.import_module("codeparser_ui.theme_manager")

    settings = QSettings(str(tmp_path / "theme.ini"), QSettings.Format.IniFormat)
    app = QApplication.instance() or bootstrap_module.create_application([])
    theme_manager = theme_module.ThemeManager(app, settings=settings)
    window = module.MainWindow(theme_manager=theme_manager)
    qtbot.addWidget(window)

    index = window.theme_mode_combo.findData(theme_module.ThemeMode.DARK)
    window.theme_mode_combo.setCurrentIndex(index)

    assert theme_manager.mode == theme_module.ThemeMode.DARK


def test_main_window_starts_with_generate_tab_ready_state(qtbot) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    window = module.MainWindow()
    qtbot.addWidget(window)

    assert window.tab_widget.tabText(0) == "Generate"
    assert window.tab_widget.tabText(1) == "Build"
    assert window.tab_widget.currentWidget() is window.generate_tab
    assert window.target_edit.text() == ""
    assert window.output_editor.toPlainText() == ""
    assert window.copy_btn.isEnabled() is False
    assert window.save_btn.isEnabled() is False
    assert "Ready to preview" in window.generate_tab.preview_detail_label.text()


def test_build_tab_has_placeholder_copy(qtbot) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    window = module.MainWindow()
    qtbot.addWidget(window)

    assert "Rebuild a project from packed XML" in window.build_tab.placeholder_title.text()
    assert "coming soon" in window.build_tab.placeholder_body.text().lower()


def test_generate_tab_does_not_preview_until_target_is_selected(qtbot, monkeypatch) -> None:
    module = importlib.import_module("codeparser.gui.generate_tab")

    calls: list[object] = []

    def fake_generate_xml(*args, **kwargs):
        calls.append((args, kwargs))
        raise AssertionError("Preview generation should not run on launch without a target")

    monkeypatch.setattr(module, "generate_xml", fake_generate_xml)

    tab = module.GenerateTab(initial_target=None)
    qtbot.addWidget(tab)

    assert calls == []
    assert tab.target_edit.text() == ""
    assert "Ready to preview" in tab.preview_detail_label.text()


def test_generate_tab_keeps_cached_remote_target_alive_during_generation(
    qtbot,
    monkeypatch,
    tmp_path,
) -> None:
    module = importlib.import_module("codeparser.gui.generate_tab")
    parser_module = importlib.import_module("codeparser.parser_core")

    class FakeResolvedTarget:
        def __init__(self, root_path: Path) -> None:
            self.root_path = root_path
            self.display_name = "project"
            self.cleanup_calls = 0

        def cleanup(self) -> None:
            self.cleanup_calls += 1

    fake_target = FakeResolvedTarget(tmp_path)

    def fake_resolve_target(_value: str) -> FakeResolvedTarget:
        return fake_target

    def fake_generate_xml(_config, use_tqdm: bool = False, preview: bool = False):
        return "<file_summary />", parser_module.GenerationStats(total_files=1)

    monkeypatch.setattr(module, "resolve_target", fake_resolve_target)
    monkeypatch.setattr(module, "generate_xml", fake_generate_xml)

    tab = module.GenerateTab(
        initial_target="https://github.com/example/project",
        auto_refresh_preview=False,
    )
    qtbot.addWidget(tab)

    tab._cached_remote_target = fake_target
    tab._cached_remote_url = "https://github.com/example/project"

    xml_text, stats = tab._generate_xml()

    assert xml_text == "<file_summary />"
    assert stats.total_files == 1
    assert tab._cached_remote_target is fake_target
    assert fake_target.cleanup_calls == 0

    tab.close()
    QApplication.processEvents()
    assert fake_target.cleanup_calls == 1


def test_generate_tab_runs_generation_without_process_events(
    qtbot,
    monkeypatch,
    tmp_path,
) -> None:
    import time

    module = importlib.import_module("codeparser.gui.generate_tab")
    parser_module = importlib.import_module("codeparser.parser_core")
    worker_module = importlib.import_module("codeparser_ui.workers.generate_worker")

    root = tmp_path / "repo"
    root.mkdir()
    (root / "main.py").write_text("print('ok')\n", encoding="utf-8")

    calls: list[str] = []
    original_process_events = module.QApplication.processEvents

    def record_process_events(*args, **kwargs):
        calls.append("processEvents")
        return original_process_events(*args, **kwargs)

    def fake_generate_xml(_config, use_tqdm: bool = False, preview: bool = False):
        time.sleep(0.05)
        return "<file_summary />", parser_module.GenerationStats(total_files=1)

    monkeypatch.setattr(module.QApplication, "processEvents", record_process_events)
    monkeypatch.setattr(worker_module, "generate_xml", fake_generate_xml)

    tab = module.GenerateTab(initial_target=str(root), auto_refresh_preview=False)
    qtbot.addWidget(tab)

    try:
        tab._on_generate()
    finally:
        monkeypatch.setattr(module.QApplication, "processEvents", original_process_events)

    assert calls == []
    assert tab.generate_btn.isEnabled() is False
    qtbot.waitUntil(lambda: tab.output_editor.toPlainText() == "<file_summary />", timeout=3_000)
    assert tab.copy_btn.isEnabled() is True
    assert tab.save_btn.isEnabled() is True
    assert "Generated XML for 1 files." in tab.status_label.text()
