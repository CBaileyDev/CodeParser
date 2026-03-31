from __future__ import annotations

import importlib
from pathlib import Path


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
