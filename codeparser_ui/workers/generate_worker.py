"""generate_worker.py -- QThreadPool-based generation controller.

Replaces QApplication.processEvents() anti-pattern. Workers never touch widgets.
"""

from __future__ import annotations

import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Protocol

from PyQt6.QtCore import QObject, QRunnable, QThreadPool, pyqtSignal

from codeparser.config import CodeParserConfig
from codeparser.parser_core import generate_xml


@dataclass(frozen=True)
class GenerateRequest:
    source_path: str
    include_hidden: bool
    include_comments: bool
    count_tokens: bool
    run_secret_scan: bool
    use_tree_sitter: bool
    config: CodeParserConfig | None = None
    use_tqdm: bool = False
    preview: bool = False


@dataclass(frozen=True)
class GenerateResult:
    xml_text: str
    stats: Any
    output_path: str | None = None


class GeneratorEngine(Protocol):
    """Protocol for the parser core. Keep UI-agnostic."""

    def generate_xml(self, request: GenerateRequest) -> GenerateResult: ...


class ParserCoreGenerateEngine:
    """Adapter that maps a GenerateRequest onto the existing parser core."""

    def generate_xml(self, request: GenerateRequest) -> GenerateResult:
        config = request.config or CodeParserConfig(
            root_path=Path(request.source_path),
            compress=request.use_tree_sitter,
            remove_comments=not request.include_comments,
            count_tokens=request.count_tokens,
            secret_scan=request.run_secret_scan,
        )
        xml_text, stats = generate_xml(
            config,
            use_tqdm=request.use_tqdm,
            preview=request.preview,
        )
        return GenerateResult(xml_text=xml_text, stats=stats)


class _Signals(QObject):
    finished = pyqtSignal(object)
    failed = pyqtSignal(str, str)


class _GenerateTask(QRunnable):
    def __init__(self, engine: GeneratorEngine, request: GenerateRequest) -> None:
        super().__init__()
        self.setAutoDelete(True)
        self._engine = engine
        self._request = request
        self.signals = _Signals()

    def run(self) -> None:
        try:
            result = self._engine.generate_xml(self._request)
        except Exception as exc:  # pragma: no cover - exercised by UI error handling
            self.signals.failed.emit(str(exc), traceback.format_exc())
            return
        self.signals.finished.emit(result)


class GenerateController(QObject):
    """
    Submits generation work to QThreadPool and emits results on the main thread.

    Usage:
        controller = GenerateController(engine)
        controller.result_ready.connect(self.on_xml_ready)
        controller.error_raised.connect(self.on_error)
        controller.submit(request)
    """

    busy_changed = pyqtSignal(bool)
    result_ready = pyqtSignal(object)
    error_raised = pyqtSignal(str, str)

    def __init__(self, engine: GeneratorEngine, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._engine = engine
        self._pool = QThreadPool.globalInstance()
        self._busy = False

    @property
    def busy(self) -> bool:
        return self._busy

    def submit(self, request: GenerateRequest) -> bool:
        if self._busy:
            return False

        task = _GenerateTask(self._engine, request)
        task.signals.finished.connect(self._on_finished)
        task.signals.failed.connect(self._on_failed)

        self._busy = True
        self.busy_changed.emit(True)
        self._pool.start(task)
        return True

    def _on_finished(self, result: GenerateResult) -> None:
        self._busy = False
        self.busy_changed.emit(False)
        self.result_ready.emit(result)

    def _on_failed(self, summary: str, trace: str) -> None:
        self._busy = False
        self.busy_changed.emit(False)
        self.error_raised.emit(summary, trace)
