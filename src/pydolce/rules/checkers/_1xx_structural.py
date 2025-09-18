import ast
from pathlib import Path

import docstring_parser

from pydolce.parser import CodeSegment, Scopes
from pydolce.rules.rules import Rule, RuleContext, RuleResult

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


@Rule.register(_id(1), "Docstring has invalid syntax.", docsig_rule="SIG901")
def invalid_docstring_syntax(
    segment: CodeSegment,
    _ctx: RuleContext,
) -> RuleResult | None:
    if segment.parsed_doc is None:
        return None

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        return RuleResult.bad([f"{e}"])

    return RuleResult.good()


@Rule.register(
    _id(2),
    "Module is missing a docstring.",
    scopes=Scopes.modules(),
    pydocstyle_rule="D100",
)
def missing_module_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    return RuleResult.check(bool(segment.doc.strip()))


@Rule.register(
    _id(3),
    "Class is missing a docstring.",
    scopes=Scopes.classes(),
    pydocstyle_rule="D101",
    docsig_rule="SIG102",
)
def missing_class_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    return RuleResult.check(bool(segment.doc.strip()))


@Rule.register(
    _id(4),
    "Method is missing a docstring.",
    scopes=Scopes.methods(),
    pydocstyle_rule="D102",
)
def missing_method_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    return RuleResult.check(bool(segment.doc.strip()))


@Rule.register(
    _id(5),
    "Function is missing a docstring.",
    scopes=Scopes.non_method_funcs(),
    pydocstyle_rule="D103",
    docsig_rule="SIG101",
)
def missing_func_docstring(segment: CodeSegment, ctx: RuleContext) -> RuleResult | None:
    if ctx.config.ignore_private_functions:
        assert isinstance(segment.code_node, (ast.FunctionDef, ast.AsyncFunctionDef))
        if segment.code_node.name.startswith("_"):
            return None
    return RuleResult.check(bool(segment.doc.strip()))
