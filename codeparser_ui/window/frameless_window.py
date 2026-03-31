"""frameless_window.py -- Production frameless window using WM_NCCALCSIZE + WM_NCHITTEST.

This preserves DWM shadow, native resize, Aero Snap, and Win11 Snap Layouts
WITHOUT using Qt.WindowType.FramelessWindowHint.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes
import sys

from PyQt6.QtCore import QByteArray, QPoint, QEvent
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout


# --------------------------------------------------
# Windows API constants
# --------------------------------------------------
HTCLIENT = 1
HTCAPTION = 2
HTLEFT = 10
HTRIGHT = 11
HTTOP = 12
HTTOPLEFT = 13
HTTOPRIGHT = 14
HTBOTTOM = 15
HTBOTTOMLEFT = 16
HTBOTTOMRIGHT = 17

WM_NCHITTEST = 0x0084
WM_NCCALCSIZE = 0x0083
WM_GETMINMAXINFO = 0x0024

# DWM attributes
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
DWMWA_WINDOW_CORNER_PREFERENCE = 33
DWMWA_SYSTEMBACKDROP_TYPE = 38

# DWM backdrop types (Windows 11 22H2+, build 22621+)
DWMSBT_MAINWINDOW = 2
DWMSBT_TRANSIENTWINDOW = 3
DWMSBT_TABBEDWINDOW = 4

# Legacy Mica (early Win11 builds only, pre-22621)
DWMWA_MICA_EFFECT_LEGACY = 1029

# Corner preferences
DWMWCP_ROUND = 2

MONITOR_DEFAULTTONEAREST = 2

IS_WINDOWS = sys.platform == "win32"


# --------------------------------------------------
# ctypes structures for WM_GETMINMAXINFO
# --------------------------------------------------
class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class RECT(ctypes.Structure):
    _fields_ = [
        ("left", ctypes.c_long),
        ("top", ctypes.c_long),
        ("right", ctypes.c_long),
        ("bottom", ctypes.c_long),
    ]


class MINMAXINFO(ctypes.Structure):
    _fields_ = [
        ("ptReserved", POINT),
        ("ptMaxSize", POINT),
        ("ptMaxPosition", POINT),
        ("ptMinTrackSize", POINT),
        ("ptMaxTrackSize", POINT),
    ]


class MONITORINFO(ctypes.Structure):
    _fields_ = [
        ("cbSize", ctypes.c_ulong),
        ("rcMonitor", RECT),
        ("rcWork", RECT),
        ("dwFlags", ctypes.c_ulong),
    ]


class NativeFramelessWindow(QMainWindow):
    """
    Frameless window that retains native Windows behavior.

    Architecture:
    1. Normal window (native frame preserved for DWM shadow + snap).
    2. WM_NCCALCSIZE: expand client area to hide the native title bar.
    3. WM_NCHITTEST: map regions to resize edges, title bar, and client.
    4. WM_GETMINMAXINFO: clamp maximize to current monitor work area.
    5. DWM provides drop shadow automatically.

    The result: a window that looks frameless but behaves natively -- resize
    cursors, Aero Snap, Win11 Snap Layouts, taskbar click to minimize, and
    multi-monitor DPI transitions all work correctly.
    """

    RESIZE_BORDER = 6
    TITLE_BAR_HEIGHT = 40
    OUTER_MARGIN = 0

    def __init__(self) -> None:
        super().__init__()

        self.setMinimumSize(1100, 720)
        self.resize(1440, 900)

        # Central container.
        self._central = QWidget()
        self._central.setObjectName("windowChromeRoot")
        self.setCentralWidget(self._central)
        self._layout = QVBoxLayout(self._central)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

        # Title bar -- set by subclass via set_title_bar().
        self._title_bar: QWidget | None = None

    @classmethod
    def supports_custom_shell(cls) -> bool:
        """Return True when the native Windows shell path is available."""
        return IS_WINDOWS

    def set_title_bar(self, title_bar: QWidget) -> None:
        """Set the custom title bar widget. Call before show()."""
        self._title_bar = title_bar
        if title_bar.parentWidget() is self._central and self._layout.indexOf(title_bar) < 0:
            self._layout.insertWidget(0, title_bar)

    def set_content(self, widget: QWidget) -> None:
        """Set the main content widget (below title bar)."""
        while self._layout.count():
            item = self._layout.takeAt(0)
            child = item.widget()
            if child is not None:
                child.setParent(None)
        self._layout.addWidget(widget, 1)

    def showEvent(self, event) -> None:
        super().showEvent(event)
        if IS_WINDOWS:
            self._apply_dwm_effects()

    def changeEvent(self, event) -> None:
        super().changeEvent(event)
        if event.type() == QEvent.Type.WindowStateChange:
            self._on_window_state_changed()

    # --------------------------------------------------
    # Windows native event handling -- THE KEY METHOD
    # --------------------------------------------------
    def nativeEvent(self, event_type: QByteArray, message: int) -> tuple[bool, int]:
        if not IS_WINDOWS or not self.supports_custom_shell():
            return super().nativeEvent(event_type, message)

        msg = ctypes.wintypes.MSG.from_address(int(message))

        if msg.message == WM_NCCALCSIZE:
            if msg.wParam:
                # Return 0: client area fills the entire window frame.
                # DWM shadow is preserved because we never used FramelessWindowHint.
                return True, 0

        if msg.message == WM_NCHITTEST:
            return self._handle_nchittest(msg)

        if msg.message == WM_GETMINMAXINFO:
            self._handle_getminmaxinfo(int(msg.hwnd), int(msg.lParam))
            return True, 0

        return super().nativeEvent(event_type, message)

    def _handle_nchittest(self, msg: ctypes.wintypes.MSG) -> tuple[bool, int]:
        """Map cursor position to window region."""
        x = ctypes.c_short(msg.lParam & 0xFFFF).value
        y = ctypes.c_short((msg.lParam >> 16) & 0xFFFF).value

        rect = self.geometry()
        local_x = x - rect.x()
        local_y = y - rect.y()
        width = rect.width()
        height = rect.height()
        border = self.RESIZE_BORDER

        if not self.isMaximized():
            if local_x < border and local_y < border:
                return True, HTTOPLEFT
            if local_x > width - border and local_y < border:
                return True, HTTOPRIGHT
            if local_x < border and local_y > height - border:
                return True, HTBOTTOMLEFT
            if local_x > width - border and local_y > height - border:
                return True, HTBOTTOMRIGHT

            if local_x < border:
                return True, HTLEFT
            if local_x > width - border:
                return True, HTRIGHT
            if local_y < border:
                return True, HTTOP
            if local_y > height - border:
                return True, HTBOTTOM

        if local_y < self.TITLE_BAR_HEIGHT:
            if self._title_bar is not None:
                title_pos = self._title_bar.mapFromGlobal(QPoint(x, y))
                child = self._title_bar.childAt(title_pos)
                if child is not None:
                    return True, HTCLIENT
            return True, HTCAPTION

        return True, HTCLIENT

    def _handle_getminmaxinfo(self, hwnd: int, lparam: int) -> None:
        """Clamp maximized window to current monitor's work area."""
        if not IS_WINDOWS:
            return

        user32 = ctypes.windll.user32
        monitor = user32.MonitorFromWindow(
            ctypes.wintypes.HWND(hwnd),
            MONITOR_DEFAULTTONEAREST,
        )
        if not monitor:
            return

        info = MONITORINFO()
        info.cbSize = ctypes.sizeof(MONITORINFO)
        if not user32.GetMonitorInfoW(monitor, ctypes.byref(info)):
            return

        work = info.rcWork
        monitor_rect = info.rcMonitor
        minmax = MINMAXINFO.from_address(lparam)

        minmax.ptMaxPosition.x = work.left - monitor_rect.left
        minmax.ptMaxPosition.y = work.top - monitor_rect.top
        minmax.ptMaxSize.x = work.right - work.left
        minmax.ptMaxSize.y = work.bottom - work.top
        minmax.ptMinTrackSize.x = max(minmax.ptMinTrackSize.x, self.minimumWidth())
        minmax.ptMinTrackSize.y = max(minmax.ptMinTrackSize.y, self.minimumHeight())

    # --------------------------------------------------
    # DWM effects
    # --------------------------------------------------
    def _apply_dwm_effects(self) -> None:
        """Apply DWM visual effects. Non-fatal on failure."""
        try:
            hwnd = int(self.winId())
            self._set_dwm_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1)
            self._set_dwm_attr(hwnd, DWMWA_WINDOW_CORNER_PREFERENCE, DWMWCP_ROUND)
            self._apply_backdrop(hwnd)
        except (AttributeError, OSError):
            pass

    def _apply_backdrop(self, hwnd: int) -> None:
        """Apply Mica. Falls back gracefully on older Windows."""
        if self._set_dwm_attr(hwnd, DWMWA_SYSTEMBACKDROP_TYPE, DWMSBT_MAINWINDOW):
            return
        self._set_dwm_attr(hwnd, DWMWA_MICA_EFFECT_LEGACY, 1)

    @staticmethod
    def _set_dwm_attr(hwnd: int, attribute: int, value: int) -> bool:
        """Set a DWM window attribute. Returns True on success."""
        if not IS_WINDOWS:
            return False
        data = ctypes.c_int(value)
        result = ctypes.windll.dwmapi.DwmSetWindowAttribute(
            hwnd,
            attribute,
            ctypes.byref(data),
            ctypes.sizeof(data),
        )
        return result == 0

    def _on_window_state_changed(self) -> None:
        """Override in subclass to update chrome when maximized/restored."""

    def update_dark_mode(self, dark: bool) -> None:
        """Call when theme changes to sync DWM chrome darkness."""
        if IS_WINDOWS:
            try:
                hwnd = int(self.winId())
                self._set_dwm_attr(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE, 1 if dark else 0)
            except (AttributeError, OSError):
                pass
