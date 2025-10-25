import os
from pathlib import Path

def get_u5_path() -> Path:
    u5_search_paths = [
        r"%ProgramFiles(x86)%\GOG Galaxy\Games\Ultima 5"
    ]
    for path_str in u5_search_paths:
        expanded = os.path.expanduser(os.path.expandvars(path_str))
        path = Path(expanded)
        if not path.exists():
            print(f"(main) no copy found at '{path.resolve()}'")
            continue
        return path
    assert False, "Could not find legal copy of Ultima V"
