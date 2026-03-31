"""theme_manager.py -- Theme manager with QPalette + semantic QSS."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import Enum

from PyQt6.QtCore import QObject, QSettings, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QGuiApplication, QPalette
from PyQt6.QtWidgets import QApplication

from .utils.accessibility import validate_theme_contrast


class ThemeMode(str, Enum):
    SYSTEM = "system"
    DARK = "dark"
    LIGHT = "light"


@dataclass(frozen=True, slots=True)
class ThemeTokens:
    """Immutable color/spacing tokens for a theme variant."""

    name: str
    is_dark: bool
    bg_window: str
    bg_panel: str
    bg_elevated: str
    bg_input: str
    bg_hover: str
    text_primary: str
    text_secondary: str
    text_muted: str
    text_on_accent: str
    accent: str
    accent_hover: str
    accent_pressed: str
    success: str
    warning: str
    danger: str
    border: str
    border_strong: str
    focus_ring: str
    separator: str
    radius_sm: int = 8
    radius_md: int = 12
    radius_lg: int = 14


DARK_TOKENS = ThemeTokens(
    name="dark",
    is_dark=True,
    bg_window="#0B1016",
    bg_panel="#111823",
    bg_elevated="#17202C",
    bg_input="#0F1620",
    bg_hover="#1B2633",
    text_primary="#E8EEF5",
    text_secondary="#B4C0CD",
    text_muted="#7F8B99",
    text_on_accent="#F8FBFF",
    accent="#7C9DFF",
    accent_hover="#92AEFF",
    accent_pressed="#6F90F5",
    success="#3FB950",
    warning="#D29922",
    danger="#F85149",
    border="#253041",
    border_strong="#334358",
    focus_ring="rgba(124, 157, 255, 0.42)",
    separator="rgba(255, 255, 255, 0.07)",
)

LIGHT_TOKENS = ThemeTokens(
    name="light",
    is_dark=False,
    bg_window="#F7F9FC",
    bg_panel="#FFFFFF",
    bg_elevated="#EFF3F8",
    bg_input="#FFFFFF",
    bg_hover="#EAF0F8",
    text_primary="#15202B",
    text_secondary="#425466",
    text_muted="#657487",
    text_on_accent="#FFFFFF",
    accent="#255EDC",
    accent_hover="#2E6BFF",
    accent_pressed="#2156C8",
    success="#1F8F45",
    warning="#A86A00",
    danger="#C93A2F",
    border="#D5DEE8",
    border_strong="#B9C5D2",
    focus_ring="rgba(37, 94, 220, 0.32)",
    separator="rgba(0, 0, 0, 0.08)",
)


def build_palette(tokens: ThemeTokens) -> QPalette:
    """Build QPalette from tokens. Keeps native dialogs and placeholder text coherent."""
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor(tokens.bg_window))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(tokens.text_primary))
    palette.setColor(QPalette.ColorRole.Base, QColor(tokens.bg_input))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(tokens.bg_panel))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(tokens.bg_panel))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(tokens.text_primary))
    palette.setColor(QPalette.ColorRole.Text, QColor(tokens.text_primary))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(tokens.text_muted))
    palette.setColor(QPalette.ColorRole.Button, QColor(tokens.bg_panel))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(tokens.text_primary))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(tokens.accent))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(tokens.text_on_accent))
    palette.setColor(QPalette.ColorRole.Link, QColor(tokens.accent))
    return palette


def build_qss(tokens: ThemeTokens) -> str:
    """Generate semantic QSS from tokens. Uses dynamic properties, not object-name sprawl."""
    values = asdict(tokens)
    return """
    /* ==================================================
       CodeParser Theme: {name}
       Generated from ThemeTokens -- do not edit directly
       ================================================== */

    QWidget {{
        color: {text_primary};
        font-family: "Inter", "Segoe UI Variable", "Segoe UI", sans-serif;
        font-size: 14px;
        selection-background-color: {accent};
        selection-color: {text_on_accent};
    }}

    QMainWindow {{
        background: {bg_window};
    }}

    QWidget#windowChromeRoot {{
        background: transparent;
    }}

    /* -- Shell chrome -- */
    QFrame#appSurface,
    QFrame[surface="panel"],
    QFrame#CodeParserPanel,
    QFrame#CodeParserSurface {{
        background: {bg_panel};
        border: 1px solid {border};
        border-radius: {radius_lg}px;
    }}

    QFrame#appSurface[windowState="maximized"] {{
        border-radius: 0px;
    }}

    QFrame[surface="elevated"],
    QFrame#CodeParserInset {{
        background: {bg_elevated};
        border: 1px solid {border};
        border-radius: {radius_lg}px;
    }}

    QWidget#sidebarPanel {{
        background: {bg_panel};
        border: 1px solid {border};
        border-radius: {radius_lg}px;
    }}

    QWidget#titleBar {{
        background: transparent;
    }}

    QLabel#titleLabel {{
        font-size: 14px;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel#titleSubtitle {{
        font-size: 12px;
        color: {text_muted};
    }}

    QLabel#CodeParserTitle {{
        font-size: 24px;
        font-weight: 700;
        color: {text_primary};
    }}

    QLabel#CodeParserMetricLabel,
    QLabel[tone="muted"],
    QLabel#CodeParserEyebrow {{
        color: {text_muted};
    }}

    QLabel#CodeParserEyebrow {{
        font-size: 11px;
        font-weight: 600;
        letter-spacing: 1px;
        text-transform: uppercase;
    }}

    QLabel#CodeParserBody,
    QLabel[tone="secondary"] {{
        color: {text_secondary};
        font-size: 13px;
    }}

    QLabel#CodeParserMetric {{
        color: {text_primary};
        font-size: 18px;
        font-weight: 700;
    }}

    QLabel#sidebarSectionLabel {{
        color: {text_primary};
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.5px;
        text-transform: uppercase;
    }}

    /* -- Window control buttons -- */
    QToolButton#windowControlButton,
    QToolButton#closeButton {{
        min-width: 40px;
        max-width: 40px;
        min-height: 30px;
        max-height: 30px;
        border: none;
        border-radius: {radius_sm}px;
        background: transparent;
        font-family: "Segoe UI Symbol", "Segoe UI", sans-serif;
        font-size: 14px;
        font-weight: 600;
    }}

    QToolButton#windowControlButton:hover {{
        background: {bg_hover};
    }}

    QToolButton#windowControlButton:pressed {{
        background: {bg_elevated};
    }}

    QToolButton#closeButton:hover {{
        background: rgba(248, 81, 73, 0.92);
    }}

    QToolButton#closeButton:pressed {{
        background: rgba(201, 58, 47, 0.96);
    }}

    /* -- Buttons -- */
    QPushButton,
    QToolButton[variant="toolbar"] {{
        min-height: 34px;
        padding: 0 14px;
        background: {bg_panel};
        border: 1px solid {border};
        border-radius: {radius_md}px;
        color: {text_primary};
        font-weight: 600;
    }}

    QPushButton:hover {{
        background: {bg_hover};
        border-color: {border_strong};
    }}

    QPushButton:pressed {{
        background: {bg_elevated};
    }}

    QPushButton:focus {{
        border-color: {accent};
    }}

    QPushButton:disabled {{
        color: {text_muted};
    }}

    QPushButton[variant="primary"] {{
        background: {accent};
        border-color: transparent;
        color: {text_on_accent};
    }}

    QPushButton[variant="primary"]:hover {{
        background: {accent_hover};
    }}

    QPushButton[variant="primary"]:pressed {{
        background: {accent_pressed};
    }}

    QPushButton[variant="danger"] {{
        background: transparent;
        border-color: {danger};
        color: {danger};
    }}

    QPushButton[variant="danger"]:hover {{
        background: {danger};
        color: #ffffff;
    }}

    QPushButton[variant="toolbar"] {{
        background: transparent;
    }}

    QPushButton[variant="ghost"] {{
        min-width: 32px;
        max-width: 32px;
        min-height: 32px;
        max-height: 32px;
        padding: 0;
        background: transparent;
    }}

    QPushButton#sidebarToggleButton:hover {{
        background: {bg_hover};
    }}

    /* -- Inputs -- */
    QLineEdit,
    QPlainTextEdit,
    QTextEdit,
    QComboBox,
    QSpinBox {{
        background: {bg_input};
        border: 1px solid {border};
        border-radius: {radius_md}px;
        padding: 8px 10px;
    }}

    QPlainTextEdit,
    QTextEdit {{
        font-family: "JetBrains Mono", "Cascadia Code", "Fira Code", "Consolas", monospace;
    }}

    QLineEdit:focus,
    QPlainTextEdit:focus,
    QTextEdit:focus,
    QComboBox:focus {{
        border-color: {accent};
    }}

    QComboBox::drop-down {{
        border: none;
        width: 24px;
    }}

    QComboBox QAbstractItemView {{
        background: {bg_panel};
        color: {text_primary};
        border: 1px solid {border};
        selection-background-color: rgba(124, 157, 255, 0.18);
    }}

    /* -- Tree / List views -- */
    QTreeView,
    QListView {{
        background: {bg_input};
        border: 1px solid {border};
        border-radius: {radius_md}px;
        outline: none;
        padding: 4px;
    }}

    QTreeView::item,
    QListView::item {{
        padding: 6px 8px;
        border-radius: {radius_sm}px;
    }}

    QTreeView::item:selected {{
        background: rgba(124, 157, 255, 0.18);
        color: {text_primary};
    }}

    QTreeView::item:hover {{
        background: rgba(124, 157, 255, 0.10);
    }}

    /* -- Tabs -- */
    QTabWidget::pane {{
        border: 1px solid {border};
        background: {bg_panel};
        border-radius: {radius_lg}px;
        top: -1px;
        padding: 4px;
    }}

    QTabBar::tab {{
        min-height: 34px;
        padding: 0 14px;
        margin: 0 4px 0 0;
        background: transparent;
        border: 1px solid transparent;
        border-radius: {radius_md}px;
        color: {text_secondary};
        font-weight: 600;
    }}

    QTabBar::tab:hover {{
        background: rgba(124, 157, 255, 0.08);
        color: {text_primary};
    }}

    QTabBar::tab:selected {{
        background: {bg_panel};
        color: {text_primary};
        border-color: {border};
    }}

    QTabWidget#workbenchTabs::pane {{
        border: none;
        background: transparent;
        padding: 0px;
        margin-top: 8px;
    }}

    QTabWidget#workbenchTabs QTabBar {{
        qproperty-drawBase: 0;
    }}

    QTabWidget#workbenchTabs QTabBar::tab {{
        min-height: 36px;
        padding: 0 16px;
        margin: 0 8px 0 0;
        background: transparent;
        border: 1px solid transparent;
        border-radius: 12px;
        color: {text_secondary};
        font-weight: 600;
    }}

    QTabWidget#workbenchTabs QTabBar::tab:hover:!selected {{
        background: {bg_hover};
        color: {text_primary};
    }}

    QTabWidget#workbenchTabs QTabBar::tab:selected {{
        background: {bg_panel};
        color: {text_primary};
        border-color: {border_strong};
    }}

    /* -- Scrollbars -- */
    QScrollBar:vertical {{
        width: 10px;
        margin: 4px;
        background: transparent;
    }}

    QScrollBar::handle:vertical {{
        min-height: 36px;
        border-radius: 5px;
        background: {border_strong};
    }}

    QScrollBar::handle:vertical:hover {{
        background: {text_muted};
    }}

    QScrollBar::add-line:vertical,
    QScrollBar::sub-line:vertical,
    QScrollBar::add-page:vertical,
    QScrollBar::sub-page:vertical {{
        background: transparent;
        height: 0px;
    }}

    /* -- Splitters -- */
    QSplitter::handle {{
        background: transparent;
    }}

    QSplitter::handle:horizontal {{
        width: 6px;
    }}

    QSplitter::handle:vertical {{
        height: 6px;
    }}

    QSplitter::handle:hover {{
        background: rgba(124, 157, 255, 0.22);
    }}

    /* -- Progress bar -- */
    QProgressBar {{
        min-height: 8px;
        border: none;
        border-radius: 4px;
        background: {bg_elevated};
        text-align: center;
    }}

    QProgressBar::chunk {{
        border-radius: 4px;
        background: {accent};
    }}

    /* -- Tooltips -- */
    QToolTip {{
        background: {bg_elevated};
        color: {text_primary};
        border: 1px solid {border};
        border-radius: 6px;
        padding: 4px 8px;
        font-size: 12px;
    }}

    /* -- Status bar -- */
    QStatusBar {{
        background: {bg_panel};
        color: {text_secondary};
        border-top: 1px solid {border};
        font-size: 12px;
    }}

    QStatusBar::item {{
        border: none;
    }}

    /* -- Semantic properties -- */
    QLabel[tone="secondary"] {{
        color: {text_secondary};
    }}

    QLabel[tone="muted"] {{
        color: {text_muted};
    }}
    """.format(**values)


class ThemeManager(QObject):
    """Theme manager supporting dark, light, and optional system-follow modes."""

    themeChanged = pyqtSignal(object)

    def __init__(self, app: QApplication, settings: QSettings | None = None) -> None:
        super().__init__(app)
        self._app = app
        self._settings = settings or QSettings()
        self._last_contrast_report: dict[str, float] = {}

        raw = str(self._settings.value("theme/mode", ThemeMode.DARK.value))
        self._mode = (
            ThemeMode(raw)
            if raw in ThemeMode._value2member_map_
            else ThemeMode.DARK
        )

        hints = QGuiApplication.styleHints()
        if hasattr(hints, "colorSchemeChanged"):
            hints.colorSchemeChanged.connect(self._on_system_scheme_changed)

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    @property
    def tokens(self) -> ThemeTokens:
        return self._resolve_tokens()

    def set_mode(self, mode: ThemeMode) -> ThemeTokens:
        self._mode = mode
        self._settings.setValue("theme/mode", mode.value)
        return self.apply()

    def apply(self) -> ThemeTokens:
        tokens = self._resolve_tokens()
        self._last_contrast_report = validate_theme_contrast(tokens)
        self._app.setPalette(build_palette(tokens))
        self._app.setStyleSheet(build_qss(tokens))
        self.themeChanged.emit(tokens)
        return tokens

    def _resolve_tokens(self) -> ThemeTokens:
        if self._mode == ThemeMode.DARK:
            return DARK_TOKENS
        if self._mode == ThemeMode.LIGHT:
            return LIGHT_TOKENS
        scheme = QGuiApplication.styleHints().colorScheme()
        return DARK_TOKENS if scheme == Qt.ColorScheme.Dark else LIGHT_TOKENS

    def _on_system_scheme_changed(self, _scheme: Qt.ColorScheme) -> None:
        if self._mode == ThemeMode.SYSTEM:
            self.apply()
