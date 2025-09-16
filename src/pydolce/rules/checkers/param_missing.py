from pydolce.parser import CodeSegment


def check_params_missing(segment: CodeSegment) -> list[str] | None:
    if segment.args is None or not segment.args or segment.parsed_doc is None:
        return None

    documented_params = {param.arg_name for param in segment.parsed_doc.params}
    errors = []
    for p_name in segment.args:
        if p_name not in documented_params:
            errors.append(f"Parameter '{p_name}' in signature but not documented.")

    return errors if errors else None
