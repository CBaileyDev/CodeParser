# CodeParser Utility Tabs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a polished tabbed desktop shell with a stronger Generate workflow, a Build placeholder tab, and a calmer ready-to-pack startup while also fixing the most obvious XML self-inclusion quality issue discovered during review.

**Architecture:** Split the GUI into smaller widgets so the main window becomes a shell around `Generate` and `Build` tabs. Keep the existing parsing logic intact where possible, but tighten XML output behavior so generated review/output files are not re-packed into later runs.

**Tech Stack:** Python 3.14, PyQt6, pytest, pytest-qt

---

## File map

- Modify: `C:/Users/Carte/Downloads/CodeParser/codeparser/gui/main_window.py`
- Create: `C:/Users/Carte/Downloads/CodeParser/codeparser/gui/generate_tab.py`
- Create: `C:/Users/Carte/Downloads/CodeParser/codeparser/gui/build_tab.py`
- Create: `C:/Users/Carte/Downloads/CodeParser/codeparser/gui/styles.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/codeparser/gui/__init__.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/tests/test_gui.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/codeparser/config.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/codeparser/parser_core.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/codeparser/xml_builder.py`
- Modify: `C:/Users/Carte/Downloads/CodeParser/tests/test_xml_output.py`

## Task 1: Lock the UI contract in tests

- [ ] Add Qt tests for:
  - default active tab is `Generate`
  - `Build` tab exists and shows placeholder copy
  - startup is ready-to-pack rather than auto-generated
  - XML actions are disabled until a generation run completes
- [ ] Add XML regression coverage ensuring an explicitly selected output path is not re-packed into a later run.
- [ ] Run the focused tests first and confirm they fail for the right reasons.

## Task 2: Introduce the tab shell and split the GUI

- [ ] Extract the current generation workflow into a dedicated `GenerateTab` widget.
- [ ] Create a `BuildTab` placeholder widget with polished explanatory content.
- [ ] Move the global dark theme into a small dedicated style module.
- [ ] Refactor `MainWindow` into a shell that hosts the tab widget and applies the default desktop-utility styling.

## Task 3: Polish Generate for the approved workflow

- [ ] Rework the top section so target selection and options become the visual hero.
- [ ] Make the app start in a clean ready state with no initial auto-generate or auto-save.
- [ ] Keep XML output below the control area.
- [ ] Make `Generate` the obvious primary action while preserving copy/save behavior after generation.

## Task 4: Fix XML self-inclusion and note accuracy

- [ ] Allow the parser config to track an output path that must be excluded from traversal.
- [ ] Ensure generated XML files chosen as output are not included in subsequent packing runs.
- [ ] Update summary notes so the `directory_structure` description is truthful about what is included.

## Task 5: Verify and review

- [ ] Run focused GUI and XML tests.
- [ ] Run the full test suite.
- [ ] Run at least one local CLI smoke command that writes an XML file.
- [ ] Request a code review pass before wrapping up.
