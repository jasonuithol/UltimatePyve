"""
One-off: dump NUL-separated ASCII strings from a region of DATA.OVL.
Used to map the shopkeeper-text block that lives between ~0x7000..0x9300
(outside any currently-defined DataOVL slice).

Run from repo root:
    python3 tools/dump_data_ovl_strings.py 0x7e00 0x9300
    python3 tools/dump_data_ovl_strings.py             # default range
"""

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent


def is_printable(b: int) -> bool:
    return 32 <= b < 127 or b in (9, 10, 13)


def main():
    start = int(sys.argv[1], 0) if len(sys.argv) > 1 else 0x7000
    end   = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x9300

    raw = (ROOT / "u5" / "DATA.OVL").read_bytes()
    region = raw[start:end]

    cursor = 0
    while cursor < len(region):
        if region[cursor] == 0 or not is_printable(region[cursor]):
            cursor += 1
            continue
        run_start = cursor
        while cursor < len(region) and is_printable(region[cursor]):
            cursor += 1
        run = region[run_start:cursor]
        if len(run) >= 3:
            text = run.decode("ascii", errors="replace")
            print(f"0x{start + run_start:04x}  {text!r}")


if __name__ == "__main__":
    main()
