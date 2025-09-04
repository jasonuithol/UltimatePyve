# file: utilities/dependencies.py
import os
import ast
import subprocess
import argparse

def gather_module_dependencies(root_dir, exclude):
    deps = set()
    modules = {}

    # Map module names (with package path) to file paths
    for dirpath, _, filenames in os.walk(root_dir):
        for fname in filenames:
            if fname.endswith(".py") and not fname.startswith("__"):
                rel_path = os.path.relpath(os.path.join(dirpath, fname), root_dir)
                mod_name = rel_path.replace(os.sep, ".")[:-3]  # strip .py
                if any(mod_name == ex or mod_name.startswith(ex + ".") for ex in exclude):
                    continue
                modules[mod_name] = os.path.join(dirpath, fname)

    # Parse each file for imports
    for mod_name, path in modules.items():
        with open(path, "r", encoding="utf-8") as f:
            try:
                tree = ast.parse(f.read(), filename=path)
            except SyntaxError:
                continue

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name in modules:
                        deps.add((mod_name, alias.name))
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module in modules:
                    deps.add((mod_name, node.module))
                elif node.module:
                    top_pkg = node.module.split('.')[0]
                    for m in modules:
                        if m == top_pkg or m.startswith(top_pkg + "."):
                            deps.add((mod_name, m))
                            break

    return sorted(deps), modules

def generate_dot(dependencies, modules):
    lines = [
        'digraph dependencies {',
        '    rankdir=LR;',
        '    node [shape=box, style=filled, fillcolor="#f0f8ff", fontname="Helvetica"];',
        '    edge [color="#555555", arrowsize=0.8];'
    ]

    # Group by top-level package
    clusters = {}
    for mod in modules:
        top_pkg = mod.split('.')[0]
        clusters.setdefault(top_pkg, set()).add(mod)

    for pkg, mods in sorted(clusters.items()):
        lines.append(f'    subgraph cluster_{pkg} {{')
        lines.append(f'        label = "{pkg}";')
        lines.append('        style=filled; fillcolor="#e6f2ff";')
        for m in sorted(mods):
            lines.append(f'        "{m}";')
        lines.append('    }')

    # Add edges
    for dependor, dependee in dependencies:
        lines.append(f'    "{dependor}" -> "{dependee}";')

    lines.append('}')
    return "\n".join(lines)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Generate dependency graph")
    parser.add_argument("--exclude", nargs="*", default=[], help="Modules or packages to exclude")
    parser.add_argument("--root", default=".", help="Project root directory")
    args = parser.parse_args()

    deps, modules = gather_module_dependencies(args.root, args.exclude)

    # 1. Save plain a -> b pairs
    pairs_txt = "dependencies.txt"
    with open(pairs_txt, "w", encoding="utf-8") as f:
        for dependor, dependee in deps:
            f.write(f"{dependor} -> {dependee}\n")
    print(f"Dependency pairs written to {pairs_txt}")

    # 2. Generate DOT
    dot_content = generate_dot(deps, modules)
    dot_path = "dependencies.dot"
    with open(dot_path, mode="w") as dot_file:
        dot_file.write(dot_content)
    print(f"Dependency graph written to {dot_path}")

    # 3. Render to SVG
    svg_path = "dependencies.svg"
    subprocess.run(["dot", "-Tsvg", dot_path, "-o", svg_path], check=True)
    print(f"Dependency graph written to {svg_path}")