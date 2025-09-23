import hashlib

from pydolce.core.parser import CodeSegment
from pydolce.core.rules.checkers.common import CheckContext
from pydolce.core.rules.checkers.content import (
    description_spelling,
    param_desc_spelling,
    return_desc_spelling,
)
from pydolce.core.rules.checkers.semantic import (
    func_behavior_mismatch,
    func_critical_behavior_omited,
)
from pydolce.core.rules.checkers.signature import (
    duplicate_params,
    missing_param,
    missing_param_description,
    missing_param_type,
    missing_return,
    missing_return_description,
    missing_yield,
    missing_yield_description,
    params_does_not_exist,
    return_on_property,
    unnecessary_return,
    unnecessary_yield,
    wrong_param_type,
    wrong_return_type,
    wrong_yield_type,
)
from pydolce.core.rules.checkers.structural import (
    invalid_docstring_syntax,
    missing_class_docstring,
    missing_func_docstring,
    missing_method_docstring,
    missing_module_docstring,
)
from pydolce.core.rules.checkers.style import invalid_docstring_style
from pydolce.core.rules.filters import exclude, only_llm, without_llm
from pydolce.core.rules.rule import DEFAULT_PREFIX, Rule
from pydolce.types import RuleSet

all_rules: set[Rule] = {
    # Structural (1xx)
    Rule(101, "Docstring has invalid syntax.", invalid_docstring_syntax),
    Rule(102, "Module is missing a docstring.", missing_module_docstring),
    Rule(103, "Class is missing a docstring.", missing_class_docstring),
    Rule(104, "Method is missing a docstring.", missing_method_docstring),
    Rule(105, "Function is missing a docstring.", missing_func_docstring),
    # Style (2xx)
    Rule(201, "Docstring has invalid style.", invalid_docstring_style),
    # Signature (3xx)
    Rule(301, "Parameter in signature is not documented.", missing_param),
    Rule(302, "Missing parameter type in docstring.", missing_param_type),
    Rule(303, "Parameter documented type does not match signature.", wrong_param_type),
    Rule(304, "Missing parameter description.", missing_param_description),
    Rule(305, "Parameter doesn't exist in signature.", params_does_not_exist),
    Rule(306, "Parameter is documented multiple times.", duplicate_params),
    Rule(321, "Missing return section in docstring.", missing_return),
    Rule(322, "Missing return description.", missing_return_description),
    Rule(323, "Return type does not match signature.", wrong_return_type),
    Rule(324, "Unnecessary return section in docstring.", unnecessary_return),
    Rule(325, "Return documented on property.", return_on_property),
    Rule(341, "Missing yield section in docstring.", missing_yield),
    Rule(342, "Missing yield description.", missing_yield_description),
    Rule(343, "Yield type does not match signature.", wrong_yield_type),
    Rule(344, "Invalid yield section in docstring.", unnecessary_yield),
    # Content (4xx)
    Rule(
        401,
        "Docstring description contains spelling errors.",
        prompter=description_spelling,
    ),
    Rule(
        402,
        "Docstring parameter description contains spelling errors.",
        prompter=param_desc_spelling,
    ),
    Rule(
        403,
        "Docstring return description contains spelling errors.",
        prompter=return_desc_spelling,
    ),
    # Semantic (5xx)
    Rule(
        501,
        "Description is not consistent with the function implementation.",
        prompter=func_behavior_mismatch,
    ),
    Rule(
        502, "Critical behavior not documented.", prompter=func_critical_behavior_omited
    ),
}


default_rules = exclude(
    [f"{DEFAULT_PREFIX}{code:03d}" for code in {102}],
    all_rules,
)


llm_based_rules = only_llm(all_rules)
non_llm_based_rules = without_llm(all_rules)


def check(ruleset: RuleSet, segment: CodeSegment, ctx: CheckContext) -> list[str]:
    issues = []
    for rule in ruleset:
        if rule.checker is not None and (
            rule.scopes is None or segment.seg_type in rule.scopes
        ):
            result = rule.checker(segment, ctx)
            if result is None or result.passed:
                continue
            if not result.issues:
                issues.append(f"{rule.reference}: {rule.description}")
                continue
            for error in result.issues:
                issues.append(f"{rule.reference}: {rule.description} ({error})")
    return issues


def hash_ruleset(ruleset: RuleSet) -> str:
    sorted_rules = sorted(r.reference for r in ruleset)
    hasher = hashlib.sha256()
    hasher.update(",".join(sorted_rules).encode("utf-8"))
    return hasher.hexdigest()
