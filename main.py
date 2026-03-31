from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

from codeparser.config import CodeParserConfig
from codeparser.parser_core import GenerationStats, generate_xml


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


def _is_github_url(value: str | None) -> bool:
    if not value:
        return False
    return value.startswith("https://github.com/") or value.startswith("http://github.com/")


def _default_output_path_for_root(root: Path) -> Path:
    folder = root.name or "repo"
    date_str = datetime.now().strftime("%Y%m%d")
    return Path.cwd() / f"codeparser-{folder}-{date_str}.xml"


def _run_for_root(args: argparse.Namespace, root: Path) -> None:
    output_path = (
        Path(args.output).resolve()
        if args.output
        else _default_output_path_for_root(root)
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


def run_cli(args: argparse.Namespace) -> None:
    # GitHub URL positional argument takes precedence over --path.
    if _is_github_url(args.target):
        with tempfile.TemporaryDirectory(prefix="codeparser-") as tmpdir:
            clone_dir = Path(tmpdir) / "repo"
            print(f"[CodeParser] Cloning {args.target} into {clone_dir} (shallow clone)...")
            try:
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        args.target,
                        str(clone_dir),
                    ],
                    check=True,
                )
            except (OSError, subprocess.CalledProcessError) as exc:
                print(f"[CodeParser] Failed to clone repository: {exc}")
                return

            _run_for_root(args, clone_dir)
    else:
        root = Path(args.path).resolve() if args.path else Path.cwd()
        _run_for_root(args, root)


def main(argv: list[str] | None = None) -> None:
    parser = build_cli_parser()
    args = parser.parse_args(argv)

    if args.cli or _is_github_url(args.target):
        run_cli(args)
    else:
        # Import PyQt6 GUI lazily so CLI users do not need a Qt-capable environment.
        from codeparser.gui.main_window import run_gui

        run_gui()


if __name__ == "__main__":
    main(sys.argv[1:])
