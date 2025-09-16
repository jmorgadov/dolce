from pydolce.parser import CodeSegment


def check_params_descr(segment: CodeSegment) -> list[str] | None:
    if segment.parsed_doc is None:
        return None

    errors = []
    for param in segment.parsed_doc.params:
        p_descr = param.description
        if p_descr is None or not p_descr.strip():
            errors.append(f"Parameter '{param.arg_name}' is missing a description.")

    return errors if errors else None
