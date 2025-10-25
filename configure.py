import os, sys
from pathlib import Path

MINIMUM_PYTHON_VERSION = (3,13)

def reject_python_version():
    print(f"Python {MINIMUM_PYTHON_VERSION[0]}.{MINIMUM_PYTHON_VERSION[1]} or later required. Exiting.")
    exit()

def check_python_version():
    if sys.version_info.major < MINIMUM_PYTHON_VERSION[0]:
        reject_python_version()
    if sys.version_info.major == MINIMUM_PYTHON_VERSION[0] and sys.version_info.minor < MINIMUM_PYTHON_VERSION[1]:
        reject_python_version()

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
