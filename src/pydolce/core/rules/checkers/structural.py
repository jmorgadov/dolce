import ast

import docstring_parser

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext, CheckResult


def invalid_docstring_syntax(
    segment: CodeSegment,
    _ctx: CheckContext,
) -> CheckResult | None:
    """Docstring has invalid syntax"""
    if segment.parsed_doc is None:
        return None

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        return CheckResult.bad([f"{e}"])

    return CheckResult.good()


def missing_module_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> CheckResult | None:
    """Module has no docstring"""
    return CheckResult.check(bool(segment.doc.strip()))


def missing_class_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> CheckResult | None:
    """Class has no docstring"""
    return CheckResult.check(bool(segment.doc.strip()))


def missing_method_docstring(
    segment: CodeSegment, _ctx: CheckContext
) -> CheckResult | None:
    """Method has no docstring"""
    return CheckResult.check(bool(segment.doc.strip()))


def missing_func_docstring(
    segment: CodeSegment, ctx: CheckContext
) -> CheckResult | None:
    """Function has no docstring"""
    if ctx.config.ignore_private_functions and isinstance(
        segment.code_node, (ast.FunctionDef, ast.AsyncFunctionDef)
    ):
        if segment.code_node.name.startswith("_"):
            return None
    return CheckResult.check(bool(segment.doc.strip()))
