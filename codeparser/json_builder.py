from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any, Dict, List

if TYPE_CHECKING:
    from .parser_core import GenerationStats


def build_json(
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats: GenerationStats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    stats_dict: Dict[str, Any] = {"total_files": stats.total_files}
    if stats.total_tokens is not None:
        stats_dict["total_tokens"] = stats.total_tokens
    if stats.secrets_found:
        stats_dict["secrets_found"] = stats.secrets_found

    files_list: List[Dict[str, Any]] = []
    for file_info in sorted(processed_files, key=lambda f: f["path"]):
        entry: Dict[str, Any] = {
            "path": file_info["path"],
            "content": file_info["content"],
            "lines": file_info["lines"],
        }
        if file_info.get("tokens") is not None:
            entry["tokens"] = file_info["tokens"]
        files_list.append(entry)

    payload: Dict[str, Any] = {
        "repository": repository_name,
        "generator": "CodeParser",
        "stats": stats_dict,
        "directory_tree": directory_tree,
        "files": files_list,
    }

    if include_git_logs and git_log_commits:
        payload["git_history"] = git_log_commits

    return json.dumps(payload, indent=2, ensure_ascii=False)
