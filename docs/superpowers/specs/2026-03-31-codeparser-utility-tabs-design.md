# CodeParser Utility Tabs Design

**Date:** 2026-03-31

## Goal

Evolve CodeParser into a more polished desktop utility by making the target-and-options workflow the visual hero, introducing a real tab shell now, and preserving room for a future reverse-flow build experience.

## Approved Direction

- Style the app as a polished desktop utility rather than a wizard or mini-IDE.
- Keep a compact single-window workflow.
- Introduce a tab shell now with `Generate` active and `Build` present as a placeholder.
- Open in a clean ready-to-pack state instead of auto-generating and auto-saving on launch.

## Layout

### Window shell

- Add a top-level tab control with:
  - `Generate`
  - `Build`
- `Generate` remains the main workflow.
- `Build` is intentionally a polished placeholder that explains the planned reverse operation: taking a packed XML file and recreating the files/directories.

### Generate tab

- Promote the target-and-options workflow to the primary visual area.
- Keep the XML result viewer below the main tool panel.
- Group controls into clearer sections:
  - target selection
  - presets and utility actions
  - packing options
  - preview/status summary
  - primary action row

## UX refinements

- Remove automatic generation on startup.
- Remove automatic save-on-launch behavior.
- Make `Generate` the clear primary action.
- Keep dark theme enabled by default.
- Preserve drag-and-drop for folders and GitHub URL support.

## Future compatibility

- The tab shell should make it easy to later replace the `Build` placeholder with a real XML-to-files workflow.
- The current refactor should move toward smaller GUI units rather than a single monolithic window implementation.
