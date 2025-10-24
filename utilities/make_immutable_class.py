#!/usr/bin/env python3
import ast, sys, tokenize
from pathlib import Path
from io import StringIO
from typing import Dict, List, Tuple

Field = Tuple[str, str, str, bool]  # (name, annotation, comment, inherited)

CLASS_TEMPLATE = """\
class {clsname}(tuple):
    __slots__ = ()

    def __new__(
        cls,
{args}
    ):
        return tuple.__new__(cls, (
{argnames}
        ))

{properties}
"""

PROP_TEMPLATE = """\
    @property
    def {name}(self) -> {annotation}:
        return self[{index}]
"""

INHERITED_PROP_TEMPLATE = """\
    # inherits {name}:{annotation} at tuple index {index}
"""

# ---------------- helpers ----------------

def tokenize_comments(src: str) -> Dict[int, str]:
    comments = {}
    for tok in tokenize.generate_tokens(StringIO(src).readline):
        if tok.type == tokenize.COMMENT:
            comments[tok.start[0]] = tok.string.strip()
    return comments

def extract_classes(src: str) -> Dict[str, Tuple[ast.ClassDef, Dict[int, str]]]:
    tree = ast.parse(src)
    comments = tokenize_comments(src)
    return {
        node.name: (node, comments)
        for node in tree.body
        if isinstance(node, ast.ClassDef)
    }

def fields_from_annotations(node: ast.ClassDef, comments: Dict[int, str], parent_class: bool) -> List[Field]:
    out = []
    for stmt in node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            ann = ast.unparse(stmt.annotation)
            comment = comments.get(stmt.lineno, "")
            out.append((name, ann, comment, parent_class))
    return out

def fields_from_new(node: ast.ClassDef, parent_class: bool) -> List[Field]:
    for stmt in node.body:
        if isinstance(stmt, ast.FunctionDef) and stmt.name == "__new__":
            fields = []
            for arg in stmt.args.args[1:]:  # skip 'cls'
                name = arg.arg
                ann = ast.unparse(arg.annotation) if arg.annotation else "Any"
                fields.append((name, ann, "", parent_class))  # no comments available
            return fields
    return []

def fields_in_class(node: ast.ClassDef, comments: Dict[int, str], parent_class: bool) -> List[Field]:
    ann_fields = fields_from_annotations(node, comments, parent_class)
    if ann_fields:
        return ann_fields
    return fields_from_new(node, parent_class)

def get_base_names(node: ast.ClassDef) -> List[str]:
    names = []
    for base in node.bases:
        if isinstance(base, ast.Name):
            names.append(base.id)
    return names

def collect_fields(clsname: str, class_index: Dict[str, Tuple[ast.ClassDef, Dict[int, str]]], seen: list[str] = None, parent_class: bool = True) -> List[Field]:
    if seen is None:
        seen = set()
    if clsname in seen or clsname not in class_index:
        return []
    seen.add(clsname)

    node, comments = class_index[clsname]
    fields: List[Field] = []

    # collect from bases first
    for base in get_base_names(node):
        fields.extend(collect_fields(base, class_index, seen, parent_class = True))

    # then this class
    fields.extend(fields_in_class(node, comments, parent_class))
    return fields

def render_class(clsname: str, fields: List[Field]) -> str:
    arg_lines, argname_lines = [], []
    for name, ann, comment, inherited in fields:
        if inherited:
            if not comment:
                comment = "# "
            comment = comment +  " (inherited)"
        line = f"        {name}: {ann},"
        if comment:
            line = f"{line:<44} {comment}"
        arg_lines.append(line)

        argname_line = f"            {name},"
        argname_lines.append(f"{argname_line:<44} {comment}")
    args = "\n".join(arg_lines)
    argnames = "\n".join(argname_lines)

    props = []
    for idx, (name, ann, _, inherited) in enumerate(fields):
        if inherited:
            template = INHERITED_PROP_TEMPLATE
        else:
            template = PROP_TEMPLATE
        props.append(template.format(name=name, annotation=ann, index=idx))
    properties = "\n".join(props)

    return CLASS_TEMPLATE.format(
        clsname=clsname,
        args=args,
        argnames=argnames,
        properties=properties,
    )

def build_class_index(root: Path) -> Dict[str, Tuple[ast.ClassDef, Dict[int, str]]]:
    index = {}
    for py in root.rglob("*.py"):
        try:
            src = py.read_text(encoding="utf-8")
            index.update(extract_classes(src))
        except Exception:
            pass
    return index

# ---------------- main ----------------

def main(path: str):
    root = Path(path).parent
    if path == "-":
        src = sys.stdin.read()
    else:
        src = Path(path).read_text(encoding="utf-8")
    class_index = build_class_index(root)

    # assume last class in file is the target
    classes = extract_classes(src)
    if not classes:
        raise ValueError("No class found in file")
    clsname = list(classes.keys())[-1]

    fields = collect_fields(clsname, class_index, parent_class = False)
    print(render_class(clsname, fields))

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: make_immutable_class.py <child_class_file.py>")
        sys.exit(1)
    main(sys.argv[1])

'''
#!/usr/bin/env python3
import ast
import sys
import tokenize
from io import StringIO
from textwrap import indent

CLASS_TEMPLATE = """\
class {clsname}(tuple):
    __slots__ = ()

    def __new__(
        cls,
{args}
    ):
        return super().__new__(cls, (
{argnames}
        ))

{properties}
"""

PROP_TEMPLATE = """\
    @property
    def {name}(self) -> {annotation}:
        return self[{index}]
"""

def extract_fields_with_comments(src: str, class_node: ast.ClassDef):
    """Return list of (name, annotation, comment) for annotated assignments."""
    # Map line numbers to comments using tokenize
    comments_by_line = {}
    tokgen = tokenize.generate_tokens(StringIO(src).readline)
    for tok_type, tok_str, start, end, line in tokgen:
        if tok_type == tokenize.COMMENT:
            lineno = start[0]
            comments_by_line[lineno] = tok_str.strip()

    fields = []
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            ann = ast.unparse(stmt.annotation)
            comment = comments_by_line.get(stmt.lineno, "")
            fields.append((name, ann, comment))
    return fields

def transform_class(src: str) -> str:
    tree = ast.parse(src)
    class_node = next((n for n in tree.body if isinstance(n, ast.ClassDef)), None)
    if class_node is None:
        raise ValueError("No class found in source")

    clsname = class_node.name
    fields = extract_fields_with_comments(src, class_node)
    if not fields:
        raise ValueError(f"No annotated fields found in class {clsname}")

    # Build argument list (one per line, with comments)
    arg_lines = []
    argname_lines = []
    for name, ann, comment in fields:
        line = f"        {name}: {ann},"
        if comment:
            line = f"{line:<40} {comment}"
        arg_lines.append(line)
        argname_lines.append(f"            {name},")
    args = "\n".join(arg_lines)
    argnames = "\n".join(argname_lines)

    # Build properties
    props = []
    for idx, (name, ann, _) in enumerate(fields):
        props.append(PROP_TEMPLATE.format(name=name, annotation=ann, index=idx))
    properties = "\n".join(props)

    return CLASS_TEMPLATE.format(
        clsname=clsname,
        args=args,
        argnames=argnames,
        properties=properties,
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: make_immutable_class.py <sourcefile.py>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        src = f.read()

    print(transform_class(src))
'''




'''
#!/usr/bin/env python3
import ast
import sys
from textwrap import indent

CLASS_TEMPLATE = """\
class {clsname}(tuple):
    __slots__ = ()

    def __new__(cls, {args}):
        return super().__new__(cls, ({argnames}))

{properties}
"""

PROP_TEMPLATE = """\
    @property
    def {name}(self) -> {annotation}:
        return self[{index}]
"""

def transform_class(src: str) -> str:
    tree = ast.parse(src)
    class_node = None
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_node = node
            break
    if class_node is None:
        raise ValueError("No class found in source")

    clsname = class_node.name
    fields = []
    for stmt in class_node.body:
        if isinstance(stmt, ast.AnnAssign) and isinstance(stmt.target, ast.Name):
            name = stmt.target.id
            ann = ast.unparse(stmt.annotation)
            fields.append((name, ann))

    if not fields:
        raise ValueError(f"No annotated fields found in class {clsname}")

    # Build argument list
    args = ", ".join(f"{name}: {ann}" for name, ann in fields)
    argnames = ", ".join(name for name, _ in fields)

    # Build properties
    props = []
    for idx, (name, ann) in enumerate(fields):
        props.append(PROP_TEMPLATE.format(name=name, annotation=ann, index=idx))
    properties = "\n".join(props)

    return CLASS_TEMPLATE.format(
        clsname=clsname,
        args=args,
        argnames=argnames,
        properties=properties,
    )

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: make_immutable_class.py <sourcefile.py>")
        sys.exit(1)

    with open(sys.argv[1], "r", encoding="utf-8") as f:
        src = f.read()

    print(transform_class(src))
'''