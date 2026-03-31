"""workbench.py -- Host existing GenerateTab/BuildTab inside the premium shell."""

from __future__ import annotations

from PyQt6.QtCore import QSettings, QSignalBlocker, Qt
from PyQt6.QtGui import QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QSplitter,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from codeparser.gui.build_tab import BuildTab
from codeparser.gui.generate_tab import GenerateTab

from .components.command_palette import CommandPaletteCommand, CommandPaletteDialog
from .components.sidebar import CollapsibleSidebar
from .components.toggle_switch import ToggleSwitch
from .theme_manager import ThemeManager, ThemeMode
from .utils.accessibility import setup_accessible_widget
from .utils.system_theme_watcher import SystemThemeWatcher
from .window.window_shell import NativeTitleBarWindow, WindowShell


class _WorkbenchContent(QWidget):
    def __init__(
        self,
        theme_manager: ThemeManager,
        settings: QSettings,
        initial_target: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._settings = settings
        self._shortcuts: list[QShortcut] = []
        self._focus_cycle_widgets: list[QWidget] = []
        self._last_focus_index = -1

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 18, 20, 18)
        root_layout.setSpacing(12)

        self.main_splitter = QSplitter(Qt.Orientation.Horizontal, self)
        self.main_splitter.setChildrenCollapsible(False)

        self.sidebar = CollapsibleSidebar(self.main_splitter)
        self._build_sidebar()

        center_surface = QFrame(self.main_splitter)
        center_surface.setObjectName("workbenchCenterSurface")
        center_surface.setProperty("surface", "panel")
        center_layout = QVBoxLayout(center_surface)
        center_layout.setContentsMargins(16, 16, 16, 16)
        center_layout.setSpacing(12)

        self.tab_widget = QTabWidget(center_surface)
        self.tab_widget.setObjectName("workbenchTabs")
        self.tab_widget.setDocumentMode(True)

        self.generate_tab = GenerateTab(initial_target=initial_target)
        self.build_tab = BuildTab()

        self.tab_widget.addTab(self.generate_tab, "Generate")
        self.tab_widget.addTab(self.build_tab, "Build")
        center_layout.addWidget(self.tab_widget, 1)

        self.main_splitter.addWidget(self.sidebar)
        self.main_splitter.addWidget(center_surface)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([320, 1080])

        root_layout.addWidget(self.main_splitter, 1)

        self.target_edit = self.generate_tab.target_edit
        self.generate_btn = self.generate_tab.generate_btn
        self.copy_btn = self.generate_tab.copy_btn
        self.save_btn = self.generate_tab.save_btn
        self.output_editor = self.generate_tab.output_editor

        self._theme_manager.themeChanged.connect(self._on_theme_changed)
        self.tab_widget.currentChanged.connect(self._persist_active_tab)
        self.main_splitter.splitterMoved.connect(self._persist_splitter_state)
        self.target_edit.textChanged.connect(self._persist_source_path)
        self._command_palette = CommandPaletteDialog(self._build_commands(), self)
        self._install_shortcuts()
        self._install_accessibility()
        self._sync_theme_controls()

    def _build_sidebar(self) -> None:
        summary_wrap = QFrame(self.sidebar)
        summary_wrap.setProperty("surface", "elevated")
        summary_layout = QVBoxLayout(summary_wrap)
        summary_layout.setContentsMargins(14, 14, 14, 14)
        summary_layout.setSpacing(8)

        summary_title = QLabel("Workspace", summary_wrap)
        summary_title.setObjectName("sidebarSectionLabel")
        summary_layout.addWidget(summary_title)

        summary_body = QLabel(
            "Keep Generate and Build together inside one premium shell while the parser core stays unchanged.",
            summary_wrap,
        )
        summary_body.setObjectName("CodeParserBody")
        summary_body.setProperty("tone", "secondary")
        summary_body.setWordWrap(True)
        summary_layout.addWidget(summary_body)

        self.sidebar.content_layout.addWidget(summary_wrap)

        actions_wrap = QFrame(self.sidebar)
        actions_wrap.setProperty("surface", "elevated")
        actions_layout = QVBoxLayout(actions_wrap)
        actions_layout.setContentsMargins(14, 14, 14, 14)
        actions_layout.setSpacing(8)

        actions_title = QLabel("Quick actions", actions_wrap)
        actions_title.setObjectName("sidebarSectionLabel")
        actions_layout.addWidget(actions_title)

        self.open_button = QPushButton("Open folder", actions_wrap)
        self.open_button.setProperty("variant", "toolbar")
        self.open_button.clicked.connect(self._open_folder)
        actions_layout.addWidget(self.open_button)

        self.generate_now_button = QPushButton("Generate XML", actions_wrap)
        self.generate_now_button.setProperty("variant", "primary")
        self.generate_now_button.clicked.connect(self._generate_current_target)
        actions_layout.addWidget(self.generate_now_button)

        self.export_button = QPushButton("Export XML", actions_wrap)
        self.export_button.setProperty("variant", "toolbar")
        self.export_button.clicked.connect(self._export_xml)
        actions_layout.addWidget(self.export_button)

        self.sidebar.content_layout.addWidget(actions_wrap)

        theme_wrap = QFrame(self.sidebar)
        theme_wrap.setProperty("surface", "elevated")
        theme_layout = QVBoxLayout(theme_wrap)
        theme_layout.setContentsMargins(14, 14, 14, 14)
        theme_layout.setSpacing(10)

        theme_title = QLabel("Appearance", theme_wrap)
        theme_title.setObjectName("sidebarSectionLabel")
        theme_layout.addWidget(theme_title)

        system_row = QHBoxLayout()
        system_row.setSpacing(10)
        system_label_wrap = QVBoxLayout()
        system_label_wrap.setSpacing(2)

        system_label = QLabel("Follow system", theme_wrap)
        system_label.setObjectName("CodeParserMetricLabel")
        system_label_wrap.addWidget(system_label)

        system_hint = QLabel("Use the OS theme automatically.", theme_wrap)
        system_hint.setObjectName("CodeParserBody")
        system_hint.setProperty("tone", "secondary")
        system_hint.setWordWrap(True)
        system_label_wrap.addWidget(system_hint)

        system_row.addLayout(system_label_wrap, 1)

        self.system_theme_switch = ToggleSwitch(theme_wrap)
        self.system_theme_switch.toggled.connect(self._on_system_theme_toggled)
        system_row.addWidget(self.system_theme_switch, 0, Qt.AlignmentFlag.AlignTop)
        theme_layout.addLayout(system_row)

        self.theme_mode_combo = QComboBox(theme_wrap)
        self.theme_mode_combo.setAccessibleName("Theme mode selector")
        self.theme_mode_combo.addItem("Dark", ThemeMode.DARK)
        self.theme_mode_combo.addItem("Light", ThemeMode.LIGHT)
        self.theme_mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)
        theme_layout.addWidget(self.theme_mode_combo)

        self.sidebar.content_layout.addWidget(theme_wrap)
        self.sidebar.content_layout.addStretch(1)

    def _build_commands(self) -> list[CommandPaletteCommand]:
        return [
            CommandPaletteCommand(
                title="Open folder",
                shortcut="Ctrl+O",
                handler=self._open_folder,
                subtitle="Open a local repository folder for Generate.",
            ),
            CommandPaletteCommand(
                title="Paste repository URL",
                shortcut="Ctrl+Shift+V",
                handler=self._paste_repository_url,
                subtitle="Paste a GitHub repository URL into the source field.",
            ),
            CommandPaletteCommand(
                title="Generate XML",
                shortcut="Ctrl+Enter",
                handler=self._generate_current_target,
                subtitle="Run the Generate workflow for the current target.",
            ),
            CommandPaletteCommand(
                title="Export XML",
                shortcut="Ctrl+Shift+E",
                handler=self._export_xml,
                subtitle="Save the generated XML to disk.",
            ),
            CommandPaletteCommand(
                title="Focus source input",
                shortcut="Ctrl+L",
                handler=self._focus_source_input,
                subtitle="Jump to the target path or repository URL field.",
            ),
            CommandPaletteCommand(
                title="Switch to Generate tab",
                shortcut="Ctrl+1",
                handler=self._select_generate_tab,
                subtitle="Focus the Generate workflow.",
            ),
            CommandPaletteCommand(
                title="Switch to Build tab",
                shortcut="Ctrl+2",
                handler=self._select_build_tab,
                subtitle="Focus the Build workflow.",
            ),
        ]

    def _install_shortcuts(self) -> None:
        shortcuts: list[tuple[str, callable]] = [
            ("Ctrl+K", self._show_command_palette),
            ("Ctrl+O", self._open_folder),
            ("Ctrl+Shift+V", self._paste_repository_url),
            ("Ctrl+Enter", self._generate_current_target),
            ("Ctrl+Shift+E", self._export_xml),
            ("Ctrl+L", self._focus_source_input),
            ("F6", self._cycle_major_panes),
            ("Ctrl+1", self._select_generate_tab),
            ("Ctrl+2", self._select_build_tab),
        ]

        for sequence, handler in shortcuts:
            shortcut = QShortcut(QKeySequence(sequence), self)
            shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
            shortcut.activated.connect(handler)
            self._shortcuts.append(shortcut)

        self._focus_cycle_widgets = [
            self.sidebar.toggle_btn,
            self.theme_mode_combo,
            self.target_edit,
            self.output_editor,
        ]

    def _install_accessibility(self) -> None:
        setup_accessible_widget(
            self.sidebar.toggle_btn,
            "Toggle sidebar",
            "Collapse or expand the configuration sidebar.",
        )
        setup_accessible_widget(
            self.open_button,
            "Open folder",
            "Choose a local repository folder to pack.",
        )
        setup_accessible_widget(
            self.generate_now_button,
            "Generate XML",
            "Generate the repository XML from the current target.",
        )
        setup_accessible_widget(
            self.export_button,
            "Export XML",
            "Save the current XML output to disk.",
        )
        setup_accessible_widget(
            self.system_theme_switch,
            "Follow system theme",
            "Toggle whether the workbench follows the operating system color scheme.",
        )
        setup_accessible_widget(
            self.theme_mode_combo,
            "Theme mode",
            "Choose the workbench color theme when system-follow is disabled.",
        )
        setup_accessible_widget(
            self.tab_widget,
            "Workflow tabs",
            "Switch between the Generate and Build workflows.",
        )
        setup_accessible_widget(
            self.target_edit,
            "Repository source",
            "Enter a local folder path or a GitHub repository URL.",
        )
        setup_accessible_widget(
            self.output_editor,
            "Generated XML output",
            "Read the generated XML content for the active repository.",
        )
        self._command_palette.filter_edit.setAccessibleName("Command palette search")
        self._command_palette.command_list.setAccessibleName("Command palette results")

    def _sync_theme_controls(self) -> None:
        mode = self._theme_manager.mode
        if mode == ThemeMode.SYSTEM:
            combo_mode = ThemeMode.DARK if self._theme_manager.tokens.is_dark else ThemeMode.LIGHT
            follow_system = True
        else:
            combo_mode = mode
            follow_system = False

        switch_blocker = QSignalBlocker(self.system_theme_switch)
        combo_blocker = QSignalBlocker(self.theme_mode_combo)
        self.system_theme_switch.setChecked(follow_system)
        index = self.theme_mode_combo.findData(combo_mode)
        if index >= 0:
            self.theme_mode_combo.setCurrentIndex(index)
        self.theme_mode_combo.setEnabled(not follow_system)
        del combo_blocker
        del switch_blocker

    def _selected_theme_mode(self) -> ThemeMode:
        selected = self.theme_mode_combo.currentData()
        return selected if isinstance(selected, ThemeMode) else ThemeMode.DARK

    def _on_system_theme_toggled(self, enabled: bool) -> None:
        self.theme_mode_combo.setEnabled(not enabled)
        if enabled:
            self._theme_manager.set_mode(ThemeMode.SYSTEM)
            return
        self._theme_manager.set_mode(self._selected_theme_mode())

    def _on_theme_mode_changed(self, _index: int) -> None:
        if self.system_theme_switch.isChecked():
            return
        self._theme_manager.set_mode(self._selected_theme_mode())

    def _on_theme_changed(self, _tokens: object) -> None:
        self._sync_theme_controls()

    def _open_folder(self) -> None:
        self.generate_tab.browse_btn.click()

    def _generate_current_target(self) -> None:
        self.generate_tab.generate_btn.click()

    def _export_xml(self) -> None:
        self.generate_tab.save_btn.click()

    def _show_command_palette(self) -> None:
        self._command_palette.filter_edit.clear()
        self._command_palette._refresh_items()
        self._command_palette.show()
        self._command_palette.raise_()
        self._command_palette.activateWindow()

    def _paste_repository_url(self) -> None:
        current_value = self.target_edit.text().strip()
        value, accepted = QInputDialog.getText(
            self,
            "Paste Repository URL",
            "GitHub repository URL:",
            text=current_value,
        )
        if accepted and value.strip():
            self.target_edit.setText(value.strip())
            self.target_edit.setFocus()

    def _focus_source_input(self) -> None:
        self.target_edit.setFocus()
        self.target_edit.selectAll()

    def _cycle_major_panes(self) -> None:
        if not self._focus_cycle_widgets:
            return
        self._last_focus_index = (self._last_focus_index + 1) % len(self._focus_cycle_widgets)
        self._focus_cycle_widgets[self._last_focus_index].setFocus()

    def _select_generate_tab(self) -> None:
        self.tab_widget.setCurrentIndex(0)
        self.target_edit.setFocus()

    def _select_build_tab(self) -> None:
        self.tab_widget.setCurrentIndex(1)
        self.build_tab.build_button.setFocus()

    def restore_persistent_state(self, initial_target: str | None = None) -> None:
        splitter_state = self._settings.value("splitter/main")
        if splitter_state:
            self.main_splitter.restoreState(splitter_state)
        active_tab = int(self._settings.value("last/active_tab", 0))
        if 0 <= active_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(active_tab)

        if not initial_target:
            last_source = str(self._settings.value("last/source_path", ""))
            if last_source:
                self.target_edit.setText(last_source)

    def save_persistent_state(self) -> None:
        self._settings.setValue("splitter/main", self.main_splitter.saveState())
        self._settings.setValue("last/active_tab", self.tab_widget.currentIndex())
        self._settings.setValue("last/source_path", self.target_edit.text().strip())

    def _persist_splitter_state(self) -> None:
        self._settings.setValue("splitter/main", self.main_splitter.saveState())

    def _persist_active_tab(self, index: int) -> None:
        self._settings.setValue("last/active_tab", index)

    def _persist_source_path(self, value: str) -> None:
        self._settings.setValue("last/source_path", value.strip())


def _bind_workbench(window: QWidget, content: _WorkbenchContent) -> None:
    window.tab_widget = content.tab_widget
    window.generate_tab = content.generate_tab
    window.build_tab = content.build_tab
    window.sidebar = content.sidebar
    window.main_splitter = content.main_splitter
    window.system_theme_switch = content.system_theme_switch
    window.theme_mode_combo = content.theme_mode_combo
    window.target_edit = content.target_edit
    window.generate_btn = content.generate_btn
    window.copy_btn = content.copy_btn
    window.save_btn = content.save_btn
    window.output_editor = content.output_editor


class CodeParserWorkbench(WindowShell):
    """Host existing tabs inside the premium custom shell."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        initial_target: str | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__(theme_manager=theme_manager)
        self._settings = settings or QSettings()
        self._system_theme_watcher: SystemThemeWatcher | None = None
        self.setWindowTitle("CodeParser")
        self.title_bar.set_subtitle("Repository intelligence packer")

        content = _WorkbenchContent(theme_manager, self._settings, initial_target)
        self.set_workbench(content)
        _bind_workbench(self, content)
        self._restore_persistent_state(initial_target)
        self._start_system_theme_watcher_if_needed()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._clamp_to_available_geometry()

    def closeEvent(self, event) -> None:
        self._save_persistent_state()
        if self._system_theme_watcher is not None:
            self._system_theme_watcher.stop()
        super().closeEvent(event)

    def _start_system_theme_watcher_if_needed(self) -> None:
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            return
        self._system_theme_watcher = SystemThemeWatcher(self._theme_manager, self)
        self._system_theme_watcher.start()

    def _restore_persistent_state(self, initial_target: str | None = None) -> None:
        geometry = self._settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self._settings.value("window/state")
        if state:
            self.restoreState(state)
        self._clamp_to_available_geometry()
        self._content_layout.itemAt(0).widget().restore_persistent_state(initial_target)

    def _save_persistent_state(self) -> None:
        self._content_layout.itemAt(0).widget().save_persistent_state()
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())

    def _clamp_to_available_geometry(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return
        available = QApplication.primaryScreen().availableGeometry()
        current = self.frameGeometry()
        if any(screen.availableGeometry().intersects(current) for screen in screens):
            return

        width = min(current.width(), available.width())
        height = min(current.height(), available.height())
        x = max(available.left(), min(current.x(), available.right() - width + 1))
        y = max(available.top(), min(current.y(), available.bottom() - height + 1))
        self.setGeometry(x, y, width, height)


class NativeCodeParserWorkbench(NativeTitleBarWindow):
    """Native-titlebar fallback that still hosts the premium workbench content."""

    def __init__(
        self,
        theme_manager: ThemeManager,
        initial_target: str | None = None,
        settings: QSettings | None = None,
    ) -> None:
        super().__init__(theme_manager=theme_manager)
        self._settings = settings or QSettings()
        self._system_theme_watcher: SystemThemeWatcher | None = None
        self.setWindowTitle("CodeParser")

        content = _WorkbenchContent(theme_manager, self._settings, initial_target)
        self.set_workbench(content)
        _bind_workbench(self, content)
        self._restore_persistent_state(initial_target)
        self._start_system_theme_watcher_if_needed()

    def showEvent(self, event) -> None:
        super().showEvent(event)
        self._clamp_to_available_geometry()

    def closeEvent(self, event) -> None:
        self._save_persistent_state()
        if self._system_theme_watcher is not None:
            self._system_theme_watcher.stop()
        super().closeEvent(event)

    def _start_system_theme_watcher_if_needed(self) -> None:
        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            return
        self._system_theme_watcher = SystemThemeWatcher(self._theme_manager, self)
        self._system_theme_watcher.start()

    def _restore_persistent_state(self, initial_target: str | None = None) -> None:
        geometry = self._settings.value("window/geometry")
        if geometry:
            self.restoreGeometry(geometry)
        state = self._settings.value("window/state")
        if state:
            self.restoreState(state)
        self._clamp_to_available_geometry()
        self._content_layout.itemAt(0).widget().restore_persistent_state(initial_target)

    def _save_persistent_state(self) -> None:
        self._content_layout.itemAt(0).widget().save_persistent_state()
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("window/state", self.saveState())

    def _clamp_to_available_geometry(self) -> None:
        screens = QGuiApplication.screens()
        if not screens:
            return
        available = QApplication.primaryScreen().availableGeometry()
        current = self.frameGeometry()
        if any(screen.availableGeometry().intersects(current) for screen in screens):
            return

        width = min(current.width(), available.width())
        height = min(current.height(), available.height())
        x = max(available.left(), min(current.x(), available.right() - width + 1))
        y = max(available.top(), min(current.y(), available.bottom() - height + 1))
        self.setGeometry(x, y, width, height)


def create_workbench(
    *,
    theme_manager: ThemeManager,
    initial_target: str | None = None,
    use_custom_shell: bool = True,
    settings: QSettings | None = None,
) -> QWidget:
    if use_custom_shell and CodeParserWorkbench.supports_custom_shell():
        return CodeParserWorkbench(
            theme_manager=theme_manager,
            initial_target=initial_target,
            settings=settings,
        )
    return NativeCodeParserWorkbench(
        theme_manager=theme_manager,
        initial_target=initial_target,
        settings=settings,
    )
