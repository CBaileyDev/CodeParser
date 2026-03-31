from __future__ import annotations

from PyQt6.QtCore import QSignalBlocker
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from codeparser_ui.theme_manager import ThemeManager, ThemeMode
from codeparser_ui.workbench import create_workbench

from .build_tab import BuildTab
from .generate_tab import GenerateTab


class MainWindow(QMainWindow):
    def __init__(
        self,
        initial_target: str | None = None,
        *,
        use_custom_shell: bool = True,
        theme_manager: ThemeManager | None = None,
    ) -> None:
        super().__init__()
        self.setWindowTitle("CodeParser")
        self.resize(1180, 820)
        self.setAcceptDrops(True)
        self.use_custom_shell = use_custom_shell
        app = QApplication.instance()
        if app is None:
            raise RuntimeError("MainWindow requires an existing QApplication instance.")
        self._theme_manager = theme_manager or ThemeManager(app)

        self._build_ui(initial_target or "")
        self._theme_manager.themeChanged.connect(self._on_theme_changed)
        self._sync_theme_mode_combo()
        self._theme_manager.apply()

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
        subtitle.setProperty("tone", "secondary")
        subtitle.setWordWrap(True)
        title_wrap.addWidget(subtitle)

        header_layout.addLayout(title_wrap, 1)

        theme_label = QLabel("Theme", header)
        theme_label.setProperty("tone", "muted")
        header_layout.addWidget(theme_label)

        self.theme_mode_combo = QComboBox(header)
        self.theme_mode_combo.setAccessibleName("Theme mode")
        self.theme_mode_combo.addItem("System", ThemeMode.SYSTEM)
        self.theme_mode_combo.addItem("Dark", ThemeMode.DARK)
        self.theme_mode_combo.addItem("Light", ThemeMode.LIGHT)
        self.theme_mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)
        header_layout.addWidget(self.theme_mode_combo)

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

    def _sync_theme_mode_combo(self) -> None:
        index = self.theme_mode_combo.findData(self._theme_manager.mode)
        if index < 0:
            return
        blocker = QSignalBlocker(self.theme_mode_combo)
        self.theme_mode_combo.setCurrentIndex(index)
        del blocker

    def _on_theme_mode_changed(self, _index: int) -> None:
        mode = self.theme_mode_combo.currentData()
        if isinstance(mode, ThemeMode):
            self._theme_manager.set_mode(mode)

    def _on_theme_changed(self, _tokens: object) -> None:
        self._sync_theme_mode_combo()

    def dragEnterEvent(self, event):  # type: ignore[override]
        self.generate_tab.dragEnterEvent(event)

    def dropEvent(self, event):  # type: ignore[override]
        self.generate_tab.dropEvent(event)


def run_gui(
    initial_target: str | None = None,
    *,
    app: QApplication | None = None,
    use_custom_shell: bool = True,
) -> int:
    qt_app = app or QApplication.instance() or QApplication([])
    theme_manager = ThemeManager(qt_app)
    theme_manager.apply()
    window = create_workbench(
        theme_manager=theme_manager,
        initial_target=initial_target,
        use_custom_shell=use_custom_shell,
    )
    window.show()
    return qt_app.exec()
