from pydolce.parser import CodeSegment


def check_params_type_missing(segment: CodeSegment) -> list[str] | None:
    if segment.args is None or not segment.args or segment.parsed_doc is None:
        return None

    errors = []
    for param in segment.parsed_doc.params:
        p_name = param.arg_name
        p_type = param.type_name
        if p_type is None:
            errors.append(f"Parameter '{p_name}' is missing a type in the docstring.")

    return errors if errors else None
