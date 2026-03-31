from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict

PRESET_FILE_NAME = "codeparser_presets.json"


@dataclass
class CodeParserConfig:
    """Configuration for a single CodeParser run.

    This configuration is intentionally minimal and focused on the
    options exposed in the GUI and CLI. It is also serializable so it
    can be stored as a user preset.
    """

    root_path: Path
    compress: bool = False
    remove_comments: bool = False
    include_git_history: bool = False
    count_tokens: bool = True
    secret_scan: bool = False
    model_name: str = "gpt-4o-mini"
    max_file_size_bytes: int = 1_000_000  # 1 MB
    preview_mode: bool = False


def get_preset_store_path() -> Path:
    """Return the JSON file used to store presets.

    On Windows, this prefers %APPDATA%/CodeParser. On other platforms,
    it falls back to `~/.config/CodeParser`.
    """

    appdata = os.getenv("APPDATA")
    if appdata:
        base = Path(appdata)
    else:
        base = Path.home() / ".config"

    return base / "CodeParser" / PRESET_FILE_NAME


def load_presets() -> Dict[str, Dict[str, Any]]:
    path = get_preset_store_path()
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    if not isinstance(data, dict):
        return {}
    presets = data.get("presets", {})
    return presets if isinstance(presets, dict) else {}


def save_presets(presets: Dict[str, Dict[str, Any]]) -> None:
    path = get_preset_store_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {"presets": presets}
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def config_to_preset_dict(config: CodeParserConfig) -> Dict[str, Any]:
    data = asdict(config).copy()
    # Do not persist path or preview-only settings.
    data.pop("root_path", None)
    data.pop("preview_mode", None)
    return data


def apply_preset_to_config(
    config: CodeParserConfig, preset: Dict[str, Any]
) -> CodeParserConfig:
    for field, value in preset.items():
        if hasattr(config, field):
            setattr(config, field, value)
    return config
