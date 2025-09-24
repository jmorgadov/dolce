from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext, CheckResult


def invalid_docstring_style(
    segment: CodeSegment, ctx: CheckContext
) -> CheckResult | None:
    """Docstring does not follow the specified style"""
    if not segment.doc.strip() or segment.parsed_doc is None:
        return None

    if ctx.config.ensure_style is not None:
        used_style = segment.parsed_doc.style
        if used_style is None:
            return CheckResult.bad(
                [
                    f"Docstring style could not be determined, but should be '{ctx.config.ensure_style}'."
                ]
            )
        used_style_name = used_style.name.lower()
        if used_style_name != ctx.config.ensure_style:
            return CheckResult.bad(
                [
                    f"Docstring style is '{used_style_name}', "
                    f"but should be '{ctx.config.ensure_style}'."
                ]
            )

    return CheckResult.good()
