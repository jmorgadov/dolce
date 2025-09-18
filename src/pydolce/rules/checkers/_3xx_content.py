from pydolce.parser import CodeSegment
from pydolce.rules.rules import Rule, RuleContext


@Rule.llm_register(301, "Docstring description contains spelling errors.")
def description_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The docstring DESCRIPTION contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]"
    )


@Rule.llm_register(302, "Docstring parameter description contains spelling errors.")
def param_desc_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The description of some PARAMETERS contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]"
    )


@Rule.llm_register(303, "Docstring return description contains spelling errors.")
def return_desc_spelling(segment: CodeSegment, _ctx: RuleContext) -> str | None:
    return (
        "The description of the RETURN VALUE contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]"
    )
