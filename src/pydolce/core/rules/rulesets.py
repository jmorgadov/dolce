import hashlib
from typing import Iterable

from pydolce.core.parser import CodeSegmentType
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
from pydolce.core.rules.rule import LLMRule, Rule, StaticRule

RuleSet = Iterable[Rule]

all_scopes = list(CodeSegmentType.__members__.values())
function_scope = [CodeSegmentType.Function]
method_scope = [CodeSegmentType.Method]
class_scope = [CodeSegmentType.Class]
module_scope = [CodeSegmentType.Module]
property_scope = [CodeSegmentType.Property]
callable_scope = [CodeSegmentType.Function, CodeSegmentType.Method]

ALL_RULES: RuleSet = {
    # Structural (1xx)
    StaticRule(101, invalid_docstring_syntax, all_scopes),
    StaticRule(102, missing_module_docstring, module_scope),
    StaticRule(103, missing_class_docstring, class_scope),
    StaticRule(104, missing_method_docstring, method_scope),
    StaticRule(105, missing_func_docstring, function_scope),
    # Style (2xx)
    StaticRule(201, invalid_docstring_style, all_scopes),
    # Signature (3xx)
    StaticRule(301, missing_param, callable_scope),
    StaticRule(302, missing_param_type, callable_scope),
    StaticRule(303, wrong_param_type, callable_scope),
    StaticRule(304, missing_param_description, callable_scope),
    StaticRule(305, params_does_not_exist, callable_scope),
    StaticRule(306, duplicate_params, callable_scope),
    StaticRule(321, missing_return, callable_scope),
    StaticRule(322, missing_return_description, callable_scope),
    StaticRule(323, wrong_return_type, callable_scope),
    StaticRule(324, unnecessary_return, callable_scope),
    StaticRule(325, return_on_property, property_scope),
    StaticRule(341, missing_yield, callable_scope),
    StaticRule(342, missing_yield_description, callable_scope),
    StaticRule(343, wrong_yield_type, callable_scope),
    StaticRule(344, unnecessary_yield, callable_scope),
    # Content (4xx)
    LLMRule(401, description_spelling, all_scopes),
    LLMRule(402, param_desc_spelling, callable_scope),
    LLMRule(403, return_desc_spelling, callable_scope),
    # Semantic (5xx)
    LLMRule(501, func_behavior_mismatch, callable_scope),
    LLMRule(502, func_critical_behavior_omited, callable_scope),
}


RULE_REFERENCES = {rule.reference for rule in ALL_RULES}
RULE_BY_REF = {rule.reference: rule for rule in ALL_RULES}
DEFAULT_RULES = {rule for rule in ALL_RULES if rule.code not in {102}}


def hash_ruleset(ruleset: RuleSet) -> str:
    sorted_rules = sorted(r.reference for r in ruleset)
    hasher = hashlib.sha256()
    hasher.update(",".join(sorted_rules).encode("utf-8"))
    return hasher.hexdigest()
