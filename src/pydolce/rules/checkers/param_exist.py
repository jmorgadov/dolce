from pydolce.parser import CodeSegment


def check_params_exist(segment: CodeSegment) -> list[str] | None:
    if segment.args is None or not segment.args or segment.parsed_doc is None:
        return None

    errors = []
    for param in segment.parsed_doc.params:
        p_name = param.arg_name

        if p_name not in segment.args:
            errors.append(f"Parameter '{p_name}' documented but not in signature.")

    return errors if errors else None
