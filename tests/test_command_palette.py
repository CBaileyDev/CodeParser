from __future__ import annotations

from codeparser_ui.components.command_palette import CommandPaletteCommand, CommandPaletteDialog


def test_command_palette_filters_and_executes_selected_command(qtbot) -> None:
    triggered: list[str] = []

    dialog = CommandPaletteDialog(
        [
            CommandPaletteCommand(
                title="Open folder",
                shortcut="Ctrl+O",
                handler=lambda: triggered.append("open"),
            ),
            CommandPaletteCommand(
                title="Generate XML",
                shortcut="Ctrl+Enter",
                handler=lambda: triggered.append("generate"),
            ),
        ]
    )
    qtbot.addWidget(dialog)
    dialog.show()

    dialog.filter_edit.setText("Generate")
    dialog._refresh_items()
    dialog.command_list.setCurrentRow(0)
    dialog._activate_current_command()

    assert triggered == ["generate"]
