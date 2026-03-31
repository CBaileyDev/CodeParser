from __future__ import annotations

from datetime import datetime
from pathlib import Path
import re

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from codeparser_ui.workers.generate_worker import (
    GenerateController,
    GenerateRequest,
    GenerateResult,
    ParserCoreGenerateEngine,
)

from ..config import CodeParserConfig, apply_preset_to_config
from ..parser_core import GenerationStats, generate_xml
from ..remote import RemoteResolutionError, ResolvedTarget, is_github_url, resolve_target
from ..tree_sitter_compressor import is_advanced_compression_available
from .preset_manager import delete_preset, list_preset_names, load_preset, save_preset

__all__ = ["GenerateTab"]


class GenerateTab(QWidget):
    """Primary XML-generation workflow for the desktop shell."""

    def __init__(
        self,
        initial_target: str | None = None,
        *,
        auto_refresh_preview: bool = True,
    ) -> None:
        super().__init__()
        self.setAcceptDrops(True)

        self._cached_remote_target: ResolvedTarget | None = None
        self._cached_remote_url: str | None = None
        self._auto_refresh_preview = auto_refresh_preview
        self._last_output_path: Path | None = None
        self._active_generation_target: ResolvedTarget | None = None
        self._generate_controller = GenerateController(
            ParserCoreGenerateEngine(),
            self,
        )

        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.setInterval(220)
        self._preview_timer.timeout.connect(self._update_token_preview)

        self._build_ui(initial_target or "")
        self._refresh_presets()
        self._sync_ready_state()
        self._generate_controller.busy_changed.connect(self._set_busy)
        self._generate_controller.result_ready.connect(self._on_generation_finished)
        self._generate_controller.error_raised.connect(self._on_generation_failed)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self, initial_target: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(14)

        hero = QFrame(self)
        hero.setObjectName("CodeParserPanel")
        hero.setProperty("surface", "panel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(18, 18, 18, 18)
        hero_layout.setSpacing(12)

        eyebrow = QLabel("GENERATE WORKFLOW", hero)
        eyebrow.setObjectName("CodeParserEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("Pack a repo into Repomix-style XML", hero)
        title.setObjectName("CodeParserTitle")
        title.setWordWrap(True)
        hero_layout.addWidget(title)

        body = QLabel(
            "Choose a local folder or GitHub repository, tune a few packing options, and generate a single AI-friendly XML artifact.",
            hero,
        )
        body.setObjectName("CodeParserBody")
        body.setProperty("tone", "secondary")
        body.setWordWrap(True)
        hero_layout.addWidget(body)

        target_row = QHBoxLayout()
        target_row.setSpacing(10)

        self.target_edit = QLineEdit(initial_target)
        self.target_edit.setPlaceholderText(
            "Select a local folder or paste a GitHub repository URL",
        )
        target_row.addWidget(self.target_edit, 1)

        self.browse_btn = QPushButton("Browse...")
        self.browse_btn.setProperty("variant", "toolbar")
        self.browse_btn.clicked.connect(self._on_browse)
        target_row.addWidget(self.browse_btn)
        hero_layout.addLayout(target_row)

        hint_row = QHBoxLayout()
        hint_row.setSpacing(10)

        self.target_hint = QLabel(
            "Tip: drag a folder onto the window, or paste a GitHub URL such as https://github.com/user/repo",
            hero,
        )
        self.target_hint.setObjectName("CodeParserBody")
        self.target_hint.setProperty("tone", "secondary")
        self.target_hint.setWordWrap(True)
        hint_row.addWidget(self.target_hint, 1)

        self.generate_btn = QPushButton("Generate XML")
        self.generate_btn.setProperty("variant", "primary")
        self.generate_btn.clicked.connect(self._on_generate)
        hint_row.addWidget(self.generate_btn)
        hero_layout.addLayout(hint_row)

        layout.addWidget(hero)

        controls_surface = QFrame(self)
        controls_surface.setObjectName("CodeParserSurface")
        controls_surface.setProperty("surface", "panel")
        controls_layout = QGridLayout(controls_surface)
        controls_layout.setContentsMargins(18, 18, 18, 18)
        controls_layout.setHorizontalSpacing(14)
        controls_layout.setVerticalSpacing(14)

        preset_panel = QFrame(controls_surface)
        preset_panel.setObjectName("CodeParserInset")
        preset_panel.setProperty("surface", "elevated")
        preset_layout = QVBoxLayout(preset_panel)
        preset_layout.setContentsMargins(14, 14, 14, 14)
        preset_layout.setSpacing(8)

        preset_label = QLabel("Presets", preset_panel)
        preset_label.setObjectName("CodeParserMetricLabel")
        preset_layout.addWidget(preset_label)

        preset_row = QHBoxLayout()
        preset_row.setSpacing(8)
        self.preset_combo = QComboBox()
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)

        self.save_preset_btn = QPushButton("Save")
        self.save_preset_btn.setProperty("variant", "toolbar")
        self.save_preset_btn.clicked.connect(self._on_save_preset)
        preset_row.addWidget(self.save_preset_btn)

        self.delete_preset_btn = QPushButton("Delete")
        self.delete_preset_btn.setProperty("variant", "danger")
        self.delete_preset_btn.clicked.connect(self._on_delete_preset)
        preset_row.addWidget(self.delete_preset_btn)
        preset_layout.addLayout(preset_row)

        preset_hint = QLabel(
            "Save a repeatable packing setup for quick reuse.",
            preset_panel,
        )
        preset_hint.setObjectName("CodeParserBody")
        preset_hint.setProperty("tone", "secondary")
        preset_hint.setWordWrap(True)
        preset_layout.addWidget(preset_hint)

        controls_layout.addWidget(preset_panel, 0, 0)

        options_panel = QFrame(controls_surface)
        options_panel.setObjectName("CodeParserInset")
        options_panel.setProperty("surface", "elevated")
        options_layout = QVBoxLayout(options_panel)
        options_layout.setContentsMargins(14, 14, 14, 14)
        options_layout.setSpacing(10)

        options_label = QLabel("Packing options", options_panel)
        options_label.setObjectName("CodeParserMetricLabel")
        options_layout.addWidget(options_label)

        options_grid = QGridLayout()
        options_grid.setHorizontalSpacing(10)
        options_grid.setVerticalSpacing(8)

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

        options_grid.addWidget(self.compress_cb, 0, 0)
        options_grid.addWidget(self.remove_comments_cb, 0, 1)
        options_grid.addWidget(self.include_git_history_cb, 1, 0)
        options_grid.addWidget(self.count_tokens_cb, 1, 1)
        options_grid.addWidget(self.secret_scan_cb, 2, 0)
        options_layout.addLayout(options_grid)

        controls_layout.addWidget(options_panel, 0, 1)

        preview_panel = QFrame(controls_surface)
        preview_panel.setObjectName("CodeParserInset")
        preview_panel.setProperty("surface", "elevated")
        preview_layout = QVBoxLayout(preview_panel)
        preview_layout.setContentsMargins(14, 14, 14, 14)
        preview_layout.setSpacing(8)

        preview_label = QLabel("Live preview", preview_panel)
        preview_label.setObjectName("CodeParserMetricLabel")
        preview_layout.addWidget(preview_label)

        metrics_row = QHBoxLayout()
        metrics_row.setSpacing(10)
        metrics_row.addLayout(self._create_metric_block("Files sampled", "0", "preview_files_value"))
        metrics_row.addLayout(self._create_metric_block("Sample tokens", "0", "preview_tokens_value"))
        metrics_row.addLayout(self._create_metric_block("Source", "Local", "preview_source_value"))
        preview_layout.addLayout(metrics_row)

        self.preview_detail_label = QLabel(
            "Ready to preview the selected target.",
            preview_panel,
        )
        self.preview_detail_label.setObjectName("CodeParserBody")
        self.preview_detail_label.setProperty("tone", "secondary")
        self.preview_detail_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_detail_label)

        controls_layout.addWidget(preview_panel, 1, 0, 1, 2)
        layout.addWidget(controls_surface)

        output_surface = QFrame(self)
        output_surface.setObjectName("CodeParserSurface")
        output_surface.setProperty("surface", "panel")
        output_layout = QVBoxLayout(output_surface)
        output_layout.setContentsMargins(18, 18, 18, 18)
        output_layout.setSpacing(10)

        output_header = QHBoxLayout()
        output_header.setSpacing(10)

        output_title_wrap = QVBoxLayout()
        output_title_wrap.setSpacing(2)

        output_eyebrow = QLabel("XML OUTPUT", output_surface)
        output_eyebrow.setObjectName("CodeParserEyebrow")
        output_title_wrap.addWidget(output_eyebrow)

        output_title = QLabel("Generated package", output_surface)
        output_title.setObjectName("CodeParserTitle")
        output_title_wrap.addWidget(output_title)
        output_header.addLayout(output_title_wrap, 1)

        self.copy_btn = QPushButton("Copy XML")
        self.copy_btn.setProperty("variant", "toolbar")
        self.copy_btn.clicked.connect(self._on_copy_xml)
        self.copy_btn.setEnabled(False)
        output_header.addWidget(self.copy_btn)

        self.save_btn = QPushButton("Save As...")
        self.save_btn.setProperty("variant", "toolbar")
        self.save_btn.clicked.connect(self._on_save_xml)
        self.save_btn.setEnabled(False)
        output_header.addWidget(self.save_btn)

        output_layout.addLayout(output_header)

        self.status_label = QLabel(
            "Ready to pack. Review the target and options above, then generate when you are ready.",
            output_surface,
        )
        self.status_label.setObjectName("CodeParserBody")
        self.status_label.setProperty("tone", "secondary")
        self.status_label.setWordWrap(True)
        output_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        output_layout.addWidget(self.progress_bar)

        self.output_editor = QPlainTextEdit()
        self.output_editor.setReadOnly(True)
        self.output_editor.setPlaceholderText(
            "Your packed XML will appear here after generation.",
        )
        output_layout.addWidget(self.output_editor, 1)

        layout.addWidget(output_surface, 1)

        self.target_edit.textChanged.connect(self._on_target_changed)
        for cb in (
            self.compress_cb,
            self.remove_comments_cb,
            self.include_git_history_cb,
            self.count_tokens_cb,
            self.secret_scan_cb,
        ):
            cb.stateChanged.connect(self._schedule_preview)

    def _has_target(self) -> bool:
        return bool(self.target_edit.text().strip())

    def _sync_ready_state(self) -> None:
        self.generate_btn.setEnabled(self._has_target())
        if self._has_target():
            return
        self.preview_files_value.setText("0")
        self.preview_tokens_value.setText("0")
        self.preview_source_value.setText("Local")
        self.preview_detail_label.setText("Ready to preview the selected target.")

    def _create_metric_block(self, label_text: str, initial_value: str, attr_name: str) -> QVBoxLayout:
        block = QVBoxLayout()
        block.setSpacing(2)

        value_label = QLabel(initial_value, self)
        value_label.setObjectName("CodeParserMetric")
        setattr(self, attr_name, value_label)
        block.addWidget(value_label)

        text_label = QLabel(label_text, self)
        text_label.setObjectName("CodeParserMetricLabel")
        block.addWidget(text_label)

        return block

    # ------------------------------------------------------------------
    # Drag and drop
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
        config, resolved = self._build_config(preview=False)
        try:
            config = apply_preset_to_config(config, preset)
            self.compress_cb.setChecked(config.compress)
            self.remove_comments_cb.setChecked(config.remove_comments)
            self.include_git_history_cb.setChecked(config.include_git_history)
            self.count_tokens_cb.setChecked(config.count_tokens)
            self.secret_scan_cb.setChecked(config.secret_scan)
            self._update_token_preview()
        finally:
            self._cleanup_resolved_target(resolved)

    def _on_save_preset(self) -> None:
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset name:")
        if not ok or not name.strip():
            return
        config, resolved = self._build_config(preview=False)
        try:
            save_preset(name.strip(), config)
            self._refresh_presets()
            idx = self.preset_combo.findText(name.strip())
            if idx >= 0:
                self.preset_combo.setCurrentIndex(idx)
        finally:
            self._cleanup_resolved_target(resolved)

    def _on_delete_preset(self) -> None:
        name = self.preset_combo.currentText()
        if not name or name == "<unsaved>":
            return
        delete_preset(name)
        self._refresh_presets()

    # ------------------------------------------------------------------
    # Target/config helpers
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
                output_path=self._last_output_path,
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

    def _cleanup_resolved_target(self, resolved: ResolvedTarget) -> None:
        if resolved is self._cached_remote_target:
            return
        resolved.cleanup()

    def _default_output_path(self, display_name: str) -> Path:
        date_str = datetime.now().strftime("%Y%m%d")
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", display_name.strip()).strip("-") or "repo"
        return Path.cwd() / f"codeparser-{slug}-{date_str}.xml"

    def _on_target_changed(self) -> None:
        self._release_cached_remote_target()
        self._sync_ready_state()
        if not self._has_target():
            self._preview_timer.stop()
            return
        self._schedule_preview()

    def _schedule_preview(self) -> None:
        if not self._auto_refresh_preview or not self._has_target():
            return
        self._preview_timer.start()

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

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------
    def _update_token_preview(self) -> None:
        if not self._auto_refresh_preview or not self._has_target():
            self._sync_ready_state()
            return

        resolved: ResolvedTarget | None = None
        try:
            config, resolved = self._build_config(preview=True)
            _xml_text, stats = generate_xml(config, use_tqdm=False, preview=True)
        except Exception as exc:  # pragma: no cover - GUI only
            self.preview_files_value.setText("-")
            self.preview_tokens_value.setText("-")
            self.preview_source_value.setText("Error")
            self.preview_detail_label.setText(f"Preview error: {exc}")
            return
        finally:
            if resolved is not None:
                self._cleanup_resolved_target(resolved)

        self.preview_files_value.setText(str(stats.total_files))
        self.preview_tokens_value.setText(
            str(stats.total_tokens) if stats.total_tokens is not None else "Off"
        )
        self.preview_source_value.setText(
            "Remote" if is_github_url(self.target_edit.text().strip()) else "Local"
        )

        details: list[str] = []
        if is_github_url(self.target_edit.text().strip()):
            details.append("Previewing a remote GitHub repository.")
        if stats.secrets_found:
            details.append(f"Potential secrets flagged in sample: {stats.secrets_found}.")
        elif stats.total_files:
            details.append("Preview sampled the current included files successfully.")
        else:
            details.append("No eligible files were found for the current target.")
        self.preview_detail_label.setText(" ".join(details))

    def _set_busy(self, busy: bool) -> None:
        self.progress_bar.setVisible(busy)
        self.generate_btn.setEnabled(not busy and self._has_target())
        self.browse_btn.setEnabled(not busy)
        self.target_edit.setEnabled(not busy)
        self.compress_cb.setEnabled(not busy)
        self.remove_comments_cb.setEnabled(not busy)
        self.include_git_history_cb.setEnabled(not busy)
        self.count_tokens_cb.setEnabled(not busy)
        self.secret_scan_cb.setEnabled(not busy)
        self.preset_combo.setEnabled(not busy)
        self.save_preset_btn.setEnabled(not busy)
        self.delete_preset_btn.setEnabled(not busy)

    def _generate_xml(self) -> tuple[str, GenerationStats]:
        config, resolved = self._build_config(preview=False)
        try:
            return generate_xml(config, use_tqdm=False, preview=False)
        finally:
            self._cleanup_resolved_target(resolved)

    def _build_generate_request(self) -> tuple[GenerateRequest, ResolvedTarget]:
        config, resolved = self._build_config(preview=False)
        request = GenerateRequest(
            source_path=str(config.root_path),
            include_hidden=False,
            include_comments=not config.remove_comments,
            count_tokens=config.count_tokens,
            run_secret_scan=config.secret_scan,
            use_tree_sitter=config.compress,
            config=config,
            use_tqdm=False,
            preview=False,
        )
        return request, resolved

    def _cleanup_active_generation_target(self) -> None:
        if self._active_generation_target is None:
            return
        self._cleanup_resolved_target(self._active_generation_target)
        self._active_generation_target = None

    def _on_generate(self) -> None:
        if not self._has_target():
            self.status_label.setText("Choose a folder or GitHub repository before generating.")
            return
        if self._generate_controller.busy:
            self.status_label.setText("Generation is already in progress.")
            return

        resolved: ResolvedTarget | None = None
        try:
            request, resolved = self._build_generate_request()
        except RemoteResolutionError as exc:  # pragma: no cover - GUI only
            if resolved is not None:
                self._cleanup_resolved_target(resolved)
            QMessageBox.critical(self, "Error", f"Generation failed:\n{exc}")
            self.status_label.setText("Generation failed.")
            return
        except Exception as exc:  # pragma: no cover - GUI only
            if resolved is not None:
                self._cleanup_resolved_target(resolved)
            QMessageBox.critical(self, "Error", f"Generation failed:\n{exc}")
            self.status_label.setText("Generation failed.")
            return

        self.status_label.setText("Generating packed XML...")
        if not self._generate_controller.submit(request):
            self._cleanup_resolved_target(resolved)
            self.status_label.setText("Generation is already in progress.")
            return

        self._active_generation_target = resolved

    def _on_generation_finished(self, result: GenerateResult) -> None:
        self._cleanup_active_generation_target()
        self.copy_btn.setEnabled(True)
        self.save_btn.setEnabled(True)
        self.output_editor.setPlainText(result.xml_text)

        stats = result.stats
        summary = f"Generated XML for {stats.total_files} files."
        if stats.total_tokens is not None:
            summary += f" Tokens: {stats.total_tokens}."
        if stats.secrets_found:
            summary += f" Potential secrets: {stats.secrets_found}."
        if self.compress_cb.isChecked() and not is_advanced_compression_available():
            summary += " Tree-sitter compression was unavailable, so CodeParser kept the original source."
        self.status_label.setText(summary)

    def _on_generation_failed(self, summary: str, _trace: str) -> None:
        self._cleanup_active_generation_target()
        QMessageBox.critical(self, "Error", f"Generation failed:\n{summary}")
        self.status_label.setText("Generation failed.")

    def _on_copy_xml(self) -> None:
        xml = self.output_editor.toPlainText()
        if not xml:
            return
        QApplication.clipboard().setText(xml)
        self.status_label.setText("XML copied to the clipboard.")

    def _on_save_xml(self) -> None:
        xml = self.output_editor.toPlainText()
        if not xml:
            return
        resolved: ResolvedTarget | None = None
        try:
            config, resolved = self._build_config(preview=False)
            suggested = self._default_output_path(
                config.display_name or resolved.display_name,
            )
        except Exception:
            suggested = self._default_output_path("repo")
        finally:
            if resolved is not None:
                self._cleanup_resolved_target(resolved)
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Save XML As",
            str(suggested),
            "XML files (*.xml);;All files (*.*)",
        )
        if not path:
            return
        output_path = Path(path)
        output_path.write_text(xml, encoding="utf-8")
        self._last_output_path = output_path.resolve()
        self.status_label.setText(f"Saved XML to {output_path}.")

    def closeEvent(self, event):  # type: ignore[override]
        if self._generate_controller.busy:
            self.status_label.setText(
                "Generation is still in progress. Wait for it to finish before closing."
            )
            event.ignore()
            return
        self._cleanup_active_generation_target()
        self._release_cached_remote_target()
        super().closeEvent(event)
