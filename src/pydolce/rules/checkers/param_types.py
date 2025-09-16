from pydolce.parser import CodeSegment


def check_params_type(segment: CodeSegment) -> list[str] | None:
    if segment.args is None or not segment.args or segment.parsed_doc is None:
        return None

    errors = []
    for param in segment.parsed_doc.params:
        p_name = param.arg_name
        p_type = param.type_name
        if p_type is None:
            # If the type is not documented, skip the check for this parameter
            # There is another rule to check for missing types
            continue

        if p_name not in segment.args:
            # Parameter documented but not in signature
            # There is another rule to check for missing parameters
            continue

        sig_type = segment.args.get(p_name)
        if sig_type is None:
            sig_type = "None"

        if str(sig_type).lower() != p_type.lower():
            errors.append(
                f"Parameter '{p_name}' has type '{sig_type}' in signature but '{p_type}' in docstring."
            )

    return errors if errors else None
