from __future__ import annotations

import argparse
import sys
from pathlib import Path

from codeparser.config import CodeParserConfig
from codeparser.parser_core import GenerationStats, generate_xml


def build_cli_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="CodeParser",
        description="Pack a source tree into a Repomix-style XML file.",
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
        help="Root folder to pack (defaults to the current working directory).",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        default=None,
        help="Output XML file path (defaults to <root>/codeparser.xml).",
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


def run_cli(args: argparse.Namespace) -> None:
    root = Path(args.path).resolve() if args.path else Path.cwd()
    output_path = (
        Path(args.output).resolve()
        if args.output
        else root / "codeparser.xml"
    )

    config = CodeParserConfig(
        root_path=root,
        compress=args.compress,
        remove_comments=args.remove_comments,
        include_git_history=args.include_git_history,
        count_tokens=args.count_tokens,
        secret_scan=args.secret_scan,
        model_name=args.model,
    )

    xml_text, stats = generate_xml(config, use_tqdm=True)
    output_path.write_text(xml_text, encoding="utf-8")

    print(f"[CodeParser] Wrote XML to: {output_path}")
    if stats.total_tokens is not None:
        print(f"[CodeParser] Total tokens: {stats.total_tokens}")
    if stats.secrets_found:
        print(f"[CodeParser] Potential secrets flagged: {stats.secrets_found}")


def main(argv: list[str] | None = None) -> None:
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    if args.cli:
        run_cli(args)
    else:
        # Import PyQt6 GUI lazily so CLI users do not need a Qt-capable environment.
        from codeparser.gui.main_window import run_gui

        run_gui()


if __name__ == "__main__":
    main(sys.argv[1:])
