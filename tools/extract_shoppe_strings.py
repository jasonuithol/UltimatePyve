"""
One-off dumper for SHOPPE.DAT, for documentation/reference only.

The runtime decodes SHOPPE.DAT live via data/loaders/shoppe_dat_loader.py and
models/shoppe_strings.py. This tool just calls into the same model and writes
the result to docs/shoppe_strings.json so contributors can browse the strings
without running the game.

Run from repo root:
    python3 tools/extract_shoppe_strings.py
"""

from pathlib import Path
import json
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from models.data_ovl import DataOVL
from models.shoppe_strings import ShoppeStrings


def main():
    u5_dir = ROOT / "u5"
    strings = ShoppeStrings.from_path(u5_dir, DataOVL(u5_dir))
    out = [{"index": i, "text": s} for i, s in enumerate(strings.all())]
    out_path = ROOT / "docs" / "shoppe_strings.json"
    out_path.write_text(json.dumps(out, indent=2, ensure_ascii=False))
    print(f"Wrote {len(out)} strings to {out_path}")


if __name__ == "__main__":
    main()
