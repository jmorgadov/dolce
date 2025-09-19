from pathlib import Path

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.rules import Rule, RuleContext, RuleResult

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


@Rule.register(_id(1), "Docstring has invalid style.")
def invalid_docstring_style(
    segment: CodeSegment, ctx: RuleContext
) -> RuleResult | None:
    if not segment.doc.strip() or segment.parsed_doc is None:
        return None

    if ctx.config.ensure_style is not None:
        used_style = segment.parsed_doc.style
        if used_style is None:
            return RuleResult.bad(
                [
                    f"Docstring style could not be determined, but should be '{ctx.config.ensure_style}'."
                ]
            )
        used_style_name = used_style.name.lower()
        if used_style_name != ctx.config.ensure_style:
            return RuleResult.bad(
                [
                    f"Docstring style is '{used_style_name}', "
                    f"but should be '{ctx.config.ensure_style}'."
                ]
            )

    return RuleResult.good()
