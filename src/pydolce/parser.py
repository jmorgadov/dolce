from __future__ import annotations

import ast
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Generator

import pathspec
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
    params: dict[str, str] | None = None
    args_name: str | None = None
    args_type: str | None = None
    kwargs_name: str | None = None
    kwargs_type: str | None = None
    returns: str | None = None
    seg_type: CodeSegmentType = CodeSegmentType.Function

    @property
    def is_func(self) -> bool:
        return self.seg_type == CodeSegmentType.Function

    @property
    def is_class(self) -> bool:
        return self.seg_type == CodeSegmentType.Class

    @property
    def is_generator(self) -> bool:
        return self.returns is not None and self.returns.startswith("Generator")

    @property
    def generator_type(self) -> str | None:
        if self.is_generator:
            assert self.returns is not None
            # Extract the type inside Generator[...]
            start = self.returns.find("[") + 1
            end = self.returns.find(",", start)
            if end == -1:
                end = self.returns.find("]", start)
            if start > 0 and end > start:
                return self.returns[start:end].strip()
        return None

    @property
    def is_iterator(self) -> bool:
        return self.returns is not None and self.returns.startswith("Iterator")

    @property
    def iterator_type(self) -> str | None:
        if self.is_iterator:
            assert self.returns is not None
            # Extract the type inside Iterator[...]
            start = self.returns.find("[") + 1
            end = self.returns.find("]", start)
            if start > 0 and end > start:
                return self.returns[start:end].strip()
        return None

    @property
    def real_return_type(self) -> str | None:
        return self.returns

    @property
    def doc_return_type(self) -> str | None:
        if self.parsed_doc and self.parsed_doc.returns:
            return self.parsed_doc.returns.type_name
        return None

    @property
    def has_doc(self) -> bool:
        return bool(self.doc.strip())

    @property
    def has_return_doc(self) -> bool:
        return (
            self.parsed_doc is not None
            and self.parsed_doc.returns is not None
            and not self.parsed_doc.returns.is_generator
        )

    @property
    def has_yield_doc(self) -> bool:
        return (
            self.parsed_doc is not None
            and self.parsed_doc.returns is not None
            and self.parsed_doc.returns.is_generator
        )


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

            params = (
                {
                    a.arg: ast.unparse(a.annotation)
                    for a in node.args.args
                    if a.annotation is not None
                }
                if node.args
                else None
            )
            yield CodeSegment(
                file_path=filepath,
                code=func_code,
                doc=func_doc,
                lineno=lineno,
                code_path=f"{codepath}",
                parsed_doc=parsed_doc,
                params=params,
                args_name=str(node.args.vararg.arg) if node.args.vararg else None,
                args_type=ast.unparse(node.args.vararg.annotation)
                if node.args.vararg and node.args.vararg.annotation
                else None,
                kwargs_name=str(node.args.kwarg.arg) if node.args.kwarg else None,
                kwargs_type=ast.unparse(node.args.kwarg.annotation)
                if node.args.kwarg and node.args.kwarg.annotation
                else None,
                returns=ast.unparse(node.returns) if node.returns else None,
                seg_type=CodeSegmentType.Function,
            )


def code_docs_from_path(
    path: str | Path, excludes: list[str] | None
) -> Generator[CodeSegment]:
    path = path if isinstance(path, Path) else Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Path {path} is neither a file nor a directory.")

    spec = pathspec.PathSpec.from_lines("gitwildmatch", excludes or [])

    if path.is_file():
        yield from _parse_file(path)
        return

    curr_path = str(path.resolve())
    all_python_files = [
        p
        for p in Path(path).rglob("*.py")
        if not spec.match_file(str(p.resolve())[len(curr_path) + 1 :])
    ]

    # filter out ignored ones
    for p in all_python_files:
        yield from _parse_file(p)
