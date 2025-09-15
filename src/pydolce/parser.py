import ast
from dataclasses import dataclass
from pathlib import Path
from typing import Generator


@dataclass
class CodeDocPair:
    """A class to hold a code segment and its corresponding docstring."""

    code_path: str
    code: str
    doc: str


def _parse_file(filepath: Path) -> Generator[CodeDocPair]:
    code = filepath.read_text()
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_code = ast.get_source_segment(code, node)
            assert func_code is not None
            func_doc = ast.get_docstring(node) or ""
            lineno = getattr(node, "lineno", 1)
            func_name = node.name
            codepath = f"{filepath}:{lineno}:{func_name}"
            yield CodeDocPair(
                code=func_code,
                doc=func_doc,
                code_path=f"{codepath}",
            )


def _parse_folder(folderpath: Path) -> Generator[CodeDocPair]:
    for file in folderpath.rglob("*.py"):
        yield from _parse_file(file)


def code_docs_from_path(path: str | Path) -> Generator[CodeDocPair]:
    path = path if isinstance(path, Path) else Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Path {path} is neither a file nor a directory.")

    if path.is_file():
        yield from _parse_file(path)
    else:
        yield from _parse_folder(path)
