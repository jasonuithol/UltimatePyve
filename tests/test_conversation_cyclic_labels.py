"""
Unit test for cyclic label graphs in the conversation controller.

Construct two labels whose initial_lines goto each other (label 0 → 1, 1 → 0)
and verify _render_and_speak terminates instead of infinite-looping. Wrapped
in a SIGALRM timeout so a regression surfaces as a TimeoutError rather than
a pytest hang.
"""
import signal

import pytest

from controllers.conversation_controller import ConversationController
from models.tlk_file import (
    NpcDialog,
    ScriptItem,
    ScriptLine,
    TalkCommand,
    TlkLabel,
)


LABEL_0_BYTE = 0x91
LABEL_1_BYTE = 0x92


class _RecordingConsole:
    def __init__(self):
        self.lines: list[str] = []

    def print_ascii(self, msg, *args, **kwargs):
        self.lines.append(msg if isinstance(msg, str) else "")

    def backspace(self): pass


class _StubNpc:
    has_met_avatar = False


def _with_timeout(seconds: float, fn, *args, **kwargs):
    def _raise(signum, frame):
        raise TimeoutError(f"operation exceeded {seconds}s — likely infinite loop")
    previous = signal.signal(signal.SIGALRM, _raise)
    signal.alarm(int(seconds))
    try:
        return fn(*args, **kwargs)
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, previous)


def _build_cyclic_dialog() -> NpcDialog:
    # label 0's initial_line: [SLD, 0x91 (own id, skipped), 0x92 (goto label 1)]
    # label 1's initial_line: [SLD, 0x92 (own id, skipped), 0x91 (goto label 0)]
    label_0 = TlkLabel(
        label_num=0,
        initial_line=ScriptLine(items=[
            ScriptItem(TalkCommand.START_LABEL_DEFINITION),
            ScriptItem(LABEL_0_BYTE),
            ScriptItem(LABEL_1_BYTE),
        ]),
    )
    label_1 = TlkLabel(
        label_num=1,
        initial_line=ScriptLine(items=[
            ScriptItem(TalkCommand.START_LABEL_DEFINITION),
            ScriptItem(LABEL_1_BYTE),
            ScriptItem(LABEL_0_BYTE),
        ]),
    )
    empty = ScriptLine(items=[])
    # Greeting gotos label 0, kicking off the cycle.
    greeting = ScriptLine(items=[ScriptItem(LABEL_0_BYTE)])
    return NpcDialog(
        npc_dialog_number=1,
        name=empty,
        description=empty,
        greeting=greeting,
        job=empty,
        bye=empty,
        labels={0: label_0, 1: label_1},
    )


def _make_controller() -> ConversationController:
    controller = ConversationController()
    controller.console_service = _RecordingConsole()
    # party_agent, global_registry, input_service, npc_service are unused
    # in the rendering path exercised by this test.
    return controller


def test_render_and_speak_terminates_on_cyclic_label_graph():
    controller = _make_controller()
    dialog = _build_cyclic_dialog()
    npc = _StubNpc()

    result = _with_timeout(
        5.0,
        controller._render_and_speak,
        dialog, dialog.greeting, npc, "Avatar",
    )
    # Return value is the last label we landed on before detecting the cycle.
    assert result is not None
    assert result.label_num in (0, 1)


def test_render_text_only_terminates_on_cyclic_label_graph():
    controller = _make_controller()
    dialog = _build_cyclic_dialog()
    npc = _StubNpc()

    # _render_text_only should also bail — it shares the goto-follow pattern.
    text = _with_timeout(
        5.0,
        controller._render_text_only,
        dialog, dialog.greeting, npc, "Avatar",
    )
    # The cyclic labels carry no plain text, so the buffer is empty —
    # but the important thing is that it returned at all.
    assert isinstance(text, str)
