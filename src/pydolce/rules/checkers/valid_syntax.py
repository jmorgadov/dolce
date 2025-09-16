import docstring_parser

from pydolce.parser import CodeSegment


def check_valid_syntax(segment: CodeSegment) -> list[str] | None:
    if segment.parsed_doc is not None:
        return None

    try:
        docstring_parser.parse(segment.doc)
    except docstring_parser.ParseError as e:
        return [f"{e}"]

    return None
