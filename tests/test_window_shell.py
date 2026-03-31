from __future__ import annotations

import subprocess
import sys
import textwrap
from pathlib import Path

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtWidgets import QLabel

from codeparser_ui.components.toggle_switch import ToggleSwitch
from codeparser_ui.window.frameless_window import NativeFramelessWindow, WM_GETMINMAXINFO
from codeparser_ui.window.title_bar import TitleBar
from codeparser_ui.window.window_shell import NativeTitleBarWindow, WindowShell, create_window_shell


class _Tokens:
    def __init__(self, is_dark: bool) -> None:
        self.is_dark = is_dark


class _ThemeManager(QObject):
    themeChanged = pyqtSignal(object)


class _RecordingShell(WindowShell):
    def __init__(self, theme_manager: _ThemeManager | None = None) -> None:
        self.dark_mode_updates: list[bool] = []
        self._maximized_state = False
        super().__init__(theme_manager=theme_manager)

    def update_dark_mode(self, dark: bool) -> None:
        self.dark_mode_updates.append(dark)

    def isMaximized(self) -> bool:
        return self._maximized_state


def test_native_frameless_window_tracks_embedded_title_bar_without_reparenting(qtbot) -> None:
    window = NativeFramelessWindow()
    qtbot.addWidget(window)

    surface = QLabel("surface")
    title_bar = TitleBar(surface)

    window.set_title_bar(title_bar)
    window.set_content(surface)

    assert window._title_bar is title_bar
    assert title_bar.parentWidget() is surface


def test_native_frameless_window_treats_title_bar_toggles_as_interactive() -> None:
    host = QLabel("theme host")
    host.setProperty("interactiveInTitleBar", True)
    toggle = ToggleSwitch(host)
    toggle.setProperty("interactiveInTitleBar", True)

    assert NativeFramelessWindow._title_bar_child_is_interactive(host) is True
    assert NativeFramelessWindow._title_bar_child_is_interactive(toggle) is True


def test_window_shell_replaces_workbench_and_updates_window_state(qtbot) -> None:
    theme_manager = _ThemeManager()
    window = _RecordingShell(theme_manager=theme_manager)
    qtbot.addWidget(window)

    first = QLabel("first")
    second = QLabel("second")

    window.set_workbench(first)
    assert window._content_layout.count() == 1
    assert window._content_layout.itemAt(0).widget() is first

    window.set_workbench(second)
    assert first.parent() is None
    assert window._content_layout.itemAt(0).widget() is second

    window._maximized_state = True
    window._on_window_state_changed()
    assert window._surface.property("windowState") == "maximized"

    window._maximized_state = False
    window._on_window_state_changed()
    assert window._surface.property("windowState") == "normal"

    theme_manager.themeChanged.emit(_Tokens(is_dark=True))
    assert window.dark_mode_updates == [True]


def test_create_window_shell_uses_native_fallback_when_disabled(qtbot) -> None:
    shell = create_window_shell(use_custom_shell=False)
    qtbot.addWidget(shell)

    assert isinstance(shell, NativeTitleBarWindow)
    assert shell.uses_custom_shell is False


def test_native_event_uses_windows_msg_hwnd_field(monkeypatch, qtbot) -> None:
    window = NativeFramelessWindow()
    qtbot.addWidget(window)

    class _FakeMsg:
        message = WM_GETMINMAXINFO
        hWnd = 123
        lParam = 456

    calls: list[tuple[int, int]] = []

    monkeypatch.setattr(
        "codeparser_ui.window.frameless_window.IS_WINDOWS",
        True,
    )
    monkeypatch.setattr(
        "codeparser_ui.window.frameless_window.ctypes.wintypes.MSG.from_address",
        lambda _address: _FakeMsg(),
    )
    monkeypatch.setattr(
        window,
        "_handle_getminmaxinfo",
        lambda hwnd, lparam: calls.append((hwnd, lparam)),
    )

    handled, result = window.nativeEvent(b"windows_generic_MSG", 1)

    assert handled is True
    assert result == 0
    assert calls == [(123, 456)]


def test_premium_shell_can_show_without_native_crash() -> None:
    if sys.platform != "win32":
        return

    repo_root = Path(__file__).resolve().parents[1]
    script = textwrap.dedent(
        """
        from PyQt6.QtCore import QTimer
        from codeparser_ui.bootstrap import create_application
        from codeparser_ui.theme_manager import ThemeManager
        from codeparser_ui.workbench import create_workbench

        app = create_application([])
        theme = ThemeManager(app)
        theme.apply()
        window = create_workbench(
            theme_manager=theme,
            initial_target=None,
            use_custom_shell=True,
        )
        window.show()
        QTimer.singleShot(100, app.quit)
        app.exec()
        print(type(window).__name__)
        """
    )

    result = subprocess.run(
        [sys.executable, "-X", "faulthandler", "-c", script],
        cwd=repo_root,
        capture_output=True,
        text=True,
        timeout=15,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "CodeParserWorkbench" in result.stdout
