from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QPlainTextEdit,
    QProgressBar,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..config import CodeParserConfig, apply_preset_to_config
from ..parser_core import generate_xml
from ..remote import RemoteResolutionError, ResolvedTarget, is_github_url, resolve_target
from ..tree_sitter_compressor import is_advanced_compression_available
from .preset_manager import delete_preset, list_preset_names, load_preset, save_preset


DARK_STYLESHEET = """
QWidget {
    background-color: #11161d;
    color: #e7edf5;
    font-size: 13px;
}

QLineEdit, QPlainTextEdit, QComboBox {
    background-color: #18212c;
    color: #e7edf5;
    border: 1px solid #314050;
    border-radius: 6px;
    padding: 6px;
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

QProgressBar {
    background-color: #18212c;
    border: 1px solid #314050;
    border-radius: 6px;
    text-align: center;
}

QProgressBar::chunk {
    background-color: #4b92db;
}
"""


class MainWindow(QMainWindow):
    def __init__(
        self,
        initial_target: str | None = None,
        *,
        auto_generate: bool = False,
        auto_save_initial: bool = True,
    ) -> None:
        super().__init__()
        self.setWindowTitle("CodeParser")
        self.resize(1100, 720)
        self.setAcceptDrops(True)

        self._cached_remote_target: ResolvedTarget | None = None
        self._cached_remote_url: str | None = None
        self._auto_save_initial = auto_save_initial

        self._build_ui(initial_target or str(Path.cwd()))
        self._refresh_presets()
        self.dark_mode_cb.setChecked(True)
        self._on_dark_mode_toggled()
        self._update_token_preview()

        if auto_generate:
            QTimer.singleShot(0, self._generate_initial_output)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------
    def _build_ui(self, initial_target: str) -> None:
        root = QWidget(self)
        self.setCentralWidget(root)

        layout = QVBoxLayout(root)

        target_row = QHBoxLayout()
        target_row.addWidget(QLabel("Target:"))

        self.target_edit = QLineEdit(initial_target)
        self.target_edit.setPlaceholderText(
            "Select a local folder or paste a GitHub repository URL",
        )
        target_row.addWidget(self.target_edit, 1)

        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._on_browse)
        target_row.addWidget(browse_btn)
        layout.addLayout(target_row)

        target_hint = QLabel(
            "Tip: drag a folder onto the window, or enter a GitHub URL like https://github.com/user/repo",
        )
        layout.addWidget(target_hint)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Preset:"))

        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)

        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.clicked.connect(self._on_save_preset)
        preset_row.addWidget(self.save_preset_btn)

        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.clicked.connect(self._on_delete_preset)
        preset_row.addWidget(self.delete_preset_btn)

        self.dark_mode_cb = QCheckBox("Dark theme")
        self.dark_mode_cb.stateChanged.connect(self._on_dark_mode_toggled)
        preset_row.addWidget(self.dark_mode_cb)

        layout.addLayout(preset_row)

        splitter = QSplitter()
        splitter.setOrientation(Qt.Orientation.Vertical)
        layout.addWidget(splitter, 1)

        upper = QWidget()
        upper_layout = QGridLayout(upper)

        self.compress_cb = QCheckBox("Compress code (Tree-sitter)")
        if not is_advanced_compression_available():
            self.compress_cb.setToolTip(
                "Optional Tree-sitter packages are not installed. "
                "CodeParser will fall back to the original source content.",
            )
        self.remove_comments_cb = QCheckBox("Remove comments")
        self.include_git_history_cb = QCheckBox("Include git history")
        self.count_tokens_cb = QCheckBox("Count tokens")
        self.count_tokens_cb.setChecked(True)
        self.secret_scan_cb = QCheckBox("Secret scan")

        upper_layout.addWidget(self.compress_cb, 0, 0)
        upper_layout.addWidget(self.remove_comments_cb, 0, 1)
        upper_layout.addWidget(self.include_git_history_cb, 1, 0)
        upper_layout.addWidget(self.count_tokens_cb, 1, 1)
        upper_layout.addWidget(self.secret_scan_cb, 2, 0)

        self.token_preview_label = QLabel("Live token preview:")
        upper_layout.addWidget(self.token_preview_label, 3, 0, 1, 2)

        self.token_preview_editor = QPlainTextEdit()
        self.token_preview_editor.setReadOnly(True)
        upper_layout.addWidget(self.token_preview_editor, 4, 0, 1, 2)

        upper.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        splitter.addWidget(upper)

        lower = QWidget()
        lower_layout = QVBoxLayout(lower)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        lower_layout.addWidget(self.progress_bar)

        btn_row = QHBoxLayout()
        self.generate_btn = QPushButton("Generate")
        self.generate_btn.clicked.connect(self._on_generate)
        btn_row.addWidget(self.generate_btn)

        btn_row.addStretch(1)

        self.copy_btn = QPushButton("Copy XML")
        self.copy_btn.clicked.connect(self._on_copy_xml)
        self.copy_btn.setEnabled(False)
        btn_row.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save As...")
        self.save_btn.clicked.connect(self._on_save_xml)
        self.save_btn.setEnabled(False)
        btn_row.addWidget(self.save_btn)

        lower_layout.addLayout(btn_row)

        self.output_editor = QPlainTextEdit()
        self.output_editor.setReadOnly(True)
        lower_layout.addWidget(self.output_editor, 1)

        splitter.addWidget(lower)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)

        self.target_edit.textChanged.connect(self._on_target_changed)
        for cb in (
            self.compress_cb,
            self.remove_comments_cb,
            self.include_git_history_cb,
            self.count_tokens_cb,
            self.secret_scan_cb,
        ):
            cb.stateChanged.connect(self._update_token_preview)

    # ------------------------------------------------------------------
    # Drag-and-drop support
    # ------------------------------------------------------------------
    def dragEnterEvent(self, event):  # type: ignore[override]
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if urls:
                local_path = urls[0].toLocalFile()
                if Path(local_path).is_dir():
                    event.acceptProposedAction()
                    return
        event.ignore()

    def dropEvent(self, event):  # type: ignore[override]
        urls = event.mimeData().urls()
        if not urls:
            event.ignore()
            return
        local_path = urls[0].toLocalFile()
        if Path(local_path).is_dir():
            self.target_edit.setText(local_path)
            event.acceptProposedAction()
        else:
            event.ignore()

    # ------------------------------------------------------------------
    # Configuration helpers
    # ------------------------------------------------------------------
    def _release_cached_remote_target(self) -> None:
        if self._cached_remote_target is not None:
            self._cached_remote_target.cleanup()
            self._cached_remote_target = None
            self._cached_remote_url = None

    def _resolve_current_target(self) -> ResolvedTarget:
        target_text = (self.target_edit.text() or ".").strip()
        if is_github_url(target_text):
            if (
                self._cached_remote_target is not None
                and self._cached_remote_url == target_text
            ):
                return self._cached_remote_target

            self._release_cached_remote_target()
            resolved = resolve_target(target_text)
            self._cached_remote_target = resolved
            self._cached_remote_url = target_text
            return resolved

        self._release_cached_remote_target()
        return resolve_target(target_text)

    def _build_config(self, preview: bool = False) -> tuple[CodeParserConfig, ResolvedTarget]:
        resolved = self._resolve_current_target()
        return (
            CodeParserConfig(
                root_path=resolved.root_path,
                display_name=resolved.display_name,
                compress=self.compress_cb.isChecked(),
                remove_comments=self.remove_comments_cb.isChecked(),
                include_git_history=self.include_git_history_cb.isChecked(),
                count_tokens=self.count_tokens_cb.isChecked(),
                secret_scan=self.secret_scan_cb.isChecked(),
                preview_mode=preview,
            ),
            resolved,
        )

    def _default_output_path(self, display_name: str) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", display_name.strip()).strip("-") or "repo"
        return Path.cwd() / f"codeparser-{slug}-{date_str}.xml"

    # ------------------------------------------------------------------
    # Presets
    # ------------------------------------------------------------------
    def _refresh_presets(self) -> None:
        names = list_preset_names()
        self.preset_combo.blockSignals(True)
        self.preset_combo.clear()
        self.preset_combo.addItem("<unsaved>")
        for name in names:
            self.preset_combo.addItem(name)
        self.preset_combo.blockSignals(False)

    def _on_preset_changed(self, index: int) -> None:
        name = self.preset_combo.itemText(index)
        if not name or name == "<unsaved>":
            return
        preset = load_preset(name)
        if not preset:
            return
        config, _resolved = self._build_config(preview=False)
        config = apply_preset_to_config(config, preset)
        self.compress_cb.setChecked(config.compress)
        self.remove_comments_cb.setChecked(config.remove_comments)
        self.include_git_history_cb.setChecked(config.include_git_history)
        self.count_tokens_cb.setChecked(config.count_tokens)
        self.secret_scan_cb.setChecked(config.secret_scan)
        self._update_token_preview()

    def _on_save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if not ok or not name.strip():
            return
        config, _resolved = self._build_config(preview=False)
        save_preset(name.strip(), config)
        self._refresh_presets()
        idx = self.preset_combo.findText(name.strip())
        if idx >= 0:
            self.preset_combo.setCurrentIndex(idx)

    def _on_delete_preset(self) -> None:
        name = self.preset_combo.currentText()
        if not name or name == "<unsaved>":
            return
        delete_preset(name)
        self._refresh_presets()

    # ------------------------------------------------------------------
    # Theme toggle
    # ------------------------------------------------------------------
    def _on_dark_mode_toggled(self) -> None:
        app = QApplication.instance()
        if not app:
            return
        if self.dark_mode_cb.isChecked():
            app.setStyleSheet(DARK_STYLESHEET)
        else:
            app.setStyleSheet("")

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def _on_target_changed(self) -> None:
        self._release_cached_remote_target()
        self._update_token_preview()

    def _on_browse(self) -> None:
        current_text = self.target_edit.text().strip()
        if is_github_url(current_text):
            current = Path.cwd()
        else:
            current = Path(current_text or ".").expanduser().resolve()
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select folder to pack",
            str(current),
        )
        if folder:
            self.target_edit.setText(folder)

    def _update_token_preview(self) -> None:
        try:
            config, _resolved = self._build_config(preview=True)
            _xml_text, stats = generate_xml(config, use_tqdm=False, preview=True)
        except Exception as exc:  # pragma: no cover - GUI only
            self.token_preview_editor.setPlainText(f"Preview error: {exc}")
            return

        lines: list[str] = []
        lines.append(f"Files sampled: {stats.total_files}")
        if stats.total_tokens is not None:
            lines.append(f"Approximate tokens (sample): {stats.total_tokens}")
        if stats.secrets_found:
            lines.append(
                f"Potential secrets flagged in sample: {stats.secrets_found}",
            )
        if is_github_url(self.target_edit.text().strip()):
            lines.append("Source: remote GitHub repository")

        self.token_preview_editor.setPlainText("\n".join(lines) or "No files found.")

    def _generate_xml(self, *, auto_save: bool = False) -> None:
        config, resolved = self._build_config(preview=False)

        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.generate_btn.setEnabled(False)
        QApplication.processEvents()

        try:
            xml_text, stats = generate_xml(config, use_tqdm=False, preview=False)
        finally:
            self.progress_bar.setVisible(False)
            self.generate_btn.setEnabled(True)

        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.output_editor.setPlainText(xml_text)

        summary = f"Generated XML for {stats.total_files} files."
        if stats.total_tokens is not None:
            summary += f" Tokens: {stats.total_tokens}."
        if stats.secrets_found:
            summary += f" Potential secrets: {stats.secrets_found}."
        if config.compress and not is_advanced_compression_available():
            summary += (
                " Tree-sitter compression was unavailable, so CodeParser kept the original source."
            )

        if auto_save:
            output_path = self._default_output_path(
                config.display_name or resolved.display_name,
            )
            output_path.write_text(xml_text, encoding="utf-8")
            summary += f" Auto-saved to {output_path}."

        self.statusBar().showMessage(summary, 15_000)

    def _generate_initial_output(self) -> None:
        try:
            self._generate_xml(auto_save=self._auto_save_initial)
        except Exception as exc:  # pragma: no cover - GUI only
            self.output_editor.setPlainText(f"Initial generation error: {exc}")
            self.statusBar().showMessage(str(exc), 15_000)

    def _on_generate(self) -> None:
        try:
            self._generate_xml(auto_save=False)
        except RemoteResolutionError as exc:  # pragma: no cover - GUI only
            QMessageBox.critical(self, "Error", f"Generation failed:\n{exc}")
        except Exception as exc:  # pragma: no cover - GUI only
            QMessageBox.critical(self, "Error", f"Generation failed:\n{exc}")

    def _on_copy_xml(self) -> None:
        xml = self.output_editor.toPlainText()
        if not xml:
            return
        QApplication.clipboard().setText(xml)

    def _on_save_xml(self) -> None:
        xml = self.output_editor.toPlainText()
        if not xml:
            return
        try:
            config, resolved = self._build_config(preview=False)
            suggested = self._default_output_path(
                config.display_name or resolved.display_name,
            )
        except Exception:
            suggested = self._default_output_path("repo")
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save XML As",
            str(suggested),
            "XML files (*.xml);;All files (*.*)",
        )
        if not path:
            return
        Path(path).write_text(xml, encoding="utf-8")

    def closeEvent(self, event):  # type: ignore[override]
        self._release_cached_remote_target()
        super().closeEvent(event)


def run_gui(initial_target: str | None = None) -> None:
    app = QApplication.instance() or QApplication([])
    window = MainWindow(
        initial_target=initial_target,
        auto_generate=True,
        auto_save_initial=True,
    )
    window.show()
    app.exec()
