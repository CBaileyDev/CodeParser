from __future__ import annotations

import importlib

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest

from codeparser_ui.window.title_bar import TitleBar


def test_title_bar_updates_labels_and_drag_regions(qtbot) -> None:
    title_bar = TitleBar()
    qtbot.addWidget(title_bar)
    title_bar.resize(640, 40)
    title_bar.show()

    title_bar.set_title("Premium CodeParser")
    title_bar.set_subtitle("Repository intelligence packer")

    assert title_bar._title.text() == "Premium CodeParser"
    assert title_bar._subtitle.text() == "Repository intelligence packer"
    assert title_bar.is_draggable_point(title_bar._close_btn.geometry().center()) is False
    assert title_bar.is_draggable_point(QPoint(title_bar.width() // 2, title_bar.height() // 2)) is True
    assert not hasattr(title_bar, "_max_btn")

def test_title_bar_double_click_does_not_emit_maximize_restore(qtbot) -> None:
    title_bar = TitleBar()
    qtbot.addWidget(title_bar)
    title_bar.resize(640, 40)
    title_bar.show()

    triggered: list[bool] = []
    if hasattr(title_bar, "maximize_restore_requested"):
        title_bar.maximize_restore_requested.connect(lambda: triggered.append(True))

    QTest.mouseDClick(
        title_bar,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(title_bar.width() // 2, title_bar.height() // 2),
    )

    assert triggered == []


def test_title_bar_renders_app_icon_when_available(qtbot) -> None:
    bootstrap_module = importlib.import_module("codeparser_ui.bootstrap")

    app = bootstrap_module.create_application([])
    title_bar = TitleBar()
    qtbot.addWidget(title_bar)
    title_bar.show()

    assert app.windowIcon().isNull() is False
    assert title_bar._icon_label.pixmap() is not None
    assert title_bar._icon_label.pixmap().isNull() is False
