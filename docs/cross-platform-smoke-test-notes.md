# CodeParser Cross-Platform Smoke-Test Notes

## Scope

These notes cover the premium shell path, the native-titlebar fallback path, and the existing Generate/Build workflows after the Phase 4 polish pass.

## Manual Smoke Matrix

- Windows 11:
  - Custom shell enabled
  - Native-titlebar fallback enabled
  - Test dark, light, and system-follow theme modes
  - Test normal, maximized, restored, and snapped window states
- Windows 10:
  - Custom shell enabled
  - Native-titlebar fallback enabled
  - Verify no fake Mica assumptions leak into the fallback path
- macOS:
  - Native-titlebar fallback enabled
  - Verify title bar, shortcuts, and theme controls still work
- Linux/X11:
  - Native-titlebar fallback enabled
  - Verify shortcuts, splitter persistence, and Generate workflow
- Linux/Wayland:
  - Native-titlebar fallback enabled
  - Verify fallback path remains stable and keyboard-first flows still work

## DPI and Monitor Checks

- 100%, 125%, 150%, 175%, and 200% scale factors
- Single monitor and dual monitor setups
- Secondary monitor with negative coordinates
- Disconnect and reconnect a display after saving window geometry
- Re-open the app and verify geometry clamps back into an available screen

## Workflow Checks

- GenerateTab preserves the 220 ms preview debounce
- Background generation stays responsive
- BuildTab still loads and remains reachable from the tab strip
- Theme mode persists across relaunch
- Splitter sizes persist across relaunch
- Active tab persists across relaunch
- Last source path persists across relaunch
- Command palette opens with `Ctrl+K`
- `Ctrl+O`, `Ctrl+Shift+V`, `Ctrl+Enter`, `Ctrl+Shift+E`, `Ctrl+L`, `F6`, `Ctrl+1`, and `Ctrl+2` all work

## Accessibility Checks

- Focus indicators remain visible in dark and light themes
- Command palette search field and results list expose accessible names
- Sidebar controls, theme controls, workflow tabs, source input, and XML output expose accessible names
- Contrast ratios for the primary theme text tokens remain at or above the validated thresholds
