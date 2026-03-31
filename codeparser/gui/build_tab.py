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
        outer.setContentsMargins(16, 16, 16, 16)
        outer.setSpacing(14)

        hero = QFrame(self)
        hero.setObjectName("CodeParserPanel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(8)

        eyebrow = QLabel("BUILD WORKFLOW", hero)
        eyebrow.setObjectName("CodeParserEyebrow")
        hero_layout.addWidget(eyebrow)

        self.placeholder_title = QLabel("Rebuild a project from packed XML", hero)
        self.placeholder_title.setObjectName("CodeParserTitle")
        self.placeholder_title.setWordWrap(True)
        hero_layout.addWidget(self.placeholder_title)

        self.placeholder_body = QLabel(
            "This tab is reserved for the reverse workflow: choose a CodeParser or Repomix-style XML file, "
            "inspect the included files, and restore the directory tree when the builder is ready. "
            "Build support is coming soon, but the shell is already prepared for it. "
            "For now, the shell is in place so the future flow can land without another redesign.",
            hero,
        )
        self.placeholder_body.setObjectName("CodeParserBody")
        self.placeholder_body.setWordWrap(True)
        self.placeholder_body.setTextFormat(Qt.TextFormat.PlainText)
        hero_layout.addWidget(self.placeholder_body)

        outer.addWidget(hero)

        surface = QFrame(self)
        surface.setObjectName("CodeParserSurface")
        surface_layout = QVBoxLayout(surface)
        surface_layout.setContentsMargins(18, 18, 18, 18)
        surface_layout.setSpacing(12)

        surface_heading = QLabel("Future steps", surface)
        surface_heading.setObjectName("CodeParserEyebrow")
        surface_layout.addWidget(surface_heading)

        self.xml_source_edit = QPlainTextEdit(surface)
        self.xml_source_edit.setPlaceholderText(
            "Drop or paste a packed XML file here when the build flow is implemented.",
        )
        self.xml_source_edit.setReadOnly(True)
        self.xml_source_edit.setMinimumHeight(140)
        surface_layout.addWidget(self.xml_source_edit)

        row = QHBoxLayout()
        row.setSpacing(12)

        folder_group = QFrame(surface)
        folder_group.setObjectName("CodeParserInset")
        folder_layout = QVBoxLayout(folder_group)
        folder_layout.setContentsMargins(14, 14, 14, 14)
        folder_layout.setSpacing(6)

        folder_label = QLabel("Output folder", folder_group)
        folder_label.setObjectName("CodeParserMetricLabel")
        folder_layout.addWidget(folder_label)

        self.output_folder_edit = QLineEdit(folder_group)
        self.output_folder_edit.setPlaceholderText("Choose a folder for reconstructed files...")
        self.output_folder_edit.setReadOnly(True)
        folder_layout.addWidget(self.output_folder_edit)

        row.addWidget(folder_group, 1)

        action_group = QFrame(surface)
        action_group.setObjectName("CodeParserInset")
        action_layout = QVBoxLayout(action_group)
        action_layout.setContentsMargins(14, 14, 14, 14)
        action_layout.setSpacing(8)

        action_label = QLabel("Builder action", action_group)
        action_label.setObjectName("CodeParserMetricLabel")
        action_layout.addWidget(action_label)

        self.build_button = QPushButton("Rebuild files", action_group)
        self.build_button.setEnabled(False)
        action_layout.addWidget(self.build_button)

        hint = QLabel(
            "Placeholder only. The future builder can parse the XML, reconstruct directories, and write each file back to disk.",
            action_group,
        )
        hint.setObjectName("CodeParserBody")
        hint.setWordWrap(True)
        action_layout.addWidget(hint)

        row.addWidget(action_group, 1)

        surface_layout.addLayout(row)
        outer.addWidget(surface)
        outer.addStretch(1)

        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
