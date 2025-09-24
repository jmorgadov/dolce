from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext


def description_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    """Docstring description contains typos"""
    return (
        "The docstring DESCRIPTION contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [DESCRIPTION]"
    )


def param_desc_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    """Parameter description contains typos"""
    return (
        "The description of some PARAMETERS contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [PARAM_DESCRIPTION]"
    )


def return_desc_spelling(segment: CodeSegment, _ctx: CheckContext) -> str | None:
    """Return value description contains typos"""
    return (
        "The description of the RETURN VALUE contains TYPOS. Examples: 'functon' instead of 'function', "
        "'retrun' instead of 'return'. Report the specific typos. Scopes: [RETURN_DESCRIPTION]"
    )
