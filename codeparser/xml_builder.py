from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .parser_core import GenerationStats


def _format_notes(stats: GenerationStats) -> str:
    lines: List[str] = [
        "- Some files may have been excluded based on .gitignore, .codeparserignore, and CodeParser's configuration",
        "- Binary files are not included in this packed representation. Please refer to the Repository Structure section for a complete list of file paths, including binary files",
        "- Files matching patterns in .gitignore are excluded",
        "- Files matching patterns in .codeparserignore are excluded",
        "- Files matching default ignore patterns are excluded",
        f"- Total files included: {stats.total_files}",
    ]
    if stats.total_tokens is not None:
        lines.append(f"- Approximate total tokens: {stats.total_tokens}")
    if stats.secrets_found:
        lines.append(
            f"- Potential secrets flagged by detect-secrets: {stats.secrets_found}",
        )
    return "\n".join(lines)


def build_repomix_xml(
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats: GenerationStats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    """Build a Repomix-style XML document.

    The structure mirrors Repomix's `xmlStyle.ts` template so that tools
    expecting Repomix output can consume CodeParser output directly.
    """

    notes = _format_notes(stats)

    parts: List[str] = []

    parts.append(
        "This file is a merged representation of the entire codebase, combined into a single document by CodeParser.\n\n",
    )

    parts.append(
        "<file_summary>\n"
        "This section contains a summary of this file.\n\n"
        "<purpose>\n"
        "This file contains a packed representation of the entire repository's contents.\n"
        "It is designed to be easily consumable by AI systems for analysis, code review,\n"
        "or other automated processes.\n"
        "</purpose>\n\n"
        "<file_format>\n"
        "The content is organized as follows:\n"
        "1. This summary section\n"
        "2. Repository information\n"
        "3. Directory structure\n"
        "4. Repository files (if enabled)\n"
        "5. Multiple file entries, each consisting of:\n"
        "  - File path as an attribute\n"
        "  - Full contents of the file\n"
        "</file_format>\n\n"
        "<usage_guidelines>\n"
        "- This file should be treated as read-only. Any changes should be made to the\n"
        "  original repository files, not this packed version.\n"
        "- When processing this file, use the file path to distinguish\n"
        "  between different files in the repository.\n"
        "- Be aware that this file may contain sensitive information. Handle it with\n"
        "  the same level of security as you would the original repository.\n"
        "- Pay special attention to the Repository Description. These contain important context and guidelines specific to this project.\n"
        "</usage_guidelines>\n\n"
        "<notes>\n"
        f"{notes}\n"
        "</notes>\n\n"
        "</file_summary>\n\n",
    )

    parts.append("<user_provided_header>\n")
    parts.append(f"This repository is {repository_name}\n")
    parts.append("</user_provided_header>\n\n")

    parts.append("<directory_structure>\n")
    parts.append(directory_tree)
    parts.append("\n</directory_structure>\n\n")

    parts.append("<files>\n")
    parts.append("This section contains the contents of the repository's files.\n\n")

    for file_info in sorted(processed_files, key=lambda f: f["path"]):
        path = file_info["path"]
        content = file_info["content"]
        parts.append(f"<file path=\"{path}\">\n")
        parts.append(content)
        parts.append("\n</file>\n\n")

    parts.append("</files>\n")

    # Optional git logs
    if include_git_logs and git_log_commits:
        parts.append("<git_logs>\n")
        for commit in git_log_commits:
            parts.append("<git_log_commit>\n")
            parts.append(f"<date>{commit.get('date', '')}</date>\n")
            parts.append(f"<message>{commit.get('message', '')}</message>\n")
            parts.append("<files>\n")
            for f in commit.get("files", []):
                parts.append(f"{f}\n")
            parts.append("</files>\n")
            parts.append("</git_log_commit>\n")
        parts.append("</git_logs>\n")

    return "".join(parts)
