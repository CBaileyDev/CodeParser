"""sidebar.py -- Collapsible sidebar with proper animation lifecycle.

Key fixes:
- Animates BOTH minimumWidth and maximumWidth (Qt respects both constraints)
- Stores animation group on self to prevent garbage collection
- Hides child widgets when collapsed
"""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QParallelAnimationGroup, QPropertyAnimation, Qt, pyqtSignal
from PyQt6.QtWidgets import QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget


class CollapsibleSidebar(QWidget):
    EXPANDED_WIDTH = 300
    COLLAPSED_WIDTH = 48
    ANIMATION_DURATION = 200

    collapsed_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._is_collapsed = False
        self._animation_group: QParallelAnimationGroup | None = None

        self.setObjectName("sidebarPanel")
        self.setMinimumWidth(self.EXPANDED_WIDTH)
        self.setMaximumWidth(self.EXPANDED_WIDTH)
        self._build_ui()

    @property
    def is_collapsed(self) -> bool:
        return self._is_collapsed

    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        self.toggle_btn = QPushButton("<", self)
        self.toggle_btn.setObjectName("sidebarToggleButton")
        self.toggle_btn.setProperty("variant", "ghost")
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.setToolTip("Collapse sidebar")
        self.toggle_btn.setAccessibleName("Toggle sidebar")
        self.toggle_btn.clicked.connect(self.toggle)
        layout.addWidget(self.toggle_btn, alignment=Qt.AlignmentFlag.AlignRight)

        self._section_label = QLabel("CONFIG", self)
        self._section_label.setObjectName("sidebarSectionLabel")
        self._section_label.setProperty("tone", "muted")
        self._section_label.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Fixed,
        )
        layout.addWidget(self._section_label)

        self._content_host = QWidget(self)
        self._content_host.setSizePolicy(
            QSizePolicy.Policy.Ignored,
            QSizePolicy.Policy.Expanding,
        )
        self.content_layout = QVBoxLayout(self._content_host)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)
        layout.addWidget(self._content_host, 1)

    def toggle(self) -> None:
        self._is_collapsed = not self._is_collapsed
        target_width = self.COLLAPSED_WIDTH if self._is_collapsed else self.EXPANDED_WIDTH

        if self._is_collapsed:
            self._section_label.hide()
            self._content_host.hide()
        else:
            self._section_label.show()
            self._content_host.show()

        self._animation_group = QParallelAnimationGroup(self)

        for prop in (b"minimumWidth", b"maximumWidth"):
            animation = QPropertyAnimation(self, prop, self._animation_group)
            animation.setDuration(self.ANIMATION_DURATION)
            animation.setStartValue(getattr(self, prop.decode())())
            animation.setEndValue(target_width)
            animation.setEasingCurve(QEasingCurve.Type.InOutCubic)
            self._animation_group.addAnimation(animation)

        self._animation_group.finished.connect(self._on_finished)
        self._animation_group.start()

        self.toggle_btn.setText(">" if self._is_collapsed else "<")
        self.toggle_btn.setToolTip("Expand sidebar" if self._is_collapsed else "Collapse sidebar")

    def _on_finished(self) -> None:
        self._section_label.setVisible(not self._is_collapsed)
        self._content_host.setVisible(not self._is_collapsed)
        self.collapsed_changed.emit(self._is_collapsed)
