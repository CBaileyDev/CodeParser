from __future__ import annotations

import importlib
from pathlib import Path

from PyQt6.QtWidgets import QApplication


def test_main_window_uses_dark_theme_by_default(qtbot) -> None:
    module = importlib.import_module("codeparser.gui.main_window")
    window = module.MainWindow()
    qtbot.addWidget(window)

    assert window.dark_mode_cb.isChecked() is True
    assert module.QApplication.instance().styleSheet().strip()


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
