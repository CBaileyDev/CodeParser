from __future__ import annotations

from PyQt6.QtWidgets import QLabel

from codeparser_ui.components.sidebar import CollapsibleSidebar


def test_collapsible_sidebar_animates_and_hides_content(qtbot) -> None:
    sidebar = CollapsibleSidebar()
    qtbot.addWidget(sidebar)

    content = QLabel("Theme controls")
    sidebar.content_layout.addWidget(content)
    sidebar.show()

    assert sidebar.minimumWidth() == sidebar.EXPANDED_WIDTH
    assert sidebar.maximumWidth() == sidebar.EXPANDED_WIDTH

    sidebar.toggle()

    qtbot.waitUntil(
        lambda: sidebar.minimumWidth() == sidebar.COLLAPSED_WIDTH
        and sidebar.maximumWidth() == sidebar.COLLAPSED_WIDTH,
        timeout=2_000,
    )

    assert sidebar._animation_group is not None
    assert sidebar._section_label.isHidden() is True
    assert sidebar._content_host.isHidden() is True

    sidebar.toggle()

    qtbot.waitUntil(
        lambda: sidebar.minimumWidth() == sidebar.EXPANDED_WIDTH
        and sidebar.maximumWidth() == sidebar.EXPANDED_WIDTH,
        timeout=2_000,
    )
    assert sidebar._section_label.isVisible() is True
    assert sidebar._content_host.isVisible() is True
