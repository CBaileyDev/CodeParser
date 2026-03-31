"""toggle_switch.py -- Animated toggle for binary preferences.

Do NOT replace every checkbox with a toggle. Use toggles for immediate-effect
binary preferences only: theme mode, "follow system", compact mode.
"""

from __future__ import annotations

from math import cos, sin, tau

from PyQt6.QtCore import QEasingCurve, QPointF, QPropertyAnimation, QRectF, Qt, pyqtProperty, pyqtSignal
from PyQt6.QtGui import QColor, QKeyEvent, QMouseEvent, QPaintEvent, QPainter, QPen
from PyQt6.QtWidgets import QWidget


class ToggleSwitch(QWidget):
    toggled = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None, *, theme_icons: bool = False) -> None:
        super().__init__(parent)
        self._checked = False
        self._offset = 2.0
        self._theme_icons = theme_icons

        self.setObjectName("toggleSwitch")
        self.setProperty("appearance", "theme" if theme_icons else "default")
        if theme_icons:
            self.setFixedSize(64, 30)
        else:
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
        del event
        palette = self.palette()
        painter = QPainter(self)
        try:
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            if self._theme_icons:
                self._paint_theme_toggle(painter)
            else:
                self._paint_default_toggle(painter)
        finally:
            painter.end()

    def _target_offset(self) -> float:
        diameter = self.height() - 4
        return float(self.width() - diameter - 2) if self._checked else 2.0

    def _paint_default_toggle(self, painter: QPainter) -> None:
        palette = self.palette()
        track = palette.highlight().color() if self._checked else palette.mid().color()
        knob = palette.base().color()

        painter.setPen(track.darker(115) if self._checked else palette.dark().color())
        painter.setBrush(track)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 14, 14)

        diameter = self.height() - 4
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(knob)
        painter.drawEllipse(QRectF(self._offset, 2, diameter, diameter))
        self._paint_focus_ring(painter)

    def _paint_theme_toggle(self, painter: QPainter) -> None:
        palette = self.palette()
        track = QColor(palette.highlight().color() if self._checked else palette.alternateBase().color())
        border = QColor(track.darker(135) if self._checked else palette.mid().color())
        knob = QColor("#F8FBFF")

        painter.setPen(QPen(border, 1.0))
        painter.setBrush(track)
        painter.drawRoundedRect(self.rect().adjusted(0, 0, -1, -1), 15, 15)

        knob_diameter = self.height() - 4
        knob_rect = QRectF(self._offset, 2, knob_diameter, knob_diameter)

        inactive_icon = QColor(palette.text().color())
        inactive_icon.setAlpha(110)
        active_icon = QColor("#1C2533") if self._checked else QColor("#B46900")

        self._draw_sun_icon(painter, QPointF(13, self.height() / 2), inactive_icon, 4.0)
        self._draw_moon_icon(
            painter,
            QPointF(self.width() - 13, self.height() / 2),
            inactive_icon,
            4.8,
        )

        painter.setPen(QPen(QColor(255, 255, 255, 225), 1.0))
        painter.setBrush(knob)
        painter.drawEllipse(knob_rect)

        knob_center = knob_rect.center()
        if self._checked:
            self._draw_moon_icon(painter, knob_center, active_icon, 4.8)
        else:
            self._draw_sun_icon(painter, knob_center, active_icon, 4.0)

        self._paint_focus_ring(painter)

    def _paint_focus_ring(self, painter: QPainter) -> None:
        if not self.hasFocus():
            return
        focus_color = self.palette().highlight().color()
        focus_color.setAlpha(80)
        painter.setPen(QPen(focus_color, 1.5))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawRoundedRect(self.rect().adjusted(1, 1, -2, -2), 13, 13)

    def _draw_sun_icon(
        self,
        painter: QPainter,
        center: QPointF,
        color: QColor,
        radius: float,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(color, 1.3, cap=Qt.PenCapStyle.RoundCap))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.drawEllipse(center, radius - 1.1, radius - 1.1)

        for index in range(8):
            angle = tau * index / 8.0
            inner = QPointF(
                center.x() + cos(angle) * (radius + 0.4),
                center.y() + sin(angle) * (radius + 0.4),
            )
            outer = QPointF(
                center.x() + cos(angle) * (radius + 2.2),
                center.y() + sin(angle) * (radius + 2.2),
            )
            painter.drawLine(inner, outer)
        painter.restore()

    def _draw_moon_icon(
        self,
        painter: QPainter,
        center: QPointF,
        color: QColor,
        radius: float,
    ) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(color)
        painter.drawEllipse(center, radius, radius)

        cutout = QColor("#F8FBFF") if color.alpha() > 200 else self.palette().window().color()
        painter.setBrush(cutout)
        painter.drawEllipse(
            QPointF(center.x() + radius * 0.45, center.y() - radius * 0.15),
            radius,
            radius,
        )
        painter.restore()
