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
    QLabel,
    QLineEdit,
    QMessageBox,
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

from ..config import CodeParserConfig
from ..output_format import OutputFormat
from ..parser_core import GenerationStats, generate_xml
from ..remote import RemoteResolutionError, ResolvedTarget, is_github_url, resolve_target
from ..tree_sitter_compressor import is_advanced_compression_available

__all__ = ["GenerateTab"]


class GenerateTab(QWidget):
    """Primary generation workflow for the desktop shell."""

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
        self._sync_ready_state()
        self._generate_controller.busy_changed.connect(self._set_busy)
        self._generate_controller.result_ready.connect(self._on_generation_finished)
        self._generate_controller.error_raised.connect(self._on_generation_failed)

    # ------------------------------------------------------------------
    # UI
    # ------------------------------------------------------------------
    def _build_ui(self, initial_target: str) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # -- Hero panel --
        hero = QFrame(self)
        hero.setObjectName("CodeParserPanel")
        hero.setProperty("surface", "panel")
        hero_layout = QVBoxLayout(hero)
        hero_layout.setContentsMargins(20, 20, 20, 20)
        hero_layout.setSpacing(12)

        eyebrow = QLabel("GENERATE WORKFLOW", hero)
        eyebrow.setObjectName("CodeParserEyebrow")
        hero_layout.addWidget(eyebrow)

        title = QLabel("Pack a repo into an AI-ready file", hero)
        title.setObjectName("CodeParserTitle")
        title.setWordWrap(True)
        hero_layout.addWidget(title)

        body = QLabel(
            "Choose a local folder or GitHub repository, pick an output format, and generate a single packed file.",
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

        hint = QLabel(
            "Tip: drag a folder onto the window, or paste a GitHub URL such as https://github.com/user/repo",
            hero,
        )
        hint.setObjectName("CodeParserBody")
        hint.setProperty("tone", "secondary")
        hint.setWordWrap(True)
        hero_layout.addWidget(hint)

        layout.addWidget(hero)

        # -- Options panel --
        options_surface = QFrame(self)
        options_surface.setObjectName("CodeParserSurface")
        options_surface.setProperty("surface", "panel")
        options_layout = QVBoxLayout(options_surface)
        options_layout.setContentsMargins(20, 16, 20, 16)
        options_layout.setSpacing(12)

        options_header = QLabel("PACKING OPTIONS", options_surface)
        options_header.setObjectName("CodeParserEyebrow")
        options_layout.addWidget(options_header)

        options_grid = QGridLayout()
        options_grid.setHorizontalSpacing(20)
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
        options_grid.addWidget(self.include_git_history_cb, 0, 2)
        options_grid.addWidget(self.count_tokens_cb, 1, 0)
        options_grid.addWidget(self.secret_scan_cb, 1, 1)
        options_layout.addLayout(options_grid)

        action_row = QHBoxLayout()
        action_row.setSpacing(10)

        format_label = QLabel("Output format:", options_surface)
        format_label.setObjectName("CodeParserBody")
        action_row.addWidget(format_label)

        self.format_combo = QComboBox(options_surface)
        self.format_combo.setAccessibleName("Output format selector")
        for fmt in OutputFormat:
            self.format_combo.addItem(fmt.display_name, fmt)
        md_index = self.format_combo.findData(OutputFormat.MARKDOWN)
        if md_index >= 0:
            self.format_combo.setCurrentIndex(md_index)
        action_row.addWidget(self.format_combo)

        action_row.addStretch(1)

        self.generate_btn = QPushButton("Generate")
        self.generate_btn.setProperty("variant", "primary")
        self.generate_btn.clicked.connect(self._on_generate)
        action_row.addWidget(self.generate_btn)

        options_layout.addLayout(action_row)
        layout.addWidget(options_surface)

        # -- Live preview metrics (compact) --
        preview_surface = QFrame(self)
        preview_surface.setObjectName("CodeParserSurface")
        preview_surface.setProperty("surface", "panel")
        preview_layout = QHBoxLayout(preview_surface)
        preview_layout.setContentsMargins(20, 14, 20, 14)
        preview_layout.setSpacing(20)

        preview_layout.addLayout(self._create_metric_block("Files", "0", "preview_files_value"))
        preview_layout.addLayout(self._create_metric_block("Tokens", "0", "preview_tokens_value"))
        preview_layout.addLayout(self._create_metric_block("Source", "Local", "preview_source_value"))

        self.preview_detail_label = QLabel("Ready to preview.", preview_surface)
        self.preview_detail_label.setObjectName("CodeParserBody")
        self.preview_detail_label.setProperty("tone", "secondary")
        self.preview_detail_label.setWordWrap(True)
        preview_layout.addWidget(self.preview_detail_label, 1)

        layout.addWidget(preview_surface)

        # -- Progress bar (hidden by default) --
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # -- Success banner (hidden by default) --
        self.success_banner = QFrame(self)
        self.success_banner.setObjectName("CodeParserSurface")
        self.success_banner.setProperty("surface", "elevated")
        self.success_banner.setVisible(False)
        banner_layout = QVBoxLayout(self.success_banner)
        banner_layout.setContentsMargins(20, 16, 20, 16)
        banner_layout.setSpacing(10)

        self.banner_title = QLabel("Generation complete", self.success_banner)
        self.banner_title.setObjectName("CodeParserTitle")
        self.banner_title.setStyleSheet("font-size: 18px;")
        banner_layout.addWidget(self.banner_title)

        self.status_label = QLabel("", self.success_banner)
        self.status_label.setObjectName("CodeParserBody")
        self.status_label.setProperty("tone", "secondary")
        self.status_label.setWordWrap(True)
        banner_layout.addWidget(self.status_label)

        banner_actions = QHBoxLayout()
        banner_actions.setSpacing(10)

        self.open_folder_btn = QPushButton("Open folder")
        self.open_folder_btn.setProperty("variant", "toolbar")
        self.open_folder_btn.clicked.connect(self._on_open_output_folder)
        self.open_folder_btn.setVisible(False)
        banner_actions.addWidget(self.open_folder_btn)

        self.copy_path_btn = QPushButton("Copy path")
        self.copy_path_btn.setProperty("variant", "toolbar")
        self.copy_path_btn.clicked.connect(self._on_copy_output_path)
        self.copy_path_btn.setVisible(False)
        banner_actions.addWidget(self.copy_path_btn)

        banner_actions.addStretch(1)
        banner_layout.addLayout(banner_actions)

        layout.addWidget(self.success_banner)
        layout.addStretch(1)

        # -- Connections --
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
        self.preview_detail_label.setText("Ready to preview.")

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
        selected_format = self.format_combo.currentData()
        if not isinstance(selected_format, OutputFormat):
            selected_format = OutputFormat.XML
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
                output_format=selected_format,
                preview_mode=preview,
            ),
            resolved,
        )

    def _cleanup_resolved_target(self, resolved: ResolvedTarget) -> None:
        if resolved is self._cached_remote_target:
            return
        resolved.cleanup()

    def _default_output_path(self, display_name: str, fmt: OutputFormat | None = None) -> Path:
        if fmt is None:
            fmt = OutputFormat.XML
        date_str = datetime.now().strftime("%Y%m%d")
        slug = re.sub(r"[^A-Za-z0-9._-]+", "-", display_name.strip()).strip("-") or "repo"
        dist_dir = Path.cwd() / "dist"
        return dist_dir / f"codeparser-{slug}-{date_str}{fmt.extension}"

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
        self.format_combo.setEnabled(not busy)
        if busy:
            self.success_banner.setVisible(False)

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

        self.status_label.setText("Generating packed output...")
        if not self._generate_controller.submit(request):
            self._cleanup_resolved_target(resolved)
            self.status_label.setText("Generation is already in progress.")
            return

        self._active_generation_target = resolved

    def _on_generation_finished(self, result: GenerateResult) -> None:
        self._cleanup_active_generation_target()
        self.banner_title.setText("Generation complete")

        stats = result.stats
        selected_format = self.format_combo.currentData()
        if not isinstance(selected_format, OutputFormat):
            selected_format = OutputFormat.XML

        # Auto-save to dist/ folder
        try:
            config, resolved = self._build_config(preview=False)
            display_name = config.display_name or resolved.display_name
            self._cleanup_resolved_target(resolved)
        except Exception:
            display_name = "repo"

        output_path = self._default_output_path(display_name, selected_format)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(result.xml_text, encoding="utf-8")
        self._last_output_path = output_path.resolve()

        # Show success banner
        summary = f"Saved to {output_path}"
        if stats.total_tokens is not None:
            summary += f"  |  {stats.total_files} files  |  {stats.total_tokens} tokens"
        else:
            summary += f"  |  {stats.total_files} files"
        if stats.secrets_found:
            summary += f"  |  {stats.secrets_found} potential secrets"
        if self.compress_cb.isChecked() and not is_advanced_compression_available():
            summary += "  |  Tree-sitter unavailable, kept original source"

        self.status_label.setText(summary)
        self.success_banner.setVisible(True)
        self.open_folder_btn.setVisible(True)
        self.copy_path_btn.setVisible(True)

    def _on_generation_failed(self, summary: str, _trace: str) -> None:
        self._cleanup_active_generation_target()
        self.success_banner.setVisible(True)
        self.banner_title.setText("Generation failed")
        self.status_label.setText(summary)
        self.open_folder_btn.setVisible(False)
        self.copy_path_btn.setVisible(False)

    # ------------------------------------------------------------------
    # Banner actions
    # ------------------------------------------------------------------
    def _on_open_output_folder(self) -> None:
        if self._last_output_path and self._last_output_path.parent.exists():
            import subprocess
            import sys
            if sys.platform == "win32":
                subprocess.Popen(["explorer", "/select,", str(self._last_output_path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", "-R", str(self._last_output_path)])
            else:
                subprocess.Popen(["xdg-open", str(self._last_output_path.parent)])

    def _on_copy_output_path(self) -> None:
        if self._last_output_path:
            QApplication.clipboard().setText(str(self._last_output_path))
            self.status_label.setText(f"Path copied: {self._last_output_path}")

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
