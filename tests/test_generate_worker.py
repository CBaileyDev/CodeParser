from __future__ import annotations

import importlib
import threading


def test_generate_controller_runs_request_off_thread_and_emits_result(qtbot) -> None:
    module = importlib.import_module("codeparser_ui.workers.generate_worker")

    class FakeEngine:
        def generate_xml(self, request):
            return module.GenerateResult(
                xml_text=f"<xml source='{request.source_path}' />",
                stats={"files": 1},
            )

    controller = module.GenerateController(FakeEngine())
    busy_states: list[bool] = []
    controller.busy_changed.connect(busy_states.append)

    request = module.GenerateRequest(
        source_path="C:/repo",
        include_hidden=False,
        include_comments=True,
        count_tokens=True,
        run_secret_scan=False,
        use_tree_sitter=False,
    )

    with qtbot.waitSignal(controller.result_ready, timeout=3_000) as blocker:
        accepted = controller.submit(request)

    assert accepted is True
    assert blocker.args[0].xml_text == "<xml source='C:/repo' />"
    assert blocker.args[0].stats == {"files": 1}
    assert busy_states == [True, False]
    assert controller.busy is False


def test_generate_controller_rejects_second_request_while_busy(qtbot) -> None:
    module = importlib.import_module("codeparser_ui.workers.generate_worker")

    release = threading.Event()

    class FakeEngine:
        def generate_xml(self, request):
            release.wait(timeout=3)
            return module.GenerateResult(xml_text="<xml />", stats={})

    controller = module.GenerateController(FakeEngine())
    request = module.GenerateRequest(
        source_path="C:/repo",
        include_hidden=False,
        include_comments=True,
        count_tokens=False,
        run_secret_scan=False,
        use_tree_sitter=False,
    )

    assert controller.submit(request) is True
    assert controller.submit(request) is False

    release.set()
    qtbot.waitUntil(lambda: controller.busy is False, timeout=3_000)
