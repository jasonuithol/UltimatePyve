from pathlib import Path
from typing  import Callable

from dark_libraries.logging import LoggerMixin

from services.console_service import ConsoleService


CommandFn = Callable[[list[str]], None]


class ConsoleCommandService(LoggerMixin):

    # Injectable
    console_service: ConsoleService

    def __init__(self):
        super().__init__()
        self._commands: dict[str, CommandFn] = {}
        self.register("help", self._help)

    def run_file(self, path: Path):
        if not path.exists():
            self.log(f"WARN: console script not found at {path}")
            return
        for raw in path.read_text().splitlines():
            line = raw.split("#", 1)[0].strip()
            if not line:
                continue
            self.log(f"DEBUG: script > {line}")
            self.execute(line)

    def register(self, name: str, fn: CommandFn):
        key = name.lower()
        assert key not in self._commands, f"Command '{key}' already registered"
        self._commands[key] = fn

    def execute(self, line: str):
        tokens = line.strip().split()
        if not tokens:
            return
        name, args = tokens[0].lower(), tokens[1:]
        fn = self._commands.get(name)
        if fn is None:
            self.console_service.print_ascii(f"Unknown: {name}")
            return
        try:
            fn(args)
        except Exception as exc:
            self.log(f"ERROR: console command '{name}' raised {exc!r}")
            self.console_service.print_ascii(f"Err: {exc}")

    def _help(self, args: list[str]):
        for name in sorted(self._commands.keys()):
            self.console_service.print_ascii(name)
