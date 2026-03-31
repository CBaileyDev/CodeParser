from __future__ import annotations

from typing import Any, Dict, List

from ..config import CodeParserConfig, config_to_preset_dict, load_presets, save_presets


def list_preset_names() -> List[str]:
    presets = load_presets()
    return sorted(presets.keys())


def load_preset(name: str) -> Dict[str, Any] | None:
    presets = load_presets()
    return presets.get(name)


def save_preset(name: str, config: CodeParserConfig) -> None:
    presets = load_presets()
    presets[name] = config_to_preset_dict(config)
    save_presets(presets)


def delete_preset(name: str) -> None:
    presets = load_presets()
    if name in presets:
        del presets[name]
        save_presets(presets)
