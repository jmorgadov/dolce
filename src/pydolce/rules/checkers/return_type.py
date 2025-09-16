from pydolce.parser import CodeSegment, CodeSegmentType


def check_return_type(segment: CodeSegment) -> list[str] | None:
    if segment.seg_type != CodeSegmentType.Function:
        return None
    if (
        segment.returns is None
        or not segment.returns
        or segment.parsed_doc is None
        or segment.parsed_doc.returns is None
    ):
        return None

    if segment.returns != segment.parsed_doc.returns.type_name:
        return [
            f"Return type is '{segment.returns}' in signature but '{segment.parsed_doc.returns.type_name}' in docstring."
        ]

    return None
