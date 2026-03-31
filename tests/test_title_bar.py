from __future__ import annotations

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


def test_title_bar_double_click_emits_maximize_restore(qtbot) -> None:
    title_bar = TitleBar()
    qtbot.addWidget(title_bar)
    title_bar.resize(640, 40)
    title_bar.show()

    with qtbot.waitSignal(title_bar.maximize_restore_requested, timeout=1_000):
        QTest.mouseDClick(
            title_bar,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(title_bar.width() // 2, title_bar.height() // 2),
        )
