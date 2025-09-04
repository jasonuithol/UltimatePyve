# file: utilities/file_header_fixer.py
import os

def ensure_file_header(root_dir: str):
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if not fname.endswith(".py"):
                continue

            fpath = os.path.join(dirpath, fname)
            rel_path = os.path.relpath(fpath, root_dir).replace(os.sep, "/")
            expected_header = f"# file: {rel_path}\n"

            with open(fpath, "r", encoding="utf-8") as f:
                lines = f.readlines()

            if lines and lines[0].startswith("# file: "):
                if lines[0] != expected_header:
                    print(f"Updating header in {rel_path}")
                    lines[0] = expected_header
                else:
                    continue  # already correct
            else:
                print(f"Adding header to {rel_path}")
                lines.insert(0, expected_header)

            with open(fpath, "w", encoding="utf-8") as f:
                f.writelines(lines)

if __name__ == "__main__":
    ensure_file_header(".")  # current directory