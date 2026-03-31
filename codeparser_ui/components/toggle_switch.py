"""toggle_switch.py -- Animated toggle for binary preferences.

Do NOT replace every checkbox with a toggle. Use toggles for immediate-effect
binary preferences only: theme mode, "follow system", compact mode.
"""

from __future__ import annotations

from PyQt6.QtCore import QEasingCurve, QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QKeyEvent, QMouseEvent, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._checked = False
        self._offset = 2.0

        self.setObjectName("toggleSwitch")
        self.setFixedSize(44, 28)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setAccessibleName("Toggle switch")

        self._anim = QPropertyAnimation(self, b"offset", self)
        self._anim.setDuration(140)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

    @pyqtProperty(float)
    def offset(self) -> float:
        return self._offset

    @offset.setter
    def offset(self, value: float) -> None:
        self._offset = value
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def setChecked(self, checked: bool) -> None:
        if checked == self._checked:
            return
        self._checked = checked
        self._anim.stop()
        self._anim.setStartValue(self._offset)
        self._anim.setEndValue(self._target_offset())
        self._anim.start()
        self.toggled.emit(self._checked)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        if event.key() in (Qt.Key.Key_Space, Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self.setChecked(not self._checked)
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event: QPaintEvent) -> None:
        palette = self.palette()
        track = palette.highlight().color() if self._checked else palette.mid().color()
        knob = palette.base().color()

        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            painter.setPen(track.darker(115) if self._checked else palette.dark().color())
            painter.setBrush(track)
            painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)

            diameter = self.height() - 4
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(knob)
            painter.drawEllipse(QRectF(self._offset, 2, diameter, diameter))

            if self.hasFocus():
                focus_color = palette.highlight().color()
                focus_color.setAlpha(70)
                painter.setPen(focus_color)
                painter.setBrush(Qt.BrushStyle.NoBrush)
                painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 13, 13)
        finally:
            painter.end()

    def _target_offset(self) -> float:
        diameter = self.height() - 4
        return float(self.width() - diameter - 2) if self._checked else 2.0
