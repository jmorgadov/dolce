from pydolce.parser import CodeSegment, CodeSegmentType
from pydolce.rules.rules import Rule, RuleResult


@Rule.register(201, "Parameter in signature is not documented.")
def missing_param(segment: CodeSegment) -> RuleResult:
    if not segment.doc or segment.parsed_doc is None:
        return RuleResult.good()

    func_params = list(segment.params.keys()) if segment.params else []
    if segment.args_name:
        func_params.append(segment.args_name)
    if segment.kwargs_name:
        func_params.append(segment.kwargs_name)

    if not func_params:
        return RuleResult.good()

    documented_params = {param.arg_name for param in segment.parsed_doc.params}
    return RuleResult.bad_if_any(
        f"Parameter '{p_name}' is not documented."
        for p_name in func_params
        if p_name not in documented_params
    )


@Rule.register(202, "Missing parameter type in docstring.")
def missing_param_type(segment: CodeSegment) -> RuleResult:
    if not segment.params or segment.parsed_doc is None or not segment.doc:
        return RuleResult.good()

    return RuleResult.bad_if_any(
        f"Parameter '{p.arg_name}' is missing a type in the docstring."
        for p in segment.parsed_doc.params
        if p.type_name is None
    )


@Rule.register(203, "Parameter documented type does not match signature.")
def wrong_param_type(segment: CodeSegment) -> RuleResult:
    if segment.params is None or not segment.params or segment.parsed_doc is None:
        return RuleResult.good()

    errors = []
    for param in segment.parsed_doc.params:
        p_name = param.arg_name
        p_type = param.type_name
        if p_type is None:
            # If the type is not documented, skip the check for this parameter
            # There is another rule to check for missing types
            continue

        if p_name not in segment.params:
            # Parameter documented but not in signature
            # There is another rule to check for missing parameters
            continue

        sig_type = segment.params.get(p_name)
        if sig_type is None:
            sig_type = "None"

        if str(sig_type).lower() != p_type.lower():
            errors.append(
                f"Parameter '{p_name}' has type '{sig_type}' in signature but '{p_type}' in docstring."
            )

    return RuleResult.bad_if_any(errors)


@Rule.register(204, "Missing parameter description.")
def missing_param_description(segment: CodeSegment) -> RuleResult:
    if not segment.doc or segment.parsed_doc is None:
        return RuleResult.good()

    return RuleResult.bad_if_any(
        f"Parameter '{param.arg_name}' is missing a description."
        for param in segment.parsed_doc.params
        if param.description is None or not param.description.strip()
    )


@Rule.register(205, "Documented parameter does not exist in signature.")
def params_does_not_exist(segment: CodeSegment) -> RuleResult:
    if (
        segment.params is None
        or not segment.params
        or segment.parsed_doc is None
        or not segment.doc
    ):
        return RuleResult.good()

    return RuleResult.bad_if_any(
        f"Parameter '{param.arg_name}' documented but not in signature."
        for param in segment.parsed_doc.params
        if param.arg_name not in segment.params
    )


@Rule.register(206, "Parameter is documented multiple times in the docstring.")
def duplicate_params(segment: CodeSegment) -> RuleResult:
    if segment.parsed_doc is None:
        return RuleResult.good()

    errors = []
    checked_params = set()
    for param in segment.parsed_doc.params:
        p_name = param.arg_name

        if p_name in checked_params:
            errors.append(
                f"Parameter '{p_name}' is documented multiple times in the docstring."
            )

        checked_params.add(p_name)

    return RuleResult.bad_if_any(errors)


@Rule.register(221, "Missing return section in docstring.")
def missing_return(segment: CodeSegment) -> RuleResult:
    if (
        segment.seg_type != CodeSegmentType.Function
        or segment.parsed_doc is None
        or not segment.doc
    ):
        return RuleResult.good()

    if segment.returns is not None and segment.returns == "None":
        return RuleResult.good()

    return RuleResult.from_bool(segment.parsed_doc.returns is not None)


@Rule.register(222, "Missing return description.")
def missing_return_description(segment: CodeSegment) -> RuleResult:
    if segment.seg_type != CodeSegmentType.Function:
        return RuleResult.good()
    if (
        segment.parsed_doc is None
        or segment.parsed_doc.returns is None
        or (segment.returns is not None and segment.returns == "None")
    ):
        return RuleResult.good()

    ret = segment.parsed_doc.returns
    return RuleResult.from_bool(
        ret.description is not None and ret.description.strip() != ""
    )


@Rule.register(223, "Return documented type does not match signature.")
def wrong_return_type(segment: CodeSegment) -> RuleResult:
    if segment.seg_type != CodeSegmentType.Function:
        return RuleResult.good()
    if (
        segment.returns is None
        or not segment.returns
        or segment.parsed_doc is None
        or segment.parsed_doc.returns is None
    ):
        return RuleResult.good()

    return RuleResult.from_bool(
        segment.returns == segment.parsed_doc.returns.type_name,
        f"Return type is '{segment.returns}' but declared '{segment.parsed_doc.returns.type_name}' in docstring.",
    )
