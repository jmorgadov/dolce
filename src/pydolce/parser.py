from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Generator

from docstring_parser import Docstring, ParseError, parse


class CodeSegmentType(Enum):
    Function = auto()
    Class = auto()


@dataclass
class CodeSegment:
    """A class to hold a code segment and its corresponding docstring."""

    file_path: Path
    code_path: str
    lineno: int
    code: str
    doc: str
    parsed_doc: Docstring | None
    args: dict[str, str] | None = None
    returns: str | None = None
    seg_type: CodeSegmentType = CodeSegmentType.Function


class DocStatus(Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"


@dataclass
class CodeSegmentReport:
    status: DocStatus
    issues: list[str]

    @staticmethod
    def correct() -> CodeSegmentReport:
        return CodeSegmentReport(status=DocStatus.CORRECT, issues=[])


def _parse_file(filepath: Path) -> Generator[CodeSegment]:
    code = filepath.read_text()
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            func_code = ast.get_source_segment(code, node)
            assert func_code is not None
            func_doc = ast.get_docstring(node) or ""
            lineno = getattr(node, "lineno", 1)
            func_name = node.name
            codepath = f"{filepath}:{lineno} {func_name}"
            parsed_doc = None
            try:
                parsed_doc = parse(func_doc)
            except ParseError:
                pass

            yield CodeSegment(
                file_path=filepath,
                code=func_code,
                doc=func_doc,
                lineno=lineno,
                code_path=f"{codepath}",
                parsed_doc=parsed_doc,
                args={
                    a.arg: ast.unparse(a.annotation)
                    for a in node.args.args
                    if a.annotation is not None
                }
                if node.args
                else None,
                returns=ast.unparse(node.returns) if node.returns else None,
                seg_type=CodeSegmentType.Function,
            )


def _parse_folder(folderpath: Path) -> Generator[CodeSegment]:
    for file in folderpath.rglob("*.py"):
        yield from _parse_file(file)


def code_docs_from_path(path: str | Path) -> Generator[CodeSegment]:
    path = path if isinstance(path, Path) else Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Path {path} is neither a file nor a directory.")

    if path.is_file():
        yield from _parse_file(path)
    else:
        yield from _parse_folder(path)
