from pathlib import Path

import docstring_parser

from pydolce.parser import CodeSegment, CodeSegmentType
from pydolce.rules.rules import Rule, RuleContext, RuleResult

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


@Rule.register(_id(1), "Docstring has invalid syntax.")
def invalid_docstring_syntax(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.parsed_doc is None:
        return None

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        return RuleResult.bad([f"{e}"])

    return RuleResult.good()


@Rule.register(_id(2), "Function is missing a docstring.", pydocstyle_rule="D103")
def missing_func_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.seg_type == CodeSegmentType.Function and not segment.doc.strip():
        return RuleResult.bad()
    return RuleResult.good()


@Rule.register(_id(3), "Class is missing a docstring.", pydocstyle_rule="D101")
def missing_class_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.seg_type == CodeSegmentType.Class and not segment.doc.strip():
        return RuleResult.bad()
    return RuleResult.good()
