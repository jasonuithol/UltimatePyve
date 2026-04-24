# Console scripts

One console command per line. Blank lines and `# comments` are ignored.

Run at startup via the `UPV_CONSOLE_SCRIPT` env var:

```bash
UPV_CONSOLE_SCRIPT=dev/scripts/britain.txt python main.py
```

The script runs after the saved-game location has loaded and before the main
input loop, so `spawn` overrides whatever the save file said.

## Available commands

- `teleport <name>` — teleport to a named location (e.g. `teleport britain`,
  `teleport lord british's castle`). `teleport overworld` returns to the outer map.
- `spawn <monster>` — spawn a monster adjacent to the party (for combat tests).
- `loc` — print current location, level and coord.
- `world` — flip between overworld and underworld (only valid on the outer map).
- `transport` — cycle through transport modes.
- `help` — list all registered commands.
- `quit` — exit the game (useful as the last line of a headless smoke-test).
