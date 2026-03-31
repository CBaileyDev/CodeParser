# CodeParser

CodeParser is a Windows-first repository packer that turns a local folder or GitHub repository URL into a Repomix-style XML file for LLM workflows. It ships as a PyQt6 desktop app, supports CLI automation, respects `.gitignore` and `.codeparserignore`, and can be packaged into a single `CodeParser.exe`.

## Features

- Repomix-style XML output with `<file_summary>`, `<user_provided_header>`, `<directory_structure>`, `<files>`, and optional `<git_logs>`.
- Double-click friendly GUI that starts in dark mode, previews the current folder, and auto-saves a default XML file on launch.
- Drag-and-drop folder support plus direct GitHub URL support in both GUI and CLI.
- Ignore handling for `.gitignore`, `.codeparserignore`, and built-in defaults.
- Token counting with `tiktoken`.
- Optional Tree-sitter compression with graceful fallback when advanced dependencies are not installed.
- Secret detection with `detect-secrets`.
- Single-file Windows packaging through PyInstaller and GitHub Actions.

## GUI Usage

1. Launch `CodeParser.exe` or run `python main.py`.
2. On startup, CodeParser opens the GUI, scans the current folder, and auto-saves a default XML file named like `codeparser-my-project-20260331.xml`.
3. Use the `Target` field to choose a local folder or paste a GitHub repository URL such as `https://github.com/user/repo`.
4. Drag a folder onto the window if you want to switch targets quickly.
5. Toggle options such as `Compress code`, `Remove comments`, `Secret scan`, `Count tokens`, and `Include git history`.
6. Review the live token preview and generated XML, then use `Copy XML` or `Save As...` if you want another output path.

## CLI Usage

Local folder:

```powershell
CodeParser.exe --cli --path . --output repo.xml --compress --count-tokens --secret-scan
```

GitHub URL:

```powershell
CodeParser.exe https://github.com/user/repo --cli --output repo.xml --compress
```

Common options:

- `--cli`: run without opening the GUI.
- `--path` / `-p`: local folder to pack.
- `--output` / `-o`: output XML path. If omitted, CodeParser writes `codeparser-[name]-[date].xml` in the current directory.
- `--compress`: enable optional Tree-sitter compression.
- `--remove-comments`: remove supported full-line comments before packing.
- `--include-git-history`: add a `<git_logs>` section.
- `--count-tokens`: count tokens with `tiktoken`.
- `--secret-scan`: scan files with `detect-secrets`.
- `--model`: tokenizer model name, default `gpt-4o-mini`.

## Download Latest EXE

- Latest release page: [CodeParser Releases](https://github.com/CBaileyDev/CodeParser/releases)
- Stable direct download: [CodeParser.exe](https://github.com/CBaileyDev/CodeParser/releases/latest/download/CodeParser.exe)
- Versioned release: [v1.0](https://github.com/CBaileyDev/CodeParser/releases/tag/v1.0)

## Build Instructions

Core install on Python 3.12-3.14:

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

Optional advanced compression dependencies:

```powershell
pip install -r requirements-optional.txt
```

Run the app from source:

```powershell
python main.py
```

Build the Windows executable:

```powershell
pip install pyinstaller
pyinstaller --clean --noconfirm CodeParser.spec
```

The executable is written to `dist/CodeParser.exe`.

## Comparison to Repomix

CodeParser is designed to feel familiar to Repomix users while improving the Windows workflow:

- Repomix-style XML structure and section names, so the generated output is easy to slot into existing prompts and tooling.
- Native desktop GUI instead of a CLI-only experience.
- Single-file `CodeParser.exe` distribution for Windows users who do not want to install Node or Python manually.
- Built-in token preview, presets, secret scanning, and drag-and-drop.
- Optional Tree-sitter compression that degrades cleanly when the advanced parser bundle is unavailable.
- GitHub URL support in both GUI and CLI, without requiring a local git clone just to inspect a public repository.
