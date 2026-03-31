"""window_shell.py -- Complete shell combining frameless window + title bar + surface."""

from __future__ import annotations

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtWidgets import QFrame, QMainWindow, QVBoxLayout, QWidget

from .frameless_window import (
    DWMWA_USE_IMMERSIVE_DARK_MODE,
    DWMWA_WINDOW_CORNER_PREFERENCE,
    DWMWCP_ROUND,
    IS_WINDOWS,
    NativeFramelessWindow,
)
from .title_bar import TitleBar


class NativeTitleBarWindow(QMainWindow):
    """Native-titlebar fallback window for platforms or settings that disable custom chrome."""

    def __init__(self, theme_manager=None) -> None:
        super().__init__()
        self.uses_custom_shell = False
        self._theme_manager = theme_manager
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.setMinimumSize(1100, 720)
        self.resize(1440, 900)

        self._central = QWidget()
        self.setCentralWidget(self._central)

        root_layout = QVBoxLayout(self._central)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        self._surface = QFrame()
        self._surface.setObjectName("appSurface")
        self._surface.setProperty("windowState", "normal")

        surface_layout = QVBoxLayout(self._surface)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)

        self._content_host = QWidget()
        self._content_layout = QVBoxLayout(self._content_host)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        surface_layout.addWidget(self._content_host, 1)

        root_layout.addWidget(self._surface, 1)

        if self._theme_manager is not None:
            self._theme_manager.themeChanged.connect(self._on_theme_changed)

    def set_workbench(self, widget: QWidget) -> None:
        """Set the main workbench widget inside the native fallback shell."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        self._content_layout.addWidget(widget)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._update_surface_window_state()
        self._apply_native_chrome()
        if self._theme_manager is not None:
            self._on_theme_changed(self._theme_manager.tokens)

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._update_surface_window_state()

    def _update_surface_window_state(self) -> None:
        state = "maximized" if self.isMaximized() else "normal"
        self._surface.setProperty("windowState", state)
        self._surface.style().unpolish(self._surface)
        self._surface.style().polish(self._surface)
        self._surface.update()

    def _apply_native_chrome(self) -> None:
        if not IS_WINDOWS:
            return
        try:
            NativeFramelessWindow._set_dwm_attr(
                int(self.winId()),
                DWMWA_WINDOW_CORNER_PREFERENCE,
                DWMWCP_ROUND,
            )
        except (AttributeError, OSError):
            pass

    def _on_theme_changed(self, tokens) -> None:
        if not IS_WINDOWS:
            return
        try:
            NativeFramelessWindow._set_dwm_attr(
                int(self.winId()),
                DWMWA_USE_IMMERSIVE_DARK_MODE,
                1 if tokens.is_dark else 0,
            )
        except (AttributeError, OSError):
            pass


class WindowShell(NativeFramelessWindow):
    """
    Premium shell that hosts the CodeParser workbench.

    Architecture:
    - NativeFramelessWindow handles WM_NCCALCSIZE/NCHITTEST/GETMINMAXINFO
    - This class adds the visual layer: title bar + rounded surface
    - On maximize: radius -> 0, margins -> 0
    - On restore: radius -> 14px, margins restored
    """

    NORMAL_MARGIN = 0

    def __init__(self, theme_manager=None) -> None:
        super().__init__()
        self.uses_custom_shell = True
        self._theme_manager = theme_manager
        self.setWindowFlag(Qt.WindowType.WindowMaximizeButtonHint, False)

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self._central.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._surface = QFrame()
        self._surface.setObjectName("appSurface")
        self._surface.setProperty("windowState", "normal")

        surface_layout = QVBoxLayout(self._surface)
        surface_layout.setContentsMargins(0, 0, 0, 0)
        surface_layout.setSpacing(0)

        self.title_bar = TitleBar(self)
        self.title_bar.minimize_requested.connect(self.showMinimized)
        self.title_bar.close_requested.connect(self.close)
        surface_layout.addWidget(self.title_bar)

        self._content_host = QWidget()
        self._content_layout = QVBoxLayout(self._content_host)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(0)
        surface_layout.addWidget(self._content_host, 1)

        self.set_title_bar(self.title_bar)
        self.set_content(self._surface)

        if self._theme_manager is not None:
            self._theme_manager.themeChanged.connect(self._on_theme_changed)

    @classmethod
    def supports_custom_shell(cls) -> bool:
        return super().supports_custom_shell()

    def set_workbench(self, widget: QWidget) -> None:
        """Set the main workbench widget inside the surface."""
        while self._content_layout.count():
            item = self._content_layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        self._content_layout.addWidget(widget)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if self._theme_manager is not None:
            self.update_dark_mode(self._theme_manager.tokens.is_dark)

    def _refresh_surface_window_state(self, maximized: bool) -> None:
        state = "maximized" if maximized else "normal"
        margin = 0 if maximized else self.NORMAL_MARGIN

        self._surface.setProperty("windowState", state)
        self._layout.setContentsMargins(margin, margin, margin, margin)
        self.title_bar.update_window_state(maximized)

        self._surface.style().unpolish(self._surface)
        self._surface.style().polish(self._surface)
        self._surface.update()

    def _on_window_state_changed(self) -> None:
        """Update surface styling when maximized/restored."""
        self._refresh_surface_window_state(self.isMaximized())

    def _on_theme_changed(self, tokens) -> None:
        self.update_dark_mode(tokens.is_dark)


def create_window_shell(theme_manager=None, *, use_custom_shell: bool = True) -> QMainWindow:
    """Return the premium custom shell or the native-titlebar fallback window."""
    if use_custom_shell and WindowShell.supports_custom_shell():
        return WindowShell(theme_manager=theme_manager)
    return NativeTitleBarWindow(theme_manager=theme_manager)
