from __future__ import annotations

from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from . import BuildTab, apply_codeparser_dark_theme
from .generate_tab import GenerateTab


class MainWindow(QMainWindow):
    def __init__(self, initial_target: str | None = None) -> None:
        super().__init__()
        self.setWindowTitle("CodeParser")
        self.resize(1180, 820)
        self.setAcceptDrops(True)

        self._build_ui(initial_target or "")
        self.dark_mode_cb.setChecked(True)
        self._on_dark_mode_toggled()

    def _build_ui(self, initial_target: str) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        header = QWidget(root)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        title_wrap = QVBoxLayout()
        title_wrap.setSpacing(2)

        eyebrow = QLabel("WINDOWS DESKTOP UTILITY", header)
        eyebrow.setObjectName("CodeParserEyebrow")
        title_wrap.addWidget(eyebrow)

        title = QLabel("CodeParser", header)
        title.setObjectName("CodeParserTitle")
        title_wrap.addWidget(title)

        subtitle = QLabel(
            "Generate polished repository XML now, with a future Build workflow ready to land beside it.",
            header,
        )
        subtitle.setObjectName("CodeParserBody")
        subtitle.setWordWrap(True)
        title_wrap.addWidget(subtitle)

        header_layout.addLayout(title_wrap, 1)

        self.dark_mode_cb = QCheckBox("Dark theme")
        self.dark_mode_cb.stateChanged.connect(self._on_dark_mode_toggled)
        header_layout.addWidget(self.dark_mode_cb)

        layout.addWidget(header)

        self.tab_widget = QTabWidget(root)
        self.generate_tab = GenerateTab(initial_target=initial_target)
        self.build_tab = BuildTab()

        self.tab_widget.addTab(self.generate_tab, "Generate")
        self.tab_widget.addTab(self.build_tab, "Build")
        layout.addWidget(self.tab_widget, 1)

        # Backward-compatible attribute forwarding for tests/integration.
        self.target_edit = self.generate_tab.target_edit
        self.generate_btn = self.generate_tab.generate_btn
        self.copy_btn = self.generate_tab.copy_btn
        self.save_btn = self.generate_tab.save_btn
        self.output_editor = self.generate_tab.output_editor

    def _on_dark_mode_toggled(self) -> None:
        app = QApplication.instance()
        if not app:
            return
        if self.dark_mode_cb.isChecked():
            apply_codeparser_dark_theme(app)
        else:
            app.setStyleSheet("")

    def dragEnterEvent(self, event):  # type: ignore[override]
        self.generate_tab.dragEnterEvent(event)

    def dropEvent(self, event):  # type: ignore[override]
        self.generate_tab.dropEvent(event)


def run_gui(initial_target: str | None = None) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(initial_target=initial_target)
    window.show()
    app.exec()
