from __future__ import annotations

import importlib
from pathlib import Path
import sys
import types


def test_main_runs_cli_for_local_path_and_writes_xml(tmp_path, monkeypatch) -> None:
    sample_root = tmp_path / "sample"
    sample_root.mkdir()
    (sample_root / "README.md").write_text("# Sample\n", encoding="utf-8")

    module = importlib.import_module("main")

    written = {}

    def fake_run_for_root(args, root: Path) -> None:
        written["root"] = root
        written["output"] = args.output

    monkeypatch.setattr(module, "_run_for_root", fake_run_for_root)

    module.main(["--cli", "--path", str(sample_root), "--output", "out.xml"])

    assert written["root"] == sample_root.resolve()
    assert written["output"] == "out.xml"


def test_main_bootstraps_gui_application_and_reads_custom_shell_flag(monkeypatch) -> None:
    module = importlib.import_module("main")
    fake_app = object()
    calls: dict[str, object] = {}

    bootstrap_module = types.SimpleNamespace(
        create_application=lambda argv: calls.setdefault("argv", list(argv)) or fake_app,
        get_use_custom_shell=lambda: True,
    )
    gui_module = types.SimpleNamespace(
        run_gui=lambda **kwargs: calls.update(kwargs),
    )

    monkeypatch.setitem(sys.modules, "codeparser_ui.bootstrap", bootstrap_module)
    monkeypatch.setitem(sys.modules, "codeparser.gui.main_window", gui_module)
    monkeypatch.setattr(module, "_hide_console_window", lambda: None)

    module.main([])

    assert calls["argv"] == []
    assert calls["app"] is fake_app
    assert calls["initial_target"] is None
    assert calls["use_custom_shell"] is True
