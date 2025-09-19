import ast
from pathlib import Path

from pydolce.parser import CodeSegment, Scopes
from pydolce.rules.rules import Rule, RuleContext, RuleResult

_INDEX = int(Path(__file__).stem[1]) * 100


def _id(n: int) -> int:
    return _INDEX + n


# ----------------------------------------------------------------
#
#   Parameters related rules
#
# ----------------------------------------------------------------


@Rule.register(
    _id(1),
    "Parameter in signature is not documented.",
    scopes=Scopes.functions(),
    docsig_rule="SIG203",
)
def missing_param(segment: CodeSegment, ctx: RuleContext) -> RuleResult | None:
    if not segment.doc or segment.parsed_doc is None:
        return None

    func_params = list(segment.params.keys()) if segment.params else []
    if "self" in func_params:
        func_params.remove("self")

    if not ctx.config.ignore_args and segment.args_name:
        func_params.append(segment.args_name)
    if not ctx.config.ignore_kwargs and segment.kwargs_name:
        func_params.append(segment.kwargs_name)

    if not func_params:
        return RuleResult.good()

    documented_params = {param.arg_name for param in segment.parsed_doc.params}
    return RuleResult.bad_if_any(
        f"Parameter '{p_name}' is not documented."
        for p_name in func_params
        if p_name not in documented_params
    )


@Rule.register(
    _id(2), "Missing parameter type in docstring.", scopes=Scopes.functions()
)
def missing_param_type(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if not segment.params or segment.parsed_doc is None or not segment.doc:
        return None

    return RuleResult.bad_if_any(
        f"Parameter '{p.arg_name}' is missing a type in the docstring."
        for p in segment.parsed_doc.params
        if p.type_name is None
    )


@Rule.register(
    _id(3),
    "Parameter documented type does not match signature.",
    scopes=Scopes.functions(),
)
def wrong_param_type(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if segment.params is None or not segment.params or segment.parsed_doc is None:
        return None

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


@Rule.register(
    _id(4),
    "Missing parameter description.",
    scopes=Scopes.functions(),
    docsig_rule="SIG301",
)
def missing_param_description(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if not segment.doc or segment.parsed_doc is None:
        return None

    return RuleResult.bad_if_any(
        f"Parameter '{param.arg_name}' is missing a description."
        for param in segment.parsed_doc.params
        if param.description is None or not param.description.strip()
    )


@Rule.register(
    _id(5),
    "Documented parameter does not exist in signature.",
    scopes=Scopes.functions(),
    docsig_rule="SIG202",
)
def params_does_not_exist(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if (
        segment.params is None
        or not segment.params
        or segment.parsed_doc is None
        or not segment.doc
    ):
        return None

    return RuleResult.bad_if_any(
        f"Parameter '{param.arg_name}' documented but not in signature."
        for param in segment.parsed_doc.params
        if param.arg_name not in segment.params
    )


@Rule.register(
    _id(6),
    "Parameter is documented multiple times in the docstring.",
    scopes=Scopes.functions(),
    docsig_rule="SIG201",
)
def duplicate_params(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
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

    return RuleResult.bad_if_any(errors)


# ----------------------------------------------------------------
#
#   Returns related rules
#
# ----------------------------------------------------------------


@Rule.register(
    _id(21),
    "Missing return section in docstring.",
    scopes=Scopes.functions(),
    pydoclint_rule="DOC201",
    docsig_rule="SIG503",
)
def missing_return(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if segment.parsed_doc is None or not segment.doc or segment.is_generator:
        return None

    if segment.returns is not None and segment.returns == "None":
        return RuleResult.good()

    # Properties do not need return sections
    if segment.is_property():
        return RuleResult.good()

    return RuleResult.check(segment.parsed_doc.returns is not None)


@Rule.register(
    _id(22),
    "Missing return description.",
    scopes=Scopes.functions(),
    docsig_rule="SIG506",
)
def missing_return_description(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if (
        segment.parsed_doc is None
        or segment.parsed_doc.returns is None
        or (segment.returns is not None and segment.returns == "None")
        or segment.is_generator
        or not segment.has_return_doc
    ):
        return None

    ret = segment.parsed_doc.returns
    return RuleResult.check(
        ret.description is not None and ret.description.strip() != ""
    )


@Rule.register(
    _id(23), "Return type does not match signature.", scopes=Scopes.functions()
)
def wrong_return_type(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if (
        segment.real_return_type is None
        or not segment.has_return_doc
        or segment.parsed_doc is None
        or segment.parsed_doc.returns is None
        or segment.parsed_doc.returns.is_generator
        or segment.is_generator
    ):
        return None

    return RuleResult.check(
        segment.real_return_type == segment.doc_return_type,
        f"Return type is '{segment.real_return_type}' but declared '{segment.doc_return_type}' in docstring.",
    )


@Rule.register(
    _id(24),
    "Unnecessary return section in docstring.",
    scopes=Scopes.functions(),
    pydoclint_rule="DOC202",
    docsig_rule="SIG502",
)
def unnecessary_return(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if (
        segment.doc_return_type is None
        or not segment.has_return_doc
        or segment.is_generator
    ):
        return None

    return RuleResult.check(segment.returns != "None")


@Rule.register(
    _id(25),
    "Return documented on property.",
    scopes=Scopes.functions(),
    docsig_rule="SIG505",
)
def return_on_property(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if segment.parsed_doc is None or not segment.has_return_doc:
        return None

    return RuleResult.check(
        not segment.is_property(), "Properties should not have return sections."
    )


# ----------------------------------------------------------------
#
#   Yields related rules
#
# ----------------------------------------------------------------


@Rule.register(
    _id(41),
    "Missing yield section in docstring.",
    scopes=Scopes.functions(),
    pydoclint_rule="DOC402",
)
def missing_yield(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if (
        segment.real_return_type is None
        or segment.parsed_doc is None
        or not segment.is_generator
    ):
        return None

    return RuleResult.check(
        not segment.is_generator
        or (
            segment.parsed_doc.returns is not None
            and segment.parsed_doc.returns.is_generator
        )
    )


@Rule.register(_id(42), "Missing yield description.", scopes=Scopes.functions())
def missing_yield_description(
    segment: CodeSegment, _ctx: RuleContext
) -> RuleResult | None:
    if (
        segment.parsed_doc is None
        or not segment.is_generator
        or segment.parsed_doc.returns is None
        or not segment.parsed_doc.returns.is_generator
    ):
        return None

    ret = segment.parsed_doc.returns
    return RuleResult.check(
        ret.description is not None and ret.description.strip() != ""
    )


@Rule.register(
    _id(43), "Yield type does not match signature.", scopes=Scopes.functions()
)
def wrong_yield_type(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    if (
        segment.real_return_type is None
        or segment.parsed_doc is None
        or segment.parsed_doc.returns is None
        or not segment.parsed_doc.returns.is_generator
        or not segment.is_generator
        or (
            segment.is_generator and segment.generator_type is None
        )  # No type specified
    ):
        return None

    return RuleResult.check(
        segment.generator_type == segment.parsed_doc.returns.type_name,
        f"Yield type is '{segment.generator_type}' but declared '{segment.parsed_doc.returns.type_name}' in docstring.",
    )


@Rule.register(
    _id(44),
    "Invalid yield section in docstring.",
    scopes=Scopes.functions(),
    pydoclint_rule="DOC403",
)
def unnecessary_yield(segment: CodeSegment, _ctx: RuleContext) -> RuleResult | None:
    return RuleResult.check(not segment.has_yield_doc or segment.is_generator)
