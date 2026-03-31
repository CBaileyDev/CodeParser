"""system_theme_watcher.py -- Poll-based fallback watcher for system theme changes."""

from __future__ import annotations

import sys

from PyQt6.QtCore import QObject, QTimer


class SystemThemeWatcher(QObject):
    """
    For Qt < 6.5 on Windows (no colorSchemeChanged signal),
    poll the registry every 2 seconds.

    On Qt 6.5+, ThemeManager already listens to colorSchemeChanged
    and this class is unnecessary.
    """

    def __init__(self, theme_manager, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._check)
        self._last: bool | None = None

    def start(self, interval_ms: int = 2_000) -> None:
        self._last = self._detect()
        self._timer.start(interval_ms)

    def stop(self) -> None:
        self._timer.stop()

    def _check(self) -> None:
        current = self._detect()
        if current != self._last:
            self._last = current
            self._theme_manager.set_mode(self._theme_manager.mode)

    def _detect(self) -> bool:
        """Return True if the system is in dark mode."""
        if sys.platform == "win32":
            try:
                import winreg

                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
                )
                value, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
                winreg.CloseKey(key)
                return value == 0
            except (FileNotFoundError, OSError):
                return True
        return True
