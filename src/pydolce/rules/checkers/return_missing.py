from pydolce.parser import CodeSegment, CodeSegmentType


def check_return_missing(segment: CodeSegment) -> list[str] | None:
    if segment.seg_type != CodeSegmentType.Function:
        return None

    if segment.parsed_doc is None:
        return None

    if segment.returns is not None and segment.returns == "None":
        return None

    return [] if not segment.parsed_doc.returns else None
