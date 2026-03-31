from __future__ import annotations

from PyQt6.QtWidgets import QApplication


CODEPARSER_DARK_STYLESHEET = """
QWidget {
    background-color: #11161d;
    color: #e7edf5;
    font-size: 13px;
}

QMainWindow {
    background: #11161d;
}

QTabWidget::pane {
    border: 1px solid #2b3748;
    border-radius: 12px;
    padding: 4px;
    top: -1px;
}

QTabBar::tab {
    background-color: #18212c;
    color: #aebfd3;
    border: 1px solid #314050;
    border-bottom: none;
    border-top-left-radius: 10px;
    border-top-right-radius: 10px;
    padding: 8px 14px;
    margin-right: 4px;
    min-width: 110px;
}

QTabBar::tab:selected {
    background-color: #203040;
    color: #f2f6fb;
}

QTabBar::tab:hover {
    background-color: #243444;
}

QFrame#CodeParserPanel,
QFrame#CodeParserSurface {
    background-color: #151c25;
    border: 1px solid #2b3748;
    border-radius: 14px;
}

QFrame#CodeParserInset {
    background-color: #18212c;
    border: 1px solid #314050;
    border-radius: 10px;
}

QLineEdit, QPlainTextEdit, QComboBox, QTextEdit, QSpinBox {
    background-color: #18212c;
    color: #e7edf5;
    border: 1px solid #314050;
    border-radius: 6px;
    padding: 6px;
    selection-background-color: #4b92db;
}

QPushButton {
    background-color: #203040;
    color: #f2f6fb;
    border: 1px solid #35506b;
    border-radius: 6px;
    padding: 6px 12px;
}

QPushButton:hover {
    background-color: #29415a;
}

QPushButton#CodeParserPrimaryButton {
    background-color: #4b92db;
    color: #08131f;
    border-color: #66a8eb;
    font-weight: 700;
    padding: 8px 16px;
}

QPushButton#CodeParserPrimaryButton:hover {
    background-color: #67a8ea;
}

QPushButton:disabled {
    background-color: #18212c;
    color: #7f8b98;
    border-color: #2b3748;
}

QLabel#CodeParserEyebrow {
    color: #8ea6be;
    letter-spacing: 1px;
    font-size: 11px;
    text-transform: uppercase;
}

QLabel#CodeParserTitle {
    color: #f2f6fb;
    font-size: 24px;
    font-weight: 700;
}

QLabel#CodeParserBody {
    color: #b8c6d5;
    font-size: 13px;
    line-height: 1.4;
}

QLabel#CodeParserMetric {
    color: #f2f6fb;
    font-size: 18px;
    font-weight: 700;
}

QLabel#CodeParserMetricLabel {
    color: #8ea6be;
    font-size: 11px;
    text-transform: uppercase;
}

QProgressBar {
    background-color: #18212c;
    border: 1px solid #314050;
    border-radius: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4b92db;
}

QCheckBox {
    spacing: 8px;
}
"""


def get_codeparser_dark_stylesheet() -> str:
    return CODEPARSER_DARK_STYLESHEET


def apply_codeparser_dark_theme(app: QApplication) -> None:
    app.setStyleSheet(get_codeparser_dark_stylesheet())
