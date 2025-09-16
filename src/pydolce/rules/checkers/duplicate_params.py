from pydolce.parser import CodeSegment


def check_duplicate_params(segment: CodeSegment) -> list[str] | None:
    if segment.parsed_doc is None:
        return None

    errors = []
    checked_params = set()
    for param in segment.parsed_doc.params:
        p_name = param.arg_name

        if p_name in checked_params:
            errors.append(
                f"Parameter '{p_name}' is documented multiple times in the docstring."
            )

        checked_params.add(p_name)

    return errors if errors else None
