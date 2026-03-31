"""title_bar.py -- Custom title bar with accessible controls.

Dragging is handled by WM_NCHITTEST returning HTCAPTION.
This widget only provides visuals and button click handlers.
startSystemMove() is added as a Wayland/macOS fallback.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QMouseEvent
from PyQt6.QtWidgets import (
    QAbstractButton,
    QHBoxLayout,
    QLabel,
    QSizePolicy,
    QToolButton,
    QWidget,
)


class TitleBar(QWidget):
    """Custom title bar with minimize/close controls and drag support."""

    minimize_requested = pyqtSignal()
    close_requested = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("titleBar")
        self.setFixedHeight(40)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(12, 0, 8, 0)
        self._layout.setSpacing(4)
        self._trailing_widget: QWidget | None = None

        self._title = QLabel("CodeParser", self)
        self._title.setObjectName("titleLabel")
        self._title.setAccessibleName("Application title")
        self._layout.addWidget(self._title)

        self._subtitle = QLabel("Repository packer", self)
        self._subtitle.setObjectName("titleSubtitle")
        self._subtitle.setProperty("tone", "muted")
        self._layout.addWidget(self._subtitle)

        self._layout.addStretch(1)

        self._min_btn = self._make_button(
            "windowControlButton",
            "Minimize",
            "−",
        )
        self._close_btn = self._make_button(
            "closeButton",
            "Close",
            "✕",
        )

        self._min_btn.clicked.connect(self.minimize_requested)
        self._close_btn.clicked.connect(self.close_requested)

        self._layout.addWidget(self._min_btn)
        self._layout.addWidget(self._close_btn)

    def set_title(self, text: str) -> None:
        self._title.setText(text)

    def set_subtitle(self, text: str) -> None:
        self._subtitle.setText(text)

    def set_trailing_widget(self, widget: QWidget) -> None:
        """Insert a widget before the window control buttons."""
        if self._trailing_widget is widget:
            return

        if self._trailing_widget is not None:
            self._layout.removeWidget(self._trailing_widget)
            self._trailing_widget.setParent(None)

        self._trailing_widget = widget
        self._trailing_widget.setProperty("interactiveInTitleBar", True)
        control_count = 2
        insert_index = max(0, self._layout.count() - control_count)
        self._layout.insertWidget(insert_index, widget)

    def update_window_state(self, maximized: bool) -> None:
        _ = maximized

    def is_draggable_point(self, pos) -> bool:
        """Only empty chrome should initiate drag."""
        child = self.childAt(pos)
        return child is None or not isinstance(child, QAbstractButton)

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        """Fallback drag for Wayland/macOS where WM_NCHITTEST is unavailable."""
        if (
            event.button() == Qt.MouseButton.LeftButton
            and self.is_draggable_point(event.position().toPoint())
        ):
            handle = self.window().windowHandle()
            if handle is not None and handle.startSystemMove():
                event.accept()
                return
        super().mousePressEvent(event)

    def _make_button(
        self,
        object_name: str,
        tooltip: str,
        glyph: str,
    ) -> QToolButton:
        button = QToolButton(self)
        button.setObjectName(object_name)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setAutoRaise(True)
        button.setFixedSize(40, 30)
        button.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        button.setText(glyph)
        return button
