"""command_palette.py -- Lightweight command palette for workbench actions."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout


@dataclass(frozen=True, slots=True)
class CommandPaletteCommand:
    title: str
    shortcut: str
    handler: Callable[[], None]
    subtitle: str = ""


class CommandPaletteDialog(QDialog):
    """Simple searchable command palette dialog."""

    def __init__(
        self,
        commands: list[CommandPaletteCommand],
        parent=None,
    ) -> None:
        super().__init__(parent)
        self._commands = commands

        self.setWindowTitle("Command Palette")
        self.setModal(True)
        self.resize(520, 360)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.filter_edit = QLineEdit(self)
        self.filter_edit.setPlaceholderText("Search commands...")
        self.filter_edit.textChanged.connect(self._refresh_items)
        layout.addWidget(self.filter_edit)

        self.command_list = QListWidget(self)
        self.command_list.itemActivated.connect(self._activate_item)
        self.command_list.itemDoubleClicked.connect(self._activate_item)
        layout.addWidget(self.command_list, 1)

        self._refresh_items()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self.filter_edit.setFocus()
        self.filter_edit.selectAll()

    def _refresh_items(self) -> None:
        search_text = self.filter_edit.text().strip().lower()
        self.command_list.clear()

        matches = [
            command
            for command in self._commands
            if not search_text
            or search_text in command.title.lower()
            or search_text in command.shortcut.lower()
            or search_text in command.subtitle.lower()
        ]

        for command in matches:
            label = f"{command.title}    {command.shortcut}"
            if command.subtitle:
                label = f"{label}\n{command.subtitle}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, command)
            self.command_list.addItem(item)

        if self.command_list.count():
            self.command_list.setCurrentRow(0)

    def _activate_item(self, item: QListWidgetItem) -> None:
        command = item.data(Qt.ItemDataRole.UserRole)
        if command is None:
            return
        self.hide()
        command.handler()
        self.accept()

    def _activate_current_command(self) -> None:
        item = self.command_list.currentItem()
        if item is not None:
            self._activate_item(item)

    def keyPressEvent(self, event) -> None:
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._activate_current_command()
            event.accept()
            return
        super().keyPressEvent(event)
