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
    Method = auto()
    Class = auto()
    Module = auto()


class Scopes:
    @staticmethod
    def functions() -> list[CodeSegmentType]:
        return [CodeSegmentType.Function, CodeSegmentType.Method]

    @staticmethod
    def non_method_funcs() -> list[CodeSegmentType]:
        return [CodeSegmentType.Function]

    @staticmethod
    def methods() -> list[CodeSegmentType]:
        return [CodeSegmentType.Method]

    @staticmethod
    def classes() -> list[CodeSegmentType]:
        return [CodeSegmentType.Class]

    @staticmethod
    def modules() -> list[CodeSegmentType]:
        return [CodeSegmentType.Module]


def get_function_head(node: ast.FunctionDef) -> str:
    """Get the head of a function definition (FunctionDef)"""
    if not isinstance(node, ast.FunctionDef):
        raise TypeError("Expected ast.FunctionDef node")

    parts = []

    # Add decorators
    if node.decorator_list:
        for decorator in node.decorator_list:
            parts.append(f"@{ast.unparse(decorator)}")

    # Function definition
    func_def = f"def {node.name}("

    # Arguments
    args_parts = []

    # Regular arguments with defaults
    num_defaults = len(node.args.defaults)
    num_args = len(node.args.args)

    for i, arg in enumerate(node.args.args):
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"

        # Check if this argument has a default value
        default_index = i - (num_args - num_defaults)
        if default_index >= 0:
            default_value = ast.unparse(node.args.defaults[default_index])
            arg_str += f" = {default_value}"

        args_parts.append(arg_str)

    # Keyword-only arguments with defaults
    for i, arg in enumerate(node.args.kwonlyargs):
        arg_str = arg.arg
        if arg.annotation:
            arg_str += f": {ast.unparse(arg.annotation)}"

        # kwonlyargs defaults are in kw_defaults list (can contain None)
        if i < len(node.args.kw_defaults) and node.args.kw_defaults[i] is not None:
            _default = node.args.kw_defaults[i]
            assert _default is not None
            default_value = ast.unparse(_default)
            arg_str += f" = {default_value}"

        args_parts.append(arg_str)

    # *args
    if node.args.vararg:
        vararg_str = f"*{node.args.vararg.arg}"
        if node.args.vararg.annotation:
            vararg_str += f": {ast.unparse(node.args.vararg.annotation)}"
        args_parts.append(vararg_str)

    # **kwargs
    if node.args.kwarg:
        kwarg_str = f"**{node.args.kwarg.arg}"
        if node.args.kwarg.annotation:
            kwarg_str += f": {ast.unparse(node.args.kwarg.annotation)}"
        args_parts.append(kwarg_str)

    func_def += ", ".join(args_parts) + ")"

    # Return annotation
    if node.returns:
        func_def += f" -> {ast.unparse(node.returns)}"

    func_def += ":"
    parts.append(func_def)

    parts = [" " * node.col_offset + part for part in parts]

    return "\n".join(parts)


def get_async_function_head(node: ast.AsyncFunctionDef) -> str:
    """Get the head of an async function definition (AsyncFunctionDef)"""
    if not isinstance(node, ast.AsyncFunctionDef):
        raise TypeError("Expected ast.AsyncFunctionDef node")

    # Convert to regular FunctionDef temporarily to reuse logic
    temp_func = ast.FunctionDef(
        name=node.name,
        args=node.args,
        body=node.body,
        decorator_list=node.decorator_list,
        returns=node.returns,
    )

    # Get the regular function head and replace "def" with "async def"
    result = get_function_head(temp_func)
    return result.replace(f"def {node.name}", f"async def {node.name}")


def get_class_head(node: ast.ClassDef) -> str:
    """Get the head of a class definition (ClassDef)"""
    if not isinstance(node, ast.ClassDef):
        raise TypeError("Expected ast.ClassDef node")

    parts = []

    # Add decorators
    if node.decorator_list:
        for decorator in node.decorator_list:
            parts.append(f"@{ast.unparse(decorator)}")

    # Class definition
    class_def = f"class {node.name}"

    # Base classes and keywords
    if node.bases or node.keywords:
        bases_and_keywords = []

        # Base classes
        for base in node.bases:
            bases_and_keywords.append(ast.unparse(base))

        # Keyword arguments (like metaclass=...)
        for keyword in node.keywords:
            bases_and_keywords.append(f"{keyword.arg}={ast.unparse(keyword.value)}")

        class_def += f"({', '.join(bases_and_keywords)})"

    class_def += ":"
    parts.append(class_def)
    parts = [" " * node.col_offset + part for part in parts]

    return "\n".join(parts)


def get_node_head(node: ast.AST) -> str:
    """Get the head of any supported AST node type"""
    if isinstance(node, ast.FunctionDef):
        return get_function_head(node)
    elif isinstance(node, ast.AsyncFunctionDef):
        return get_async_function_head(node)
    elif isinstance(node, ast.ClassDef):
        return get_class_head(node)
    else:
        raise TypeError(f"Unsupported node type: {type(node).__name__}")


class ModuleHeaders:
    def __init__(self, filepath: str | Path) -> None:
        self.filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        self.headers: dict[int, str] = {}
        self.indentations: dict[int, int] = {}
        self._parse()

        for lineno, header in self.headers.items():
            stripped = header.lstrip()
            self.indentations[lineno] = len(header) - len(stripped)

    def _parse(self) -> None:
        code = self.filepath.read_text()
        visitor = ModuleHeadersVisitor()
        visitor.visit(ast.parse(code))
        self.headers = visitor.headers

    def __str__(self) -> str:
        lines = []
        for lineno in sorted(self.headers.keys()):
            lines.append(f"{self.headers[lineno]}")
        return "\n".join(lines)


class ModuleHeadersVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.headers: dict[int, str] = {}

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        lineno = node.lineno if hasattr(node, "lineno") else 1
        self.headers[lineno] = get_function_head(node)
        self.generic_visit(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        lineno = node.lineno if hasattr(node, "lineno") else 1
        self.headers[lineno] = get_async_function_head(node)
        self.generic_visit(node)

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        lineno = node.lineno if hasattr(node, "lineno") else 1
        self.headers[lineno] = get_class_head(node)
        self.generic_visit(node)


class CodeSegmentVisitor(ast.NodeVisitor):
    def __init__(self, filepath: str | Path) -> None:
        self.filepath = filepath if isinstance(filepath, Path) else Path(filepath)
        self.segments: list[CodeSegment] = []
        self._inside_class: ast.ClassDef | None = None
        self._class_init_visited: ast.FunctionDef | None = None

    def _with_func_fileds(
        self, segment: CodeSegment, node: ast.FunctionDef | ast.AsyncFunctionDef
    ) -> CodeSegment:
        params = (
            {
                a.arg: ast.unparse(a.annotation)
                for a in node.args.args
                if a.annotation is not None
            }
            if node.args
            else None
        )

        segment.params = params
        segment.args_name = str(node.args.vararg.arg) if node.args.vararg else None
        segment.args_type = (
            ast.unparse(node.args.vararg.annotation)
            if node.args.vararg and node.args.vararg.annotation
            else None
        )
        segment.kwargs_name = str(node.args.kwarg.arg) if node.args.kwarg else None
        segment.kwargs_type = (
            ast.unparse(node.args.kwarg.annotation)
            if node.args.kwarg and node.args.kwarg.annotation
            else None
        )

        segment.returns = ast.unparse(node.returns) if node.returns else None

        return segment

    def get_docstring_with_location(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
    ) -> dict | None:
        """
        Extract docstring from a function AST node with exact location information.

        Args:
            func_node: ast.FunctionDef or ast.AsyncFunctionDef node

        Returns:
            dict with 'value', 'lineno', 'col_offset', 'end_lineno', 'end_col_offset'
            or None if no docstring found
        """
        if not isinstance(
            node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Module)
        ):
            raise ValueError("Expected FunctionDef or AsyncFunctionDef node")

        # Check if function has any statements
        if not node.body:
            return None

        # Get the first statement
        first_stmt = node.body[0]

        # Check if it's an Expr node containing a string literal
        if isinstance(first_stmt, ast.Expr) and isinstance(
            first_stmt.value, ast.Constant
        ):
            if isinstance(first_stmt.value.value, str):
                # This is the docstring
                string_node = first_stmt.value
                return {
                    "value": string_node.value,
                    "lineno": string_node.lineno,
                    "col_offset": string_node.col_offset,
                    "end_lineno": string_node.end_lineno,
                    "end_col_offset": string_node.end_col_offset,
                }

        # For Python < 3.8, string literals might be ast.Str instead of ast.Constant
        elif isinstance(first_stmt, ast.Expr) and isinstance(first_stmt.value, ast.Str):
            string_node = first_stmt.value
            return {
                "value": string_node.s,
                "lineno": string_node.lineno,
                "col_offset": string_node.col_offset,
                "end_lineno": getattr(string_node, "end_lineno", None),
                "end_col_offset": getattr(string_node, "end_col_offset", None),
            }

        return None

    def _get_code_segment(
        self, node: ast.FunctionDef | ast.AsyncFunctionDef | ast.ClassDef | ast.Module
    ) -> CodeSegment:
        if (
            self._inside_class
            and isinstance(node, ast.FunctionDef)
            and node.name == "__init__"
        ):
            self._class_init_visited = node

        code_str = ast.unparse(node)
        func_doc = ast.get_docstring(node, clean=False) or ""
        lineno = node.lineno if hasattr(node, "lineno") else 1
        end_lineno = (
            node.end_lineno
            if hasattr(node, "end_lineno") and node.end_lineno is not None
            else lineno + len(code_str.splitlines()) - 1
        )
        node_name = node.name if hasattr(node, "name") else self.filepath.stem
        col_offset = node.col_offset if hasattr(node, "col_offset") else 0

        codepath = (
            str(self.filepath)
            if isinstance(node, ast.Module)
            else f"{self.filepath}:{lineno} {node_name}"
        )

        parsed_doc = None
        try:
            parsed_doc = parse(func_doc)
        except ParseError:
            pass

        head = get_node_head(node) if not isinstance(node, ast.Module) else ""

        segment = CodeSegment(
            file_path=self.filepath,
            code_str=code_str,
            col_offset=col_offset,
            code_node=node,
            doc=func_doc,
            lineno=lineno,
            endlineno=end_lineno,
            code_path=f"{codepath}",
            parsed_doc=parsed_doc,
            code_head=head,
        )

        doc_loc = self.get_docstring_with_location(node)
        if doc_loc is not None:
            segment.doc_lineno = doc_loc["lineno"]
            segment.doc_col_offset = doc_loc["col_offset"]
            segment.doc_end_lineno = doc_loc["end_lineno"]

        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment = self._with_func_fileds(segment, node)

        if isinstance(node, ast.Module):
            segment.seg_type = CodeSegmentType.Module
        elif isinstance(node, ast.ClassDef):
            segment.seg_type = CodeSegmentType.Class
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            segment.seg_type = (
                CodeSegmentType.Method
                if self._inside_class is not None
                else CodeSegmentType.Function
            )
        return segment

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self.generic_visit(node)
        self.segments.append(self._get_code_segment(node))

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self.generic_visit(node)
        self.segments.append(self._get_code_segment(node))

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self.segments.append(self._get_code_segment(node))
        self._inside_class = node
        self.generic_visit(node)
        self._inside_class = None

    def visit_Module(self, node: ast.Module) -> None:
        self.segments.append(self._get_code_segment(node))
        self.generic_visit(node)


@dataclass
class CodeSegment:
    """A class to hold a code segment and its corresponding docstring."""

    file_path: Path
    code_path: str
    col_offset: int
    lineno: int
    endlineno: int
    doc: str
    code_str: str
    code_head: str
    code_node: ast.AST | None
    parsed_doc: Docstring | None
    seg_type: CodeSegmentType = CodeSegmentType.Function

    # Docstring location info
    doc_lineno: int | None = None
    doc_end_lineno: int | None = None
    doc_col_offset: int | None = None

    # Function/method specific
    params: dict[str, str] | None = None
    args_name: str | None = None
    args_type: str | None = None
    kwargs_name: str | None = None
    kwargs_type: str | None = None
    returns: str | None = None

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

    def is_property(self) -> bool:
        if not isinstance(self.code_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            return False
        is_property = False
        for decorator in self.code_node.decorator_list:
            if isinstance(decorator, ast.Name) and decorator.id == "property":
                is_property = True
                break
            elif isinstance(decorator, ast.Attribute) and decorator.attr in [
                "setter",
                "setter",
                "deleter",
            ]:
                is_property = True
                break
            elif (
                isinstance(decorator, ast.Call)
                and isinstance(decorator.func, ast.Name)
                and decorator.func.id == "property"
            ):
                is_property = True
                break
        return is_property

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
        """Whether the segment has a non-empty docstring."""
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
    UNKNOWN = "UNKNOWN"


@dataclass
class CodeSegmentReport:
    status: DocStatus
    issues: list[str]
    segment: CodeSegment

    @staticmethod
    def correct(segment: CodeSegment) -> CodeSegmentReport:
        return CodeSegmentReport(status=DocStatus.CORRECT, issues=[], segment=segment)

    @staticmethod
    def unknown(
        segment: CodeSegment, issues: list[str] | None = None
    ) -> CodeSegmentReport:
        return CodeSegmentReport(
            status=DocStatus.UNKNOWN, issues=issues or [], segment=segment
        )

    @staticmethod
    def incorrect(
        segment: CodeSegment, issues: list[str] | None = None
    ) -> CodeSegmentReport:
        return CodeSegmentReport(
            status=DocStatus.INCORRECT, issues=issues or [], segment=segment
        )


def _parse_file(filepath: Path) -> list[CodeSegment]:
    code = filepath.read_text()
    visitor = CodeSegmentVisitor(filepath)
    visitor.visit(ast.parse(code))
    return visitor.segments


def code_segments_from_path(
    path: str | Path, excludes: list[str] | None
) -> Generator[CodeSegment]:
    path = path if isinstance(path, Path) else Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")
    if not path.is_file() and not path.is_dir():
        raise ValueError(f"Path {path} is neither a file nor a directory.")

    spec = pathspec.PathSpec.from_lines("gitwildmatch", excludes or [])

    if path.is_file():
        for seg in _parse_file(path):
            yield seg
        return

    curr_path = str(path.resolve())
    all_python_files = [
        p
        for p in Path(path).rglob("*.py")
        if not spec.match_file(str(p.resolve())[len(curr_path) + 1 :])
    ]

    # filter out ignored ones
    for p in all_python_files:
        for seg in _parse_file(p):
            yield seg
