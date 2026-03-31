from __future__ import annotations

import argparse
import ctypes
import sys
from datetime import datetime
from pathlib import Path
import re

from codeparser.config import CodeParserConfig
from codeparser.parser_core import generate_xml
from codeparser.remote import is_github_url, resolve_target
from codeparser.tree_sitter_compressor import is_advanced_compression_available


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CodeParser",
        description="Pack a source tree into a Repomix-style XML file.",
    )
    parser.add_argument(
        "target",
        nargs="?",
        help=(
            "Optional GitHub repository URL (e.g., https://github.com/user/repo) "
            "to shallow-clone and pack."
        ),
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Run in headless CLI mode instead of starting the GUI.",
    )
    parser.add_argument(
        "--path",
        "-p",
        type=str,
        default=None,
        help="Local root folder to pack (defaults to the current working directory).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help=(
            "Output XML file path (defaults to codeparser-[folder]-[date].xml in the "
            "current directory)."
        ),
    )
    parser.add_argument(
        "--compress",
        action="store_true",
        help="Enable Tree-sitter based structural compression.",
    )
    parser.add_argument(
        "--remove-comments",
        action="store_true",
        help="Remove line comments from source files where possible.",
    )
    parser.add_argument(
        "--include-git-history",
        action="store_true",
        help="Include a lightweight <git_logs> section built from recent commits.",
    )
    parser.add_argument(
        "--count-tokens",
        action="store_true",
        help="Count tokens for each file using tiktoken.",
    )
    parser.add_argument(
        "--secret-scan",
        action="store_true",
        help="Scan files for potential secrets using detect-secrets.",
    )
    parser.add_argument(
        "--model",
        type=str,
        default="gpt-4o-mini",
        help="Model name passed to tiktoken.encoding_for_model (default: gpt-4o-mini).",
    )
    return parser


def _slugify_name(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip()).strip("-")
    return slug or "repo"


def _default_output_path_for_name(display_name: str) -> Path:
    date_str = datetime.now().strftime("%Y%m%d")
    return Path.cwd() / f"codeparser-{_slugify_name(display_name)}-{date_str}.xml"


def _run_for_root(args: argparse.Namespace, root: Path) -> None:
    resolved = resolve_target(root)
    try:
        output_path = (
            Path(args.output).resolve()
            if args.output
            else _default_output_path_for_name(resolved.display_name)
        )

        config = CodeParserConfig(
            root_path=resolved.root_path,
            output_path=output_path,
            display_name=resolved.display_name,
            compress=args.compress,
            remove_comments=args.remove_comments,
            include_git_history=args.include_git_history,
            count_tokens=args.count_tokens,
            secret_scan=args.secret_scan,
            model_name=args.model,
        )

        if args.compress and not is_advanced_compression_available():
            print(
                "[CodeParser] Advanced Tree-sitter compression is unavailable; "
                "continuing with the original source content.",
            )

        xml_text, stats = generate_xml(config, use_tqdm=True)
        output_path.write_text(xml_text, encoding="utf-8")

        print(f"[CodeParser] Wrote XML to: {output_path}")
        if resolved.source_url:
            print(f"[CodeParser] Source: {resolved.source_url}")
        if stats.total_tokens is not None:
            print(f"[CodeParser] Total tokens: {stats.total_tokens}")
        if stats.secrets_found:
            print(f"[CodeParser] Potential secrets flagged: {stats.secrets_found}")
    finally:
        resolved.cleanup()


def _run_for_target(args: argparse.Namespace, target: str | Path | None) -> None:
    resolved = resolve_target(target)
    try:
        output_path = (
            Path(args.output).resolve()
            if args.output
            else _default_output_path_for_name(resolved.display_name)
        )

        config = CodeParserConfig(
            root_path=resolved.root_path,
            output_path=output_path,
            display_name=resolved.display_name,
            compress=args.compress,
            remove_comments=args.remove_comments,
            include_git_history=args.include_git_history,
            count_tokens=args.count_tokens,
            secret_scan=args.secret_scan,
            model_name=args.model,
        )

        if args.compress and not is_advanced_compression_available():
            print(
                "[CodeParser] Advanced Tree-sitter compression is unavailable; "
                "continuing with the original source content.",
            )

        xml_text, stats = generate_xml(config, use_tqdm=True)
        output_path.write_text(xml_text, encoding="utf-8")

        print(f"[CodeParser] Wrote XML to: {output_path}")
        if resolved.source_url:
            print(f"[CodeParser] Source: {resolved.source_url}")
        if stats.total_tokens is not None:
            print(f"[CodeParser] Total tokens: {stats.total_tokens}")
        if stats.secrets_found:
            print(f"[CodeParser] Potential secrets flagged: {stats.secrets_found}")
    finally:
        resolved.cleanup()


def run_cli(args: argparse.Namespace) -> None:
    if is_github_url(args.target):
        _run_for_target(args, args.target)
        return

    root = Path(args.path).resolve() if args.path else Path.cwd()
    _run_for_root(args, root)


def _hide_console_window() -> None:
    if sys.platform != "win32":
        return

    kernel32 = ctypes.windll.kernel32
    user32 = ctypes.windll.user32
    console_window = kernel32.GetConsoleWindow()
    if console_window:
        user32.ShowWindow(console_window, 0)


def main(argv: list[str] | None = None) -> None:
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    if args.cli or is_github_url(args.target):
        run_cli(args)
    else:
        # Import PyQt6 GUI lazily so CLI users do not need a Qt-capable environment.
        from codeparser_ui.bootstrap import create_application, get_use_custom_shell
        from codeparser.gui.main_window import run_gui

        _hide_console_window()
        app = create_application(argv or [])
        run_gui(
            initial_target=args.path,
            app=app,
            use_custom_shell=get_use_custom_shell(),
        )


if __name__ == "__main__":
    main(sys.argv[1:])
