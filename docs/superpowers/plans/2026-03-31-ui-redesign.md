# UI Redesign: Streamlined Single-Column Layout + Multi-Format Output

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Strip the GUI to a focused single-column tool: pick repo, set options, generate file, done. Remove sidebar, presets, and XML viewer. Add multi-format output (XML, Markdown, JSON, TXT). Dark-first design.

**Architecture:** The workbench drops its QSplitter + sidebar layout and becomes a direct QVBoxLayout hosting tabs. GenerateTab becomes a single-column flow: hero (path + generate), options row (checkboxes + format picker), and a success banner replacing the output editor. Theme controls move to a compact widget in the title bar. New output format builders (Markdown, JSON, TXT) sit alongside the existing xml_builder.py, selected by an `OutputFormat` enum on `CodeParserConfig`.

**Tech Stack:** PyQt6, Python 3.10+, existing theme token system, existing GenerateController worker

---

## File Structure

### New Files
- `codeparser/markdown_builder.py` -- Markdown output formatter
- `codeparser/json_builder.py` -- JSON output formatter
- `codeparser/text_builder.py` -- Plain text output formatter
- `codeparser/output_format.py` -- OutputFormat enum + dispatcher
- `tests/test_output_formats.py` -- Tests for all new builders
- `tests/test_generate_tab_redesign.py` -- Tests for redesigned GenerateTab

### Modified Files
- `codeparser/config.py` -- Add `output_format` field to CodeParserConfig
- `codeparser/parser_core.py` -- Use output_format dispatcher instead of hardcoded XML
- `codeparser/gui/generate_tab.py` -- Major rewrite: single-column, no presets, no viewer, success banner
- `codeparser/gui/build_tab.py` -- Minor cleanup
- `codeparser_ui/workbench.py` -- Remove sidebar+splitter, add theme controls to title bar area
- `codeparser_ui/window/title_bar.py` -- Add theme toggle widget
- `codeparser_ui/theme_manager.py` -- No structural changes, just consumed differently
- `codeparser_ui/workers/generate_worker.py` -- GenerateResult gets output_path field
- `tests/test_window_shell.py` -- Update for sidebar removal
- `tests/test_bootstrap.py` -- Minor updates if needed

### Files to Stop Using (but don't delete yet)
- `codeparser_ui/components/sidebar.py` -- No longer imported
- `codeparser/gui/preset_manager.py` -- No longer imported from GenerateTab

---

## Task 1: Add OutputFormat Enum and Config Field

**Files:**
- Create: `codeparser/output_format.py`
- Modify: `codeparser/config.py`
- Test: `tests/test_output_formats.py`

- [ ] **Step 1: Write the failing test for OutputFormat enum**

```python
# tests/test_output_formats.py
from codeparser.output_format import OutputFormat


def test_output_format_has_four_variants():
    assert set(OutputFormat) == {
        OutputFormat.XML,
        OutputFormat.MARKDOWN,
        OutputFormat.JSON,
        OutputFormat.TEXT,
    }


def test_output_format_file_extensions():
    assert OutputFormat.XML.extension == ".xml"
    assert OutputFormat.MARKDOWN.extension == ".md"
    assert OutputFormat.JSON.extension == ".json"
    assert OutputFormat.TEXT.extension == ".txt"


def test_output_format_display_names():
    assert OutputFormat.XML.display_name == "XML"
    assert OutputFormat.MARKDOWN.display_name == "Markdown"
    assert OutputFormat.JSON.display_name == "JSON"
    assert OutputFormat.TEXT.display_name == "Plain Text"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_output_formats.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'codeparser.output_format'`

- [ ] **Step 3: Implement OutputFormat enum**

```python
# codeparser/output_format.py
from __future__ import annotations

from enum import Enum


class OutputFormat(Enum):
    XML = ("xml", ".xml", "XML")
    MARKDOWN = ("markdown", ".md", "Markdown")
    JSON = ("json", ".json", "JSON")
    TEXT = ("text", ".txt", "Plain Text")

    def __init__(self, value: str, extension: str, display_name: str) -> None:
        self._value_ = value
        self._extension = extension
        self._display_name = display_name

    @property
    def extension(self) -> str:
        return self._extension

    @property
    def display_name(self) -> str:
        return self._display_name
```

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/test_output_formats.py -v`
Expected: PASS

- [ ] **Step 5: Add output_format to CodeParserConfig**

In `codeparser/config.py`, add the import and field:

```python
# At top of file, add import:
from .output_format import OutputFormat

# In the CodeParserConfig dataclass, add after secret_scan:
    output_format: OutputFormat = OutputFormat.XML
```

- [ ] **Step 6: Write test for config default**

Append to `tests/test_output_formats.py`:

```python
from codeparser.config import CodeParserConfig
from pathlib import Path


def test_config_defaults_to_xml():
    config = CodeParserConfig(root_path=Path("."))
    assert config.output_format == OutputFormat.XML
```

- [ ] **Step 7: Run all tests to verify nothing breaks**

Run: `pytest tests/test_output_formats.py -v`
Expected: All PASS

- [ ] **Step 8: Commit**

```bash
git add codeparser/output_format.py codeparser/config.py tests/test_output_formats.py
git commit -m "feat: add OutputFormat enum with XML, Markdown, JSON, TXT variants"
```

---

## Task 2: Build Markdown Output Formatter

**Files:**
- Create: `codeparser/markdown_builder.py`
- Test: `tests/test_output_formats.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_output_formats.py`:

```python
from codeparser.markdown_builder import build_markdown
from codeparser.parser_core import GenerationStats


def test_build_markdown_includes_file_contents():
    stats = GenerationStats(total_files=1, total_tokens=100)
    files = [{"path": "src/main.py", "content": "print('hello')", "lines": 1, "tokens": 5, "secrets": 0}]
    result = build_markdown(
        processed_files=files,
        directory_tree="src/\n  main.py",
        stats=stats,
        repository_name="test-repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    assert "# test-repo" in result
    assert "```" in result
    assert "print('hello')" in result
    assert "src/main.py" in result


def test_build_markdown_includes_directory_tree():
    stats = GenerationStats(total_files=1)
    files = [{"path": "a.py", "content": "x=1", "lines": 1, "tokens": None, "secrets": 0}]
    result = build_markdown(
        processed_files=files,
        directory_tree="a.py",
        stats=stats,
        repository_name="repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    assert "## Directory Structure" in result
    assert "a.py" in result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_output_formats.py::test_build_markdown_includes_file_contents -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement markdown_builder.py**

```python
# codeparser/markdown_builder.py
from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .parser_core import GenerationStats


def _guess_language(path: str) -> str:
    """Return a markdown fence language hint from the file extension."""
    ext = PurePosixPath(path).suffix.lower()
    mapping = {
        ".py": "python", ".js": "javascript", ".ts": "typescript",
        ".tsx": "tsx", ".jsx": "jsx", ".java": "java", ".c": "c",
        ".cpp": "cpp", ".go": "go", ".rs": "rust", ".rb": "ruby",
        ".sh": "bash", ".bash": "bash", ".json": "json", ".yaml": "yaml",
        ".yml": "yaml", ".toml": "toml", ".xml": "xml", ".html": "html",
        ".css": "css", ".sql": "sql", ".md": "markdown",
    }
    return mapping.get(ext, "")


def _format_stats(stats: GenerationStats) -> str:
    lines: List[str] = [f"- **Total files:** {stats.total_files}"]
    if stats.total_tokens is not None:
        lines.append(f"- **Approximate tokens:** {stats.total_tokens}")
    if stats.secrets_found:
        lines.append(f"- **Potential secrets flagged:** {stats.secrets_found}")
    return "\n".join(lines)


def build_markdown(
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats: GenerationStats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    parts: List[str] = []

    parts.append(f"# {repository_name}\n\n")
    parts.append("Packed representation of the repository, generated by CodeParser.\n\n")

    parts.append(_format_stats(stats))
    parts.append("\n\n")

    parts.append("## Directory Structure\n\n")
    parts.append(f"```\n{directory_tree}\n```\n\n")

    parts.append("## Files\n\n")
    for file_info in sorted(processed_files, key=lambda f: f["path"]):
        path = file_info["path"]
        content = file_info["content"]
        lang = _guess_language(path)
        parts.append(f"### `{path}`\n\n")
        parts.append(f"```{lang}\n{content}\n```\n\n")

    if include_git_logs and git_log_commits:
        parts.append("## Git History\n\n")
        for commit in git_log_commits:
            date = commit.get("date", "")
            message = commit.get("message", "")
            files = commit.get("files", [])
            parts.append(f"- **{date}** -- {message}\n")
            for f in files:
                parts.append(f"  - `{f}`\n")
        parts.append("\n")

    return "".join(parts)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/test_output_formats.py -v`
Expected: All PASS

- [ ] **Step 5: Commit**

```bash
git add codeparser/markdown_builder.py tests/test_output_formats.py
git commit -m "feat: add Markdown output builder"
```

---

## Task 3: Build JSON and Plain Text Output Formatters

**Files:**
- Create: `codeparser/json_builder.py`
- Create: `codeparser/text_builder.py`
- Test: `tests/test_output_formats.py` (append)

- [ ] **Step 1: Write failing tests for both builders**

Append to `tests/test_output_formats.py`:

```python
import json as json_lib

from codeparser.json_builder import build_json
from codeparser.text_builder import build_text


def test_build_json_is_valid_json():
    stats = GenerationStats(total_files=1, total_tokens=50)
    files = [{"path": "a.py", "content": "x=1", "lines": 1, "tokens": 5, "secrets": 0}]
    result = build_json(
        processed_files=files,
        directory_tree="a.py",
        stats=stats,
        repository_name="test-repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    parsed = json_lib.loads(result)
    assert parsed["repository"] == "test-repo"
    assert len(parsed["files"]) == 1
    assert parsed["files"][0]["path"] == "a.py"
    assert parsed["files"][0]["content"] == "x=1"
    assert parsed["stats"]["total_files"] == 1


def test_build_text_includes_file_contents():
    stats = GenerationStats(total_files=1)
    files = [{"path": "a.py", "content": "x=1", "lines": 1, "tokens": None, "secrets": 0}]
    result = build_text(
        processed_files=files,
        directory_tree="a.py",
        stats=stats,
        repository_name="test-repo",
        include_git_logs=False,
        git_log_commits=[],
    )
    assert "test-repo" in result
    assert "a.py" in result
    assert "x=1" in result
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `pytest tests/test_output_formats.py::test_build_json_is_valid_json tests/test_output_formats.py::test_build_text_includes_file_contents -v`
Expected: FAIL with `ModuleNotFoundError`

- [ ] **Step 3: Implement json_builder.py**

```python
# codeparser/json_builder.py
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
    stats_dict: Dict[str, Any] = {
        "total_files": stats.total_files,
    }
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
```

- [ ] **Step 4: Implement text_builder.py**

```python
# codeparser/text_builder.py
from __future__ import annotations

from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from .parser_core import GenerationStats


_SEPARATOR = "=" * 72


def build_text(
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats: GenerationStats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    parts: List[str] = []

    parts.append(f"Repository: {repository_name}")
    parts.append(f"Generated by CodeParser")
    parts.append(f"Total files: {stats.total_files}")
    if stats.total_tokens is not None:
        parts.append(f"Approximate tokens: {stats.total_tokens}")
    if stats.secrets_found:
        parts.append(f"Potential secrets flagged: {stats.secrets_found}")
    parts.append("")

    parts.append(_SEPARATOR)
    parts.append("DIRECTORY STRUCTURE")
    parts.append(_SEPARATOR)
    parts.append(directory_tree)
    parts.append("")

    parts.append(_SEPARATOR)
    parts.append("FILES")
    parts.append(_SEPARATOR)
    parts.append("")

    for file_info in sorted(processed_files, key=lambda f: f["path"]):
        path = file_info["path"]
        content = file_info["content"]
        parts.append(f"--- {path} ---")
        parts.append(content)
        parts.append("")

    if include_git_logs and git_log_commits:
        parts.append(_SEPARATOR)
        parts.append("GIT HISTORY")
        parts.append(_SEPARATOR)
        for commit in git_log_commits:
            date = commit.get("date", "")
            message = commit.get("message", "")
            parts.append(f"  {date}  {message}")
            for f in commit.get("files", []):
                parts.append(f"    {f}")
        parts.append("")

    return "\n".join(parts)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/test_output_formats.py -v`
Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add codeparser/json_builder.py codeparser/text_builder.py tests/test_output_formats.py
git commit -m "feat: add JSON and plain text output builders"
```

---

## Task 4: Wire Output Format Into parser_core

**Files:**
- Modify: `codeparser/output_format.py` (add dispatcher)
- Modify: `codeparser/parser_core.py`
- Test: `tests/test_output_formats.py` (append)

- [ ] **Step 1: Write the failing test**

Append to `tests/test_output_formats.py`:

```python
from codeparser.output_format import OutputFormat, build_output


def test_build_output_dispatches_to_correct_builder():
    stats = GenerationStats(total_files=1, total_tokens=10)
    files = [{"path": "a.py", "content": "x=1", "lines": 1, "tokens": 5, "secrets": 0}]
    kwargs = dict(
        processed_files=files,
        directory_tree="a.py",
        stats=stats,
        repository_name="repo",
        include_git_logs=False,
        git_log_commits=[],
    )

    xml_result = build_output(OutputFormat.XML, **kwargs)
    assert "<file" in xml_result

    md_result = build_output(OutputFormat.MARKDOWN, **kwargs)
    assert "# repo" in md_result

    json_result = build_output(OutputFormat.JSON, **kwargs)
    assert '"repository"' in json_result

    txt_result = build_output(OutputFormat.TEXT, **kwargs)
    assert "Repository: repo" in txt_result
```

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/test_output_formats.py::test_build_output_dispatches_to_correct_builder -v`
Expected: FAIL with `ImportError: cannot import name 'build_output'`

- [ ] **Step 3: Add build_output dispatcher to output_format.py**

Add to the bottom of `codeparser/output_format.py`:

```python
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .parser_core import GenerationStats


def build_output(
    fmt: OutputFormat,
    *,
    processed_files: list[dict],
    directory_tree: str,
    stats: GenerationStats,
    repository_name: str,
    include_git_logs: bool,
    git_log_commits: list[dict],
) -> str:
    kwargs = dict(
        processed_files=processed_files,
        directory_tree=directory_tree,
        stats=stats,
        repository_name=repository_name,
        include_git_logs=include_git_logs,
        git_log_commits=git_log_commits,
    )
    if fmt == OutputFormat.XML:
        from .xml_builder import build_repomix_xml
        return build_repomix_xml(**kwargs)
    if fmt == OutputFormat.MARKDOWN:
        from .markdown_builder import build_markdown
        return build_markdown(**kwargs)
    if fmt == OutputFormat.JSON:
        from .json_builder import build_json
        return build_json(**kwargs)
    if fmt == OutputFormat.TEXT:
        from .text_builder import build_text
        return build_text(**kwargs)
    raise ValueError(f"Unsupported output format: {fmt}")
```

- [ ] **Step 4: Update parser_core.py to use build_output**

In `codeparser/parser_core.py`, replace the `build_repomix_xml` import and call:

Replace:
```python
from .xml_builder import build_repomix_xml
```
With:
```python
from .output_format import build_output
```

Replace the `xml_text = build_repomix_xml(...)` block (around line 222-229) with:
```python
    output_text = build_output(
        config.output_format,
        processed_files=processed_files,
        directory_tree=directory_tree,
        stats=stats,
        repository_name=config.display_name or config.root_path.name or "repo",
        include_git_logs=config.include_git_history,
        git_log_commits=git_log_commits,
    )

    return output_text, stats
```

Note: The function is still called `generate_xml` for backwards compat, but now produces any format.

- [ ] **Step 5: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS (existing XML tests still work since default is XML)

- [ ] **Step 6: Commit**

```bash
git add codeparser/output_format.py codeparser/parser_core.py tests/test_output_formats.py
git commit -m "feat: wire output format dispatcher into parser core"
```

---

## Task 5: Update GenerateResult and Worker to Include output_path

**Files:**
- Modify: `codeparser_ui/workers/generate_worker.py`
- Modify: `codeparser/output_format.py` (import for extension)

- [ ] **Step 1: Update GenerateResult dataclass**

In `codeparser_ui/workers/generate_worker.py`, update:

```python
@dataclass(frozen=True)
class GenerateResult:
    xml_text: str
    stats: Any
    output_path: str | None = None
```

- [ ] **Step 2: Run existing tests to verify nothing breaks**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add codeparser_ui/workers/generate_worker.py
git commit -m "feat: add output_path to GenerateResult"
```

---

## Task 6: Redesign GenerateTab -- Single-Column, No Presets, No Viewer

This is the largest task. The GenerateTab becomes:
1. **Hero panel**: eyebrow, title, short description, path input + browse, format selector, generate button
2. **Options row**: packing option checkboxes in a compact horizontal layout
3. **Success banner**: hidden by default, shown after generation with file path + action buttons

**Files:**
- Modify: `codeparser/gui/generate_tab.py` (major rewrite)

- [ ] **Step 1: Rewrite _build_ui method**

Replace the entire `_build_ui` method in `codeparser/gui/generate_tab.py` with the new single-column layout. The full replacement for the method:

```python
def _build_ui(self, initial_target: str) -> None:
    layout = QVBoxLayout(self)
    layout.setContentsMargins(24, 24, 24, 24)
    layout.setSpacing(16)

    # -- Hero panel --
    hero = QFrame(self)
    hero.setObjectName("CodeParserPanel")
    hero.setProperty("surface", "panel")
    hero_layout = QVBoxLayout(hero)
    hero_layout.setContentsMargins(20, 20, 20, 20)
    hero_layout.setSpacing(12)

    eyebrow = QLabel("GENERATE WORKFLOW", hero)
    eyebrow.setObjectName("CodeParserEyebrow")
    hero_layout.addWidget(eyebrow)

    title = QLabel("Pack a repo into an AI-ready file", hero)
    title.setObjectName("CodeParserTitle")
    title.setWordWrap(True)
    hero_layout.addWidget(title)

    body = QLabel(
        "Choose a local folder or GitHub repository, pick an output format, and generate a single packed file.",
        hero,
    )
    body.setObjectName("CodeParserBody")
    body.setProperty("tone", "secondary")
    body.setWordWrap(True)
    hero_layout.addWidget(body)

    # Target input row
    target_row = QHBoxLayout()
    target_row.setSpacing(10)

    self.target_edit = QLineEdit(initial_target)
    self.target_edit.setPlaceholderText(
        "Select a local folder or paste a GitHub repository URL",
    )
    target_row.addWidget(self.target_edit, 1)

    self.browse_btn = QPushButton("Browse...")
    self.browse_btn.setProperty("variant", "toolbar")
    self.browse_btn.clicked.connect(self._on_browse)
    target_row.addWidget(self.browse_btn)
    hero_layout.addLayout(target_row)

    hint = QLabel(
        "Tip: drag a folder onto the window, or paste a GitHub URL such as https://github.com/user/repo",
        hero,
    )
    hint.setObjectName("CodeParserBody")
    hint.setProperty("tone", "secondary")
    hint.setWordWrap(True)
    hero_layout.addWidget(hint)

    layout.addWidget(hero)

    # -- Options panel --
    options_surface = QFrame(self)
    options_surface.setObjectName("CodeParserSurface")
    options_surface.setProperty("surface", "panel")
    options_layout = QVBoxLayout(options_surface)
    options_layout.setContentsMargins(20, 16, 20, 16)
    options_layout.setSpacing(12)

    options_header = QLabel("PACKING OPTIONS", options_surface)
    options_header.setObjectName("CodeParserEyebrow")
    options_layout.addWidget(options_header)

    # Checkboxes in a flow layout (2 rows)
    options_grid = QGridLayout()
    options_grid.setHorizontalSpacing(20)
    options_grid.setVerticalSpacing(8)

    self.compress_cb = QCheckBox("Compress code (Tree-sitter)")
    if not is_advanced_compression_available():
        self.compress_cb.setToolTip(
            "Optional Tree-sitter packages are not installed. "
            "CodeParser will fall back to the original source content.",
        )
    self.remove_comments_cb = QCheckBox("Remove comments")
    self.include_git_history_cb = QCheckBox("Include git history")
    self.count_tokens_cb = QCheckBox("Count tokens")
    self.count_tokens_cb.setChecked(True)
    self.secret_scan_cb = QCheckBox("Secret scan")

    options_grid.addWidget(self.compress_cb, 0, 0)
    options_grid.addWidget(self.remove_comments_cb, 0, 1)
    options_grid.addWidget(self.include_git_history_cb, 0, 2)
    options_grid.addWidget(self.count_tokens_cb, 1, 0)
    options_grid.addWidget(self.secret_scan_cb, 1, 1)
    options_layout.addLayout(options_grid)

    # Format selector + Generate button row
    action_row = QHBoxLayout()
    action_row.setSpacing(10)

    format_label = QLabel("Output format:", options_surface)
    format_label.setObjectName("CodeParserBody")
    action_row.addWidget(format_label)

    self.format_combo = QComboBox(options_surface)
    self.format_combo.setAccessibleName("Output format selector")
    for fmt in OutputFormat:
        self.format_combo.addItem(fmt.display_name, fmt)
    # Default to Markdown (best for AI)
    md_index = self.format_combo.findData(OutputFormat.MARKDOWN)
    if md_index >= 0:
        self.format_combo.setCurrentIndex(md_index)
    action_row.addWidget(self.format_combo)

    action_row.addStretch(1)

    self.generate_btn = QPushButton("Generate")
    self.generate_btn.setProperty("variant", "primary")
    self.generate_btn.clicked.connect(self._on_generate)
    action_row.addWidget(self.generate_btn)

    options_layout.addLayout(action_row)
    layout.addWidget(options_surface)

    # -- Live preview metrics (compact) --
    preview_surface = QFrame(self)
    preview_surface.setObjectName("CodeParserSurface")
    preview_surface.setProperty("surface", "panel")
    preview_layout = QHBoxLayout(preview_surface)
    preview_layout.setContentsMargins(20, 14, 20, 14)
    preview_layout.setSpacing(20)

    preview_layout.addLayout(self._create_metric_block("Files", "0", "preview_files_value"))
    preview_layout.addLayout(self._create_metric_block("Tokens", "0", "preview_tokens_value"))
    preview_layout.addLayout(self._create_metric_block("Source", "Local", "preview_source_value"))

    self.preview_detail_label = QLabel("Ready to preview.", preview_surface)
    self.preview_detail_label.setObjectName("CodeParserBody")
    self.preview_detail_label.setProperty("tone", "secondary")
    self.preview_detail_label.setWordWrap(True)
    preview_layout.addWidget(self.preview_detail_label, 1)

    layout.addWidget(preview_surface)

    # -- Progress bar (hidden by default) --
    self.progress_bar = QProgressBar()
    self.progress_bar.setRange(0, 0)
    self.progress_bar.setVisible(False)
    layout.addWidget(self.progress_bar)

    # -- Success banner (hidden by default) --
    self.success_banner = QFrame(self)
    self.success_banner.setObjectName("CodeParserSurface")
    self.success_banner.setProperty("surface", "elevated")
    self.success_banner.setVisible(False)
    banner_layout = QVBoxLayout(self.success_banner)
    banner_layout.setContentsMargins(20, 16, 20, 16)
    banner_layout.setSpacing(10)

    self.banner_title = QLabel("Generation complete", self.success_banner)
    self.banner_title.setObjectName("CodeParserTitle")
    self.banner_title.setStyleSheet("font-size: 18px;")
    banner_layout.addWidget(self.banner_title)

    self.status_label = QLabel("", self.success_banner)
    self.status_label.setObjectName("CodeParserBody")
    self.status_label.setProperty("tone", "secondary")
    self.status_label.setWordWrap(True)
    banner_layout.addWidget(self.status_label)

    banner_actions = QHBoxLayout()
    banner_actions.setSpacing(10)

    self.open_folder_btn = QPushButton("Open folder")
    self.open_folder_btn.setProperty("variant", "toolbar")
    self.open_folder_btn.clicked.connect(self._on_open_output_folder)
    self.open_folder_btn.setVisible(False)
    banner_actions.addWidget(self.open_folder_btn)

    self.copy_path_btn = QPushButton("Copy path")
    self.copy_path_btn.setProperty("variant", "toolbar")
    self.copy_path_btn.clicked.connect(self._on_copy_output_path)
    self.copy_path_btn.setVisible(False)
    banner_actions.addWidget(self.copy_path_btn)

    banner_actions.addStretch(1)
    banner_layout.addLayout(banner_actions)

    layout.addWidget(self.success_banner)

    # Spacer to push content up
    layout.addStretch(1)

    # -- Connections --
    self.target_edit.textChanged.connect(self._on_target_changed)
    for cb in (
        self.compress_cb,
        self.remove_comments_cb,
        self.include_git_history_cb,
        self.count_tokens_cb,
        self.secret_scan_cb,
    ):
        cb.stateChanged.connect(self._schedule_preview)
```

- [ ] **Step 2: Add new imports to generate_tab.py**

At the top of the file, add:
```python
from codeparser.output_format import OutputFormat
```

Also add `QGridLayout` to the PyQt6 import if not already there (it is).

- [ ] **Step 3: Remove preset-related code**

Remove these methods entirely from GenerateTab:
- `_refresh_presets`
- `_on_preset_changed`
- `_on_save_preset`
- `_on_delete_preset`

Remove the preset import:
```python
from .preset_manager import delete_preset, list_preset_names, load_preset, save_preset
```

Remove from `__init__`:
```python
self._refresh_presets()
```

- [ ] **Step 4: Remove the output_editor and old copy/save buttons**

The old `output_editor`, `copy_btn`, and `save_btn` are gone. Remove any references to them throughout the class.

- [ ] **Step 5: Update _build_config to use selected format**

In `_build_config`, add the format from the combo:

```python
def _build_config(self, preview: bool = False) -> tuple[CodeParserConfig, ResolvedTarget]:
    resolved = self._resolve_current_target()
    selected_format = self.format_combo.currentData()
    if not isinstance(selected_format, OutputFormat):
        selected_format = OutputFormat.XML
    return (
        CodeParserConfig(
            root_path=resolved.root_path,
            output_path=self._last_output_path,
            display_name=resolved.display_name,
            compress=self.compress_cb.isChecked(),
            remove_comments=self.remove_comments_cb.isChecked(),
            include_git_history=self.include_git_history_cb.isChecked(),
            count_tokens=self.count_tokens_cb.isChecked(),
            secret_scan=self.secret_scan_cb.isChecked(),
            output_format=selected_format,
            preview_mode=preview,
        ),
        resolved,
    )
```

- [ ] **Step 6: Update _on_generation_finished for auto-save + banner**

Replace `_on_generation_finished`:

```python
def _on_generation_finished(self, result: GenerateResult) -> None:
    self._cleanup_active_generation_target()

    stats = result.stats
    selected_format = self.format_combo.currentData()
    if not isinstance(selected_format, OutputFormat):
        selected_format = OutputFormat.XML

    # Auto-save to dist/ folder
    try:
        config, resolved = self._build_config(preview=False)
        display_name = config.display_name or resolved.display_name
        self._cleanup_resolved_target(resolved)
    except Exception:
        display_name = "repo"

    output_path = self._default_output_path(display_name, selected_format)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(result.xml_text, encoding="utf-8")
    self._last_output_path = output_path.resolve()

    # Show success banner
    summary = f"Saved to {output_path}"
    if stats.total_tokens is not None:
        summary += f"  |  {stats.total_files} files  |  {stats.total_tokens} tokens"
    else:
        summary += f"  |  {stats.total_files} files"
    if stats.secrets_found:
        summary += f"  |  {stats.secrets_found} potential secrets"
    if self.compress_cb.isChecked() and not is_advanced_compression_available():
        summary += "  |  Tree-sitter unavailable, kept original source"

    self.status_label.setText(summary)
    self.success_banner.setVisible(True)
    self.open_folder_btn.setVisible(True)
    self.copy_path_btn.setVisible(True)
```

- [ ] **Step 7: Update _default_output_path to accept format**

```python
def _default_output_path(self, display_name: str, fmt: OutputFormat | None = None) -> Path:
    if fmt is None:
        fmt = OutputFormat.XML
    date_str = datetime.now().strftime("%Y%m%d")
    slug = re.sub(r"[^A-Za-z0-9._-]+", "-", display_name.strip()).strip("-") or "repo"
    dist_dir = Path.cwd() / "dist"
    return dist_dir / f"codeparser-{slug}-{date_str}{fmt.extension}"
```

- [ ] **Step 8: Add banner action handlers**

Add these methods to GenerateTab:

```python
def _on_open_output_folder(self) -> None:
    if self._last_output_path and self._last_output_path.parent.exists():
        import subprocess
        import sys
        if sys.platform == "win32":
            subprocess.Popen(["explorer", "/select,", str(self._last_output_path)])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(self._last_output_path)])
        else:
            subprocess.Popen(["xdg-open", str(self._last_output_path.parent)])

def _on_copy_output_path(self) -> None:
    if self._last_output_path:
        QApplication.clipboard().setText(str(self._last_output_path))
        self.status_label.setText(f"Path copied: {self._last_output_path}")
```

- [ ] **Step 9: Update _set_busy (remove references to deleted widgets)**

```python
def _set_busy(self, busy: bool) -> None:
    self.progress_bar.setVisible(busy)
    self.generate_btn.setEnabled(not busy and self._has_target())
    self.browse_btn.setEnabled(not busy)
    self.target_edit.setEnabled(not busy)
    self.compress_cb.setEnabled(not busy)
    self.remove_comments_cb.setEnabled(not busy)
    self.include_git_history_cb.setEnabled(not busy)
    self.count_tokens_cb.setEnabled(not busy)
    self.secret_scan_cb.setEnabled(not busy)
    self.format_combo.setEnabled(not busy)
    if busy:
        self.success_banner.setVisible(False)
```

- [ ] **Step 10: Remove _on_copy_xml and _on_save_xml methods**

Delete these methods entirely -- they are replaced by the banner actions.

- [ ] **Step 11: Run tests**

Run: `pytest tests/ -v`
Expected: Existing tests may need updates (handled in Task 8). New UI should be structurally sound.

- [ ] **Step 12: Commit**

```bash
git add codeparser/gui/generate_tab.py
git commit -m "feat: redesign GenerateTab to single-column with auto-save and success banner"
```

---

## Task 7: Remove Sidebar From Workbench + Move Theme Controls

**Files:**
- Modify: `codeparser_ui/workbench.py`
- Modify: `codeparser_ui/window/title_bar.py`

- [ ] **Step 1: Add theme controls to title_bar.py**

Read `codeparser_ui/window/title_bar.py` first. Then add a `set_trailing_widget` method that inserts a widget before the window control buttons:

```python
def set_trailing_widget(self, widget: QWidget) -> None:
    """Insert a widget into the title bar, before the window control buttons."""
    # Insert before the stretch that precedes the control buttons
    # The layout is: title, subtitle, stretch, [trailing], min, max, close
    control_count = 3  # min, max, close
    insert_index = self._layout.count() - control_count
    self._layout.insertWidget(insert_index, widget)
```

- [ ] **Step 2: Rewrite _WorkbenchContent to remove sidebar**

Replace the `__init__` and `_build_sidebar` in `_WorkbenchContent`:

```python
class _WorkbenchContent(QWidget):
    def __init__(
        self,
        theme_manager: ThemeManager,
        settings: QSettings,
        initial_target: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._theme_manager = theme_manager
        self._settings = settings
        self._shortcuts: list[QShortcut] = []
        self._focus_cycle_widgets: list[QWidget] = []
        self._last_focus_index = -1

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(20, 12, 20, 18)
        root_layout.setSpacing(12)

        self.tab_widget = QTabWidget(self)
        self.tab_widget.setObjectName("workbenchTabs")
        self.tab_widget.setDocumentMode(True)

        self.generate_tab = GenerateTab(initial_target=initial_target)
        self.build_tab = BuildTab()

        self.tab_widget.addTab(self.generate_tab, "Generate")
        self.tab_widget.addTab(self.build_tab, "Build")

        root_layout.addWidget(self.tab_widget, 1)

        self.target_edit = self.generate_tab.target_edit
        self.generate_btn = self.generate_tab.generate_btn

        # Theme controls (compact row for title bar)
        self._theme_widget = QWidget()
        theme_layout = QHBoxLayout(self._theme_widget)
        theme_layout.setContentsMargins(0, 0, 8, 0)
        theme_layout.setSpacing(6)

        self.system_theme_switch = ToggleSwitch(self._theme_widget)
        self.system_theme_switch.setToolTip("Follow system theme")
        self.system_theme_switch.toggled.connect(self._on_system_theme_toggled)
        theme_layout.addWidget(self.system_theme_switch)

        self.theme_mode_combo = QComboBox(self._theme_widget)
        self.theme_mode_combo.setAccessibleName("Theme mode selector")
        self.theme_mode_combo.setFixedWidth(80)
        self.theme_mode_combo.addItem("Dark", ThemeMode.DARK)
        self.theme_mode_combo.addItem("Light", ThemeMode.LIGHT)
        self.theme_mode_combo.currentIndexChanged.connect(self._on_theme_mode_changed)
        theme_layout.addWidget(self.theme_mode_combo)

        self._theme_manager.themeChanged.connect(self._on_theme_changed)
        self.tab_widget.currentChanged.connect(self._persist_active_tab)
        self.target_edit.textChanged.connect(self._persist_source_path)
        self._command_palette = CommandPaletteDialog(self._build_commands(), self)
        self._install_shortcuts()
        self._install_accessibility()
        self._sync_theme_controls()

    @property
    def theme_widget(self) -> QWidget:
        """The compact theme control widget, meant to be placed in the title bar."""
        return self._theme_widget
```

- [ ] **Step 3: Remove _build_sidebar method entirely**

Delete the `_build_sidebar` method.

- [ ] **Step 4: Update _install_shortcuts to remove sidebar references**

```python
def _install_shortcuts(self) -> None:
    shortcuts: list[tuple[str, callable]] = [
        ("Ctrl+K", self._show_command_palette),
        ("Ctrl+O", self._open_folder),
        ("Ctrl+Shift+V", self._paste_repository_url),
        ("Ctrl+Enter", self._generate_current_target),
        ("Ctrl+L", self._focus_source_input),
        ("F6", self._cycle_major_panes),
        ("Ctrl+1", self._select_generate_tab),
        ("Ctrl+2", self._select_build_tab),
    ]

    for sequence, handler in shortcuts:
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ShortcutContext.WidgetWithChildrenShortcut)
        shortcut.activated.connect(handler)
        self._shortcuts.append(shortcut)

    self._focus_cycle_widgets = [
        self.theme_mode_combo,
        self.target_edit,
    ]
```

- [ ] **Step 5: Update _install_accessibility to remove sidebar references**

```python
def _install_accessibility(self) -> None:
    setup_accessible_widget(
        self.system_theme_switch,
        "Follow system theme",
        "Toggle whether the workbench follows the operating system color scheme.",
    )
    setup_accessible_widget(
        self.theme_mode_combo,
        "Theme mode",
        "Choose the workbench color theme when system-follow is disabled.",
    )
    setup_accessible_widget(
        self.tab_widget,
        "Workflow tabs",
        "Switch between the Generate and Build workflows.",
    )
    setup_accessible_widget(
        self.target_edit,
        "Repository source",
        "Enter a local folder path or a GitHub repository URL.",
    )
    self._command_palette.filter_edit.setAccessibleName("Command palette search")
    self._command_palette.command_list.setAccessibleName("Command palette results")
```

- [ ] **Step 6: Update _build_commands to remove export command**

Remove the "Export XML" command from the list (it no longer exists as a separate action since files auto-save).

- [ ] **Step 7: Remove _export_xml method and its shortcut**

Delete `_export_xml`. Remove the `Ctrl+Shift+E` shortcut entry.

- [ ] **Step 8: Update _bind_workbench to remove sidebar references**

```python
def _bind_workbench(window: QWidget, content: _WorkbenchContent) -> None:
    window.tab_widget = content.tab_widget
    window.generate_tab = content.generate_tab
    window.build_tab = content.build_tab
    window.system_theme_switch = content.system_theme_switch
    window.theme_mode_combo = content.theme_mode_combo
    window.target_edit = content.target_edit
    window.generate_btn = content.generate_btn
```

- [ ] **Step 9: Update CodeParserWorkbench to install theme widget in title bar**

After `_bind_workbench(self, content)` in CodeParserWorkbench.__init__, add:

```python
self.title_bar.set_trailing_widget(content.theme_widget)
```

- [ ] **Step 10: Update restore/save_persistent_state to remove splitter**

In `_WorkbenchContent.restore_persistent_state`:
```python
def restore_persistent_state(self, initial_target: str | None = None) -> None:
    active_tab = int(self._settings.value("last/active_tab", 0))
    if 0 <= active_tab < self.tab_widget.count():
        self.tab_widget.setCurrentIndex(active_tab)
    if not initial_target:
        last_source = str(self._settings.value("last/source_path", ""))
        if last_source:
            self.target_edit.setText(last_source)
```

In `_WorkbenchContent.save_persistent_state`:
```python
def save_persistent_state(self) -> None:
    self._settings.setValue("last/active_tab", self.tab_widget.currentIndex())
    self._settings.setValue("last/source_path", self.target_edit.text().strip())
```

Remove `_persist_splitter_state` method.

- [ ] **Step 11: Remove unused imports from workbench.py**

Remove: `QSplitter`, `QFrame`, `QHBoxLayout`, `QLabel`, `QPushButton` (if no longer used), and the `CollapsibleSidebar` import.

- [ ] **Step 12: Run tests**

Run: `pytest tests/ -v`
Expected: Some test failures in test_window_shell.py (handled in Task 8)

- [ ] **Step 13: Commit**

```bash
git add codeparser_ui/workbench.py codeparser_ui/window/title_bar.py
git commit -m "feat: remove sidebar, move theme controls to title bar, simplify workbench layout"
```

---

## Task 8: Update Tests for New Layout

**Files:**
- Modify: `tests/test_window_shell.py`

- [ ] **Step 1: Update test_window_shell.py**

The tests reference `window.sidebar`, `window.output_editor`, `window.copy_btn`, `window.save_btn`, and `window.main_splitter` which no longer exist. Update:

In `test_window_shell_replaces_workbench_and_updates_window_state`, the test creates a `_RecordingShell` and tests workbench replacement + window state. This should still work since it doesn't depend on sidebar. But remove any assertions that reference removed attributes.

Review each test and remove references to:
- `sidebar`
- `main_splitter`
- `output_editor`
- `copy_btn`
- `save_btn`

The premium shell smoke test should still work since it just shows the window and quits.

- [ ] **Step 2: Run all tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add tests/test_window_shell.py
git commit -m "test: update window shell tests for sidebar removal"
```

---

## Task 9: Clean Up Build Tab

**Files:**
- Modify: `codeparser/gui/build_tab.py`

- [ ] **Step 1: Simplify Build tab to a cleaner placeholder**

The Build tab should feel intentional. Update the copy to be forward-looking:

```python
def _build_ui(self) -> None:
    outer = QVBoxLayout(self)
    outer.setContentsMargins(24, 24, 24, 24)
    outer.setSpacing(16)

    hero = QFrame(self)
    hero.setObjectName("CodeParserPanel")
    hero.setProperty("surface", "panel")
    hero_layout = QVBoxLayout(hero)
    hero_layout.setContentsMargins(20, 20, 20, 20)
    hero_layout.setSpacing(10)

    eyebrow = QLabel("BUILD WORKFLOW", hero)
    eyebrow.setObjectName("CodeParserEyebrow")
    hero_layout.addWidget(eyebrow)

    self.placeholder_title = QLabel("Rebuild a project from packed files", hero)
    self.placeholder_title.setObjectName("CodeParserTitle")
    self.placeholder_title.setWordWrap(True)
    hero_layout.addWidget(self.placeholder_title)

    self.placeholder_body = QLabel(
        "The reverse workflow: feed a packed file back in, inspect the included files, "
        "and reconstruct the full directory tree. This is the next feature being built.",
        hero,
    )
    self.placeholder_body.setObjectName("CodeParserBody")
    self.placeholder_body.setProperty("tone", "secondary")
    self.placeholder_body.setWordWrap(True)
    self.placeholder_body.setTextFormat(Qt.TextFormat.PlainText)
    hero_layout.addWidget(self.placeholder_body)

    outer.addWidget(hero)

    # Placeholder action area
    action_surface = QFrame(self)
    action_surface.setObjectName("CodeParserSurface")
    action_surface.setProperty("surface", "panel")
    action_layout = QVBoxLayout(action_surface)
    action_layout.setContentsMargins(20, 20, 20, 20)
    action_layout.setSpacing(12)

    input_label = QLabel("PACKED FILE", action_surface)
    input_label.setObjectName("CodeParserEyebrow")
    action_layout.addWidget(input_label)

    self.xml_source_edit = QPlainTextEdit(action_surface)
    self.xml_source_edit.setPlaceholderText(
        "Drop or paste a packed file here when the build flow is ready.",
    )
    self.xml_source_edit.setReadOnly(True)
    self.xml_source_edit.setMinimumHeight(120)
    action_layout.addWidget(self.xml_source_edit)

    button_row = QHBoxLayout()
    button_row.setSpacing(10)

    self.output_folder_edit = QLineEdit(action_surface)
    self.output_folder_edit.setPlaceholderText("Output folder...")
    self.output_folder_edit.setReadOnly(True)
    button_row.addWidget(self.output_folder_edit, 1)

    self.build_button = QPushButton("Rebuild files", action_surface)
    self.build_button.setProperty("variant", "primary")
    self.build_button.setEnabled(False)
    button_row.addWidget(self.build_button)

    action_layout.addLayout(button_row)
    outer.addWidget(action_surface)

    outer.addStretch(1)
    self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
```

- [ ] **Step 2: Run tests**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 3: Commit**

```bash
git add codeparser/gui/build_tab.py
git commit -m "feat: clean up Build tab placeholder with forward-looking copy"
```

---

## Task 10: Remove Dead Imports and Final Cleanup

**Files:**
- Modify: `codeparser_ui/workbench.py` (verify clean imports)
- Modify: `codeparser/gui/generate_tab.py` (verify clean imports)

- [ ] **Step 1: Verify workbench.py has no unused imports**

The following should no longer be imported:
- `QSplitter` -- removed (no splitter)
- `QFrame` -- check if still used (center_surface is gone)
- `QHBoxLayout` -- check if still used (theme widget uses it, but it's built in _WorkbenchContent)
- `QLabel` -- check if still used
- `QPushButton` -- check if still used
- `CollapsibleSidebar` -- removed

Clean up any unused imports.

- [ ] **Step 2: Verify generate_tab.py has no unused imports**

Remove:
- `QPlainTextEdit` -- no longer used (output_editor removed)
- `QInputDialog` -- no longer used (presets removed)
- Preset manager imports

- [ ] **Step 3: Run full test suite**

Run: `pytest tests/ -v`
Expected: All PASS

- [ ] **Step 4: Commit**

```bash
git add codeparser_ui/workbench.py codeparser/gui/generate_tab.py
git commit -m "chore: remove dead imports after UI redesign"
```

---

## Summary of Layout Changes

### Before (Generate Tab)
```
+--[Sidebar]--+--[Center Panel]------------------+
| Workspace   | [Hero: title + path + generate]  |
| Quick Actn  | [Grid: presets | options]         |
| Appearance  | [Grid: live preview]              |
|             | [Output: editor + copy + save]    |
+-------------+----------------------------------+
```

### After (Generate Tab)
```
+--[Full Width]-----------------------------------+
| [Hero: title + path + browse]                    |
| [Options: checkboxes + format picker + generate] |
| [Preview: files | tokens | source | status]      |
| [Success banner: path + open folder + copy path] |
+--------------------------------------------------+
```

### Theme Controls
Before: In sidebar Appearance section
After: Compact toggle + combo in the title bar, right side before window controls
