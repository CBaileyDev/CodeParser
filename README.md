# CodeParser

CodeParser is a standalone, Windows-friendly code packing tool that turns a source tree (local or remote) into a single Repomix-style XML file optimized for LLM consumption.

## Features

- **Repomix-compatible XML output**
  - `<file_summary>` section with purpose, format description, basic statistics, and notes.
  - `<directory_structure>` section with an indented view of the packed paths.
  - `<files>` section with `<file path="…">…</file>` entries for each included file.
  - Optional `<git_logs>` section with recent commits when enabled.
- **Local and remote repositories**
  - Pack any local folder.
  - Or call `CodeParser.exe https://github.com/user/repo` to shallow-clone and pack a remote GitHub repository (similar to Repomix’s remote support).[cite:7]
- **Robust ignore handling**
  - Built-in ignore patterns for VCS folders, virtualenvs, `node_modules`, build artifacts, binaries, media, and common large assets.[cite:5]
  - Automatic support for `.gitignore` and optional `.codeparserignore` in the project root.
- **Token-aware content**
  - Token counting via `tiktoken`, with configurable model name (default: `gpt-4o-mini`).
  - Approximate token metrics surfaced in `<file_summary>/<notes>`.
- **Optional structural compression**
  - Tree-sitter powered compression via `tree_sitter_languages`, keeping imports and top-level symbols while eliding low-level implementation details when this yields a significant size reduction.[cite:9]
- **Security-aware scanning**
  - Optional secret detection via `detect-secrets`, with a count of potential secrets included in the summary.[cite:5]
- **Modern PyQt6 GUI**
  - Folder selector (default = current working directory) with drag-and-drop support.
  - Checkboxes: Compress code, Remove comments, Include git history, Count tokens, Secret scan.
  - Preset system (save / load profiles) stored per-user.
  - Live token preview panel based on a sampled subset of files.
  - Generate button with progress indicator, XML viewer, Copy to Clipboard, and Save As.
  - Light / dark theme toggle.
- **Headless CLI**
  - Fully scriptable CLI, including GitHub URL support and remote cloning.
- **First-class Windows support**
  - Single-file `CodeParser.exe` built via PyInstaller.
  - GitHub Actions workflow that builds and attaches the latest EXE to a GitHub Release on each push to `main`.

## Usage

### GUI mode

1. Ensure your current working directory is the project you want to pack.
2. Launch CodeParser from a Python environment with the dependencies installed:

   ```bash
   python main.py
   ```

3. In the GUI:
   - **Folder** – confirm or change the folder to pack (defaults to the current working directory). You can also drag-and-drop a folder from your file manager onto the window.
   - Configure options via checkboxes:
     - **Compress code (Tree-sitter)** – enable structural compression for supported languages.
     - **Remove comments** – drop full-line comments in common languages.
     - **Include git history** – add a `<git_logs>` section with recent commits.
     - **Count tokens** – estimate token counts via `tiktoken`.
     - **Secret scan** – run `detect-secrets` across included files and surface counts.[cite:5]
   - Optionally save or load a **Preset** using the presets dropdown.
   - Use the **Token preview** panel to see an approximate token count over a small sample of files.
   - Click **Generate** to build the full XML.
   - Use **Copy XML** to send the output to the clipboard, or **Save As…** to write it to disk.

The default suggested output file name is:

```text
codeparser-[foldername]-[YYYYMMDD].xml
```

For example, packing `my-app/` on 2026‑03‑31 produces `codeparser-my-app-20260331.xml`.

### CLI mode

You can also run CodeParser in headless CLI mode. This is the same interface used by the packaged `CodeParser.exe`.

Basic usage (local folder):

```bash
python main.py --cli --path . --compress --count-tokens --secret-scan
```

GitHub URL support (remote repo):

```bash
# Clone and pack a remote GitHub repository in one step
CodeParser.exe https://github.com/user/repo --cli --compress --count-tokens
```

When a GitHub URL is provided as the first positional argument:

- CodeParser performs a shallow clone (`git clone --depth=1`).
- The cloned repository becomes the root for analysis.
- The default output file name still follows `codeparser-[reponame]-[YYYYMMDD].xml`, written into the current working directory.

CLI options:

- `--cli` – run in CLI mode instead of launching the GUI.
- `--path / -p` – local root directory to pack (ignored when a GitHub URL is provided).
- `--output / -o` – output XML file path (defaults to `codeparser-[folder]-[date].xml` in the current directory).
- `--compress` – enable Tree-sitter based structural compression.
- `--remove-comments` – drop full-line comments for supported languages.
- `--include-git-history` – include `<git_logs>` with recent commit metadata.
- `--count-tokens` – count tokens via `tiktoken`.
- `--secret-scan` – enable `detect-secrets` scanning.
- `--model` – model name passed to `tiktoken.encoding_for_model` (default: `gpt-4o-mini`).

Example (local repo):

```bash
python main.py --cli -p . -o repo.xml --compress --remove-comments --count-tokens --secret-scan
```

Example (remote GitHub repo):

```bash
CodeParser.exe https://github.com/yamadashy/repomix --cli --compress --count-tokens
```

> Note: Remote URL support requires `git` to be available on the system `PATH`.

## How to build

### Development setup

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

### Manual EXE build (local)

To build a single-file, windowed Windows executable using PyInstaller:

```bash
pip install pyinstaller
python tools/generate_icon.py  # optional, generates assets/codeparser.ico
pyinstaller CodeParser.spec
```

The build will produce `dist/CodeParser.exe`.

- Launch it normally (double-click) for GUI mode.
- Use `CodeParser.exe --cli` and other CLI flags for headless mode.

## Download latest EXE

On every push to the `main` branch, a GitHub Actions workflow:

- Installs dependencies.
- Generates a simple folder/code icon.
- Builds a single-file `CodeParser.exe` via PyInstaller and the project spec.
- Publishes it as an asset on a `latest` GitHub Release.

You can always download the most recent EXE from:

- **Release page:** https://github.com/CBaileyDev/CodeParser/releases/tag/latest
- **Direct EXE link:** https://github.com/CBaileyDev/CodeParser/releases/download/latest/CodeParser.exe

The link will become valid after the first successful CI run on `main`.

## Comparison to Repomix

Repomix is a CLI tool that packs your repository into a single, AI-friendly file and supports multiple output formats, including an XML layout with `<file_summary>`, `<directory_structure>`, and `<files>` sections.[cite:6][cite:7]

CodeParser is designed to be at least as capable while being more Windows-friendly and GUI-focused:

- **Standalone EXE vs. Node-based CLI**
  - Repomix is a Node/TypeScript CLI that you install via `npm`.
  - CodeParser is a single `CodeParser.exe` built with PyInstaller, ideal for Windows users who prefer a binary over a Node toolchain.
- **GUI experience**
  - Repomix is primarily CLI-driven.[cite:6]
  - CodeParser adds a PyQt6 GUI with drag-and-drop folder selection, presets, dark mode, and live token previews.
- **Remote repo support**
  - Both tools support GitHub URLs; CodeParser mirrors Repomix’s ability to clone and pack remote repositories via a single command.[cite:6]
- **Token and security awareness**
  - Repomix focuses on packing and content formatting.[cite:6]
  - CodeParser includes integrated token counting via `tiktoken` and optional secret scanning via `detect-secrets` so you can quickly gauge size and risk before sharing the XML.
- **Tree-sitter compression**
  - Repomix supports Tree-sitter-based compression to reduce token counts.[cite:6][cite:7]
  - CodeParser offers a similar optional compression path using `tree_sitter_languages`, tuned to keep imports and high-signal definitions while shrinking implementation noise.
- **Automated Windows releases**
  - CodeParser ships with a GitHub Actions workflow that continuously builds and publishes a ready-to-run EXE on every push to `main`.

If you already use Repomix, CodeParser should feel familiar in terms of XML structure and remote support, while giving you a richer, Windows-native GUI workflow.
