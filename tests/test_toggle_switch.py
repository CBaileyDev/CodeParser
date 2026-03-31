from __future__ import annotations

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtTest import QTest

from codeparser_ui.components.toggle_switch import ToggleSwitch


def test_toggle_switch_set_checked_updates_state_and_offset(qtbot) -> None:
    switch = ToggleSwitch()
    qtbot.addWidget(switch)
    switch.show()

    with qtbot.waitSignal(switch.toggled, timeout=1_000) as blocker:
        switch.setChecked(True)

    assert blocker.args == [True]
    assert switch.isChecked() is True
    qtbot.waitUntil(lambda: switch.offset > 2.0, timeout=1_000)


def test_toggle_switch_mouse_release_toggles_value(qtbot) -> None:
    switch = ToggleSwitch()
    qtbot.addWidget(switch)
    switch.show()

    QTest.mouseClick(
        switch,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(switch.width() // 2, switch.height() // 2),
    )

    assert switch.isChecked() is True


def test_toggle_switch_theme_variant_uses_wider_control(qtbot) -> None:
    switch = ToggleSwitch(theme_icons=True)
    qtbot.addWidget(switch)

    assert switch.width() == 64
    assert switch.height() == 30
