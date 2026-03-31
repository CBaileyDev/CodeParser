# CodeParser

CodeParser is a standalone, Windows-friendly code packing tool that turns a source tree into a single Repomix-style XML file optimized for LLM consumption.

## Features

- Repomix-compatible XML layout with `<file_summary>`, `<directory_structure>`, `<files>`, and optional `<git_logs>` sections.
- Respect for `.gitignore`, optional `.codeparserignore`, and a set of built-in ignore patterns (binaries, vendor directories, large assets, etc.).
- Token counting via `tiktoken`, using a configurable model name.
- Optional Tree-sitter based structural compression to dramatically reduce token usage while preserving semantics.
- Optional line-comment removal for a further reduction in noise.
- Secret detection with `detect-secrets`.
- Clean, modern PyQt6 GUI:
  - Folder selector (defaults to the current working directory).
  - Checkboxes for compression, comment stripping, git history, token counting, and secret scan.
  - Preset system (save / load profiles).
  - Live token preview based on a sampled subset of files.
  - Generate button with XML viewer, "Copy" and "Save As" actions.
- Headless CLI mode for scripting and automation.

## Installation (development)

1. Install Python 3.12 or later.
2. Clone the repository:

   ```bash
   git clone https://github.com/CBaileyDev/CodeParser.git
   cd CodeParser
   ```

3. Create and activate a virtual environment (recommended):

   ```bash
   python -m venv .venv
   .venv/Scripts/activate  # PowerShell / cmd on Windows
   # or
   source .venv/bin/activate  # WSL / Linux / macOS
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

> Note: `pyinstaller` is not required at runtime and is **not** listed in `requirements.txt`. Install it separately when you want to build the standalone executable:
>
> ```bash
> pip install pyinstaller
> ```

## GUI usage

1. Ensure your current working directory is the project you want to pack.
2. Launch CodeParser (from an environment where the dependencies are installed):

   ```bash
   python main.py
   ```

3. In the GUI:
   - Confirm or change the **Folder** field (defaults to the current working directory).
   - Configure options:
     - **Compress code (Tree-sitter)**
     - **Remove comments**
     - **Include git history** (adds a `<git_logs>` section)
     - **Count tokens** (uses `tiktoken`)
     - **Secret scan** (uses `detect-secrets`)
   - Optionally save or load a **Preset**.
   - Inspect the **Token preview** panel to see an approximate token count based on a sampled subset of files.
   - Click **Generate** to build the full XML.
   - Use **Copy XML** to send the output to the clipboard, or **Save As…** to write it to disk.

The generated XML follows Repomix's XML layout so it can be consumed by tools or prompts expecting Repomix output.

## CLI usage

You can also run CodeParser in headless CLI mode. This is what the final `CodeParser.exe` is expected to support when built with PyInstaller.

Basic usage:

```bash
python main.py --cli --output mycode.xml --compress
```

Available options:

- `--cli` – run in CLI mode instead of launching the GUI.
- `--path / -p` – root directory to pack (defaults to the current working directory).
- `--output / -o` – output XML path (defaults to `<root>/codeparser.xml`).
- `--compress` – enable Tree-sitter based structural compression.
- `--remove-comments` – drop full-line comments in supported languages.
- `--include-git-history` – include a `<git_logs>` section with recent commits.
- `--count-tokens` – count tokens per file using `tiktoken`.
- `--secret-scan` – scan files with `detect-secrets` and include counts in the summary.
- `--model` – model name passed to `tiktoken.encoding_for_model` (default: `gpt-4o-mini`).

Example:

```bash
python main.py --cli -p . -o repo.xml --compress --remove-comments --count-tokens --secret-scan
```

When packaged as `CodeParser.exe` with `--onefile --windowed`, the same options apply:

```bash
CodeParser.exe --cli --output mycode.xml --compress --count-tokens
```

## Ignore rules

CodeParser builds an ignore specification from three sources:

- A built-in set of patterns:
  - `.git/`, `node_modules/`, virtualenvs, `__pycache__/`, common binary extensions, archives, images, media, and office documents.
- The repository's `.gitignore` file, if present.
- An optional `.codeparserignore` file in the root, which uses the same gitwildmatch pattern syntax as `.gitignore`.

All paths are evaluated relative to the selected root folder. Files that are ignored, too large, or detected as binary are skipped.

## Secret scanning

If `detect-secrets` is available and **Secret scan** is enabled, CodeParser:

- Uses `detect_secrets.core.scan.scan_file` to scan each included file.
- Counts the number of potential secrets per file.
- Aggregates the total and surfaces the count in the `<file_summary>/<notes>` section.

This provides a quick, coarse indication of whether sensitive material might have been packed before you share the XML with an external system.

## Tree-sitter compression

When **Compress code (Tree-sitter)** is enabled and `tree-sitter-languages` is installed:

- CodeParser uses Tree-sitter to parse supported languages.
- It keeps imports and high-signal top-level constructs (functions, methods, classes).
- It drops lower-level implementation details when the compressed result is significantly smaller than the original.

If Tree-sitter or language grammars are unavailable, CodeParser falls back gracefully to the original content.

## Building the standalone EXE

To build a single-file, windowed Windows executable using PyInstaller:

```bash
# From the repository root with the virtual environment activated
pip install pyinstaller
pyinstaller CodeParser.spec
```

This will produce a `CodeParser.exe` binary in the `dist/` folder with:

- GUI mode when launched normally (double-click).
- CLI mode when run with `--cli` and other CLI flags.

## License

This project is provided as-is. Refer to the repository for the latest license and usage terms.
