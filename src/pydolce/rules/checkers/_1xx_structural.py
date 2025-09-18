import docstring_parser

from pydolce.parser import CodeSegment, CodeSegmentType
from pydolce.rules.rules import Rule, RuleContext, RuleResult


@Rule.register(101, "Docstring has invalid syntax.")
def invalid_docstring_syntax(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.parsed_doc is not None:
        return None

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        return RuleResult.bad([f"{e}"])

    return RuleResult.good()


@Rule.register(102, "Function is missing a docstring.")
def missing_func_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.seg_type == CodeSegmentType.Function and not segment.doc.strip():
        return RuleResult.bad()
    return RuleResult.good()


@Rule.register(103, "Class is missing a docstring.")
def missing_class_docstring(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if segment.seg_type == CodeSegmentType.Class and not segment.doc.strip():
        return RuleResult.bad()
    return RuleResult.good()
