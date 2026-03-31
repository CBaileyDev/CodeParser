from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QPlainTextEdit,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


class BuildTab(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()

    def _build_ui(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(24, 24, 24, 24)
        outer.setSpacing(16)

        hero = QFrame(self)
        hero.setObjectName("CodeParserPanel")
        hero.setProperty("surface", "panel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(10)

        eyebrow = QLabel("BUILD WORKFLOW", hero)
        eyebrow.setObjectName("CodeParserEyebrow")
        hero_layout.addWidget(eyebrow)

        self.placeholder_title = QLabel("Rebuild a project from packed files", hero)
        self.placeholder_title.setObjectName("CodeParserTitle")
        self.placeholder_title.setWordWrap(True)
        hero_layout.addWidget(self.placeholder_title)

        self.placeholder_body = QLabel(
            "The reverse workflow: feed a packed file back in, inspect the included files, "
            "and reconstruct the full directory tree. This is the next feature being built.",
            hero,
        )
        self.placeholder_body.setObjectName("CodeParserBody")
        self.placeholder_body.setProperty("tone", "secondary")
        self.placeholder_body.setWordWrap(True)
        self.placeholder_body.setTextFormat(Qt.TextFormat.PlainText)
        hero_layout.addWidget(self.placeholder_body)

        outer.addWidget(hero)

        action_surface = QFrame(self)
        action_surface.setObjectName("CodeParserSurface")
        action_surface.setProperty("surface", "panel")
        action_layout = QVBoxLayout(action_surface)
        action_layout.setContentsMargins(20, 20, 20, 20)
        action_layout.setSpacing(12)

        input_label = QLabel("PACKED FILE", action_surface)
        input_label.setObjectName("CodeParserEyebrow")
        action_layout.addWidget(input_label)

        self.xml_source_edit = QPlainTextEdit(action_surface)
        self.xml_source_edit.setPlaceholderText(
            "Drop or paste a packed file here when the build flow is ready.",
        )
        self.xml_source_edit.setReadOnly(True)
        self.xml_source_edit.setMinimumHeight(120)
        action_layout.addWidget(self.xml_source_edit)

        button_row = QHBoxLayout()
        button_row.setSpacing(10)

        self.output_folder_edit = QLineEdit(action_surface)
        self.output_folder_edit.setPlaceholderText("Output folder...")
        self.output_folder_edit.setReadOnly(True)
        button_row.addWidget(self.output_folder_edit, 1)

        self.build_button = QPushButton("Rebuild files", action_surface)
        self.build_button.setProperty("variant", "primary")
        self.build_button.setEnabled(False)
        button_row.addWidget(self.build_button)

        action_layout.addLayout(button_row)
        outer.addWidget(action_surface)

        outer.addStretch(1)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
