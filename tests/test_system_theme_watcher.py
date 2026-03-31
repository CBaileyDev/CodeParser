from __future__ import annotations

from codeparser_ui.utils.system_theme_watcher import SystemThemeWatcher


class _ThemeManager:
    def __init__(self) -> None:
        self.mode = "system"
        self.calls: list[str] = []

    def set_mode(self, mode: str) -> None:
        self.calls.append(mode)


class _Watcher(SystemThemeWatcher):
    def __init__(self, theme_manager: _ThemeManager, values: list[bool]) -> None:
        super().__init__(theme_manager)
        self._values = values

    def _detect(self) -> bool:
        return self._values.pop(0)


def test_system_theme_watcher_reapplies_system_mode_on_change() -> None:
    theme_manager = _ThemeManager()
    watcher = _Watcher(theme_manager, [True, False])

    watcher.start(interval_ms=10)
    watcher._check()

    assert theme_manager.calls == ["system"]
    watcher.stop()
