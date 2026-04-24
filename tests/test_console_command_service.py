import pytest

from services.console_command_service import ConsoleCommandService


class _FakeConsole:
    def __init__(self):
        self.lines: list[str] = []

    def print_ascii(self, msg, include_carriage_return=True, no_prompt=False):
        self.lines.append(msg if isinstance(msg, str) else "".join(chr(b) for b in msg))


def _make() -> tuple[ConsoleCommandService, _FakeConsole]:
    svc = ConsoleCommandService()
    console = _FakeConsole()
    svc.console_service = console
    return svc, console


def test_executes_registered_command_with_args():
    svc, _ = _make()
    received: list[list[str]] = []
    svc.register("foo", lambda args: received.append(args))

    svc.execute("foo a b c")

    assert received == [["a", "b", "c"]]


def test_command_lookup_is_case_insensitive():
    svc, _ = _make()
    received: list[list[str]] = []
    svc.register("World", lambda args: received.append(args))

    svc.execute("WORLD")
    svc.execute("world")

    assert received == [[], []]


def test_unknown_command_reports_error_without_raising():
    svc, console = _make()

    svc.execute("nope")

    assert any("nope" in line for line in console.lines)


def test_empty_line_is_a_noop():
    svc, console = _make()
    svc.execute("")
    svc.execute("   ")
    assert console.lines == []


def test_duplicate_registration_asserts():
    svc, _ = _make()
    svc.register("foo", lambda args: None)
    with pytest.raises(AssertionError):
        svc.register("foo", lambda args: None)


def test_help_lists_all_commands():
    svc, console = _make()
    svc.register("alpha", lambda args: None)
    svc.register("beta",  lambda args: None)

    svc.execute("help")

    assert "alpha" in console.lines
    assert "beta"  in console.lines
    assert "help"  in console.lines


def test_command_exception_is_caught():
    svc, console = _make()

    def boom(args):
        raise RuntimeError("kaboom")

    svc.register("boom", boom)
    svc.execute("boom")

    assert any("kaboom" in line for line in console.lines)


