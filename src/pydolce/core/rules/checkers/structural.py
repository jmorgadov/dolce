import ast
from typing import Generator

import docstring_parser

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext, CheckResult


def invalid_docstring_syntax(
    segment: CodeSegment,
    _ctx: CheckContext,
) -> Generator[CheckResult]:
    """Docstring has invalid syntax"""
    if segment.parsed_doc is None:
        return

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        yield CheckResult.bad(str(e))

    yield CheckResult.good()


def missing_module_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> Generator[CheckResult]:
    """Module has no docstring"""
    yield CheckResult.check(bool(segment.doc.strip()))


def missing_class_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> Generator[CheckResult]:
    """Class has no docstring"""
    yield CheckResult.check(bool(segment.doc.strip()))


def missing_method_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> Generator[CheckResult]:
    """Method has no docstring"""
    yield CheckResult.check(bool(segment.doc.strip()))


def missing_func_docstring(
    segment: CodeSegment, ctx: CheckContext
) -> Generator[CheckResult]:
    """Function has no docstring"""
    if ctx.config.ignore_private_functions and isinstance(
        segment.code_node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        if segment.code_node.name.startswith("_"):
            return
    yield CheckResult.check(bool(segment.doc.strip()))
