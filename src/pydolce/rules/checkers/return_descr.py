from pydolce.parser import CodeSegment, CodeSegmentType


def check_params_descr(segment: CodeSegment) -> list[str] | None:
    if segment.seg_type != CodeSegmentType.Function:
        return None
    if (
        segment.parsed_doc is None
        or segment.parsed_doc.returns is None
        or (segment.returns is not None and segment.returns == "None")
    ):
        return None

    ret = segment.parsed_doc.returns
    if ret.description is None or not ret.description.strip():
        return []

    return None
