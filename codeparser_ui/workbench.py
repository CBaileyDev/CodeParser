"""workbench.py -- Host existing GenerateTab/BuildTab inside the premium shell."""

from __future__ import annotations

from PyQt6.QtCore import QSettings, QSignalBlocker, Qt
from PyQt6.QtGui import QColor, QGuiApplication, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QInputDialog,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from codeparser.gui.build_tab import BuildTab
from codeparser.gui.generate_tab import GenerateTab

from .components.command_palette import CommandPaletteCommand, CommandPaletteDialog
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
        root_layout.setContentsMargins(20, 12, 20, 18)
        root_layout.setSpacing(12)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("workbenchTabs")
        self.tab_widget.setDocumentMode(True)

        self.generate_tab = GenerateTab(initial_target=initial_target)
        self.build_tab = BuildTab()

        self.tab_widget.addTab(self.generate_tab, "Generate")
        self.tab_widget.addTab(self.build_tab, "Build")
        root_layout.addWidget(self.tab_widget, 1)

        self.target_edit = self.generate_tab.target_edit
        self.generate_btn = self.generate_tab.generate_btn

        self._theme_widget = QWidget(self)
        self._theme_widget.setObjectName("themeToggleContainer")
        self._theme_widget.setProperty("interactiveInTitleBar", True)
        theme_layout = QHBoxLayout(self._theme_widget)
        theme_layout.setContentsMargins(0, 0, 6, 0)
        theme_layout.setSpacing(0)

        self.system_theme_switch = ToggleSwitch(self._theme_widget, theme_icons=True)
        self.system_theme_switch.setProperty("interactiveInTitleBar", True)
        self.system_theme_switch.setToolTip("Toggle between dark and light theme")
        self.system_theme_switch.toggled.connect(self._on_theme_switch_toggled)
        theme_layout.addWidget(self.system_theme_switch)

        self._theme_manager.themeChanged.connect(self._on_theme_changed)
        self.tab_widget.currentChanged.connect(self._persist_active_tab)
        self.target_edit.textChanged.connect(self._persist_source_path)
        self._command_palette = CommandPaletteDialog(self._build_commands(), self)
        self._install_shortcuts()
        self._install_accessibility()
        self._sync_theme_controls()
        self._apply_surface_depth()

    @property
    def theme_widget(self) -> QWidget:
        """Compact theme controls for title bar or fallback placement."""
        return self._theme_widget

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
                title="Generate packed file",
                shortcut="Ctrl+Enter",
                handler=self._generate_current_target,
                subtitle="Run the Generate workflow for the current target.",
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
            self.system_theme_switch,
            self.target_edit,
            self.generate_tab.format_combo,
            self.generate_btn,
        ]

    def _install_accessibility(self) -> None:
        setup_accessible_widget(
            self.system_theme_switch,
            "Dark theme",
            "Toggle between dark and light theme modes.",
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
            self.generate_tab.format_combo,
            "Output format selector",
            "Choose the output format for the generated file.",
        )
        self._command_palette.filter_edit.setAccessibleName("Command palette search")
        self._command_palette.command_list.setAccessibleName("Command palette results")

    def _sync_theme_controls(self) -> None:
        mode = self._theme_manager.mode
        if mode == ThemeMode.SYSTEM:
            combo_mode = ThemeMode.DARK if self._theme_manager.tokens.is_dark else ThemeMode.LIGHT
        else:
            combo_mode = mode
        dark_enabled = combo_mode == ThemeMode.DARK

        switch_blocker = QSignalBlocker(self.system_theme_switch)
        self.system_theme_switch.setChecked(dark_enabled)
        del switch_blocker

    def _on_theme_switch_toggled(self, enabled: bool) -> None:
        self._theme_manager.set_mode(ThemeMode.DARK if enabled else ThemeMode.LIGHT)

    def _on_theme_changed(self, _tokens: object) -> None:
        self._sync_theme_controls()
        self._apply_surface_depth()

    def _apply_surface_depth(self) -> None:
        for frame in self.findChildren(QFrame):
            depth = frame.property("depth")
            if depth not in {"raised", "elevated"}:
                continue

            frame.setAttribute(Qt.WidgetAttribute.WA_Hover, True)

            effect = frame.graphicsEffect()
            if not isinstance(effect, QGraphicsDropShadowEffect):
                effect = QGraphicsDropShadowEffect(frame)
                effect.setOffset(0, 0)
                frame.setGraphicsEffect(effect)

            if depth == "elevated":
                effect.setBlurRadius(30)
                effect.setOffset(0, 10)
            else:
                effect.setBlurRadius(22)
                effect.setOffset(0, 6)

            if self._theme_manager.tokens.is_dark:
                effect.setColor(QColor(6, 10, 18, 170 if depth == "elevated" else 120))
            else:
                effect.setColor(QColor(37, 66, 110, 48 if depth == "elevated" else 32))

    def _open_folder(self) -> None:
        self.generate_tab.browse_btn.click()

    def _generate_current_target(self) -> None:
        self.generate_tab.generate_btn.click()

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
        active_tab = int(self._settings.value("last/active_tab", 0))
        if 0 <= active_tab < self.tab_widget.count():
            self.tab_widget.setCurrentIndex(active_tab)

        if not initial_target:
            last_source = str(self._settings.value("last/source_path", ""))
            if last_source:
                self.target_edit.setText(last_source)

    def save_persistent_state(self) -> None:
        self._settings.setValue("last/active_tab", self.tab_widget.currentIndex())
        self._settings.setValue("last/source_path", self.target_edit.text().strip())

    def _persist_active_tab(self, index: int) -> None:
        self._settings.setValue("last/active_tab", index)

    def _persist_source_path(self, value: str) -> None:
        self._settings.setValue("last/source_path", value.strip())


def _bind_workbench(window: QWidget, content: _WorkbenchContent) -> None:
    window.tab_widget = content.tab_widget
    window.generate_tab = content.generate_tab
    window.build_tab = content.build_tab
    window.system_theme_switch = content.system_theme_switch
    window.theme_mode_combo = None
    window.target_edit = content.target_edit
    window.generate_btn = content.generate_btn


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
        self.title_bar.set_subtitle("Repository Packer")

        content = _WorkbenchContent(theme_manager, self._settings, initial_target)
        self.set_workbench(content)
        _bind_workbench(self, content)
        self.title_bar.set_trailing_widget(content.theme_widget)
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
        self.tab_widget.setCornerWidget(content.theme_widget, Qt.Corner.TopRightCorner)
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
