from __future__ import annotations

import json
import re

from pydolce.config import DolceConfig
from pydolce.core.client import LLMClient
from pydolce.core.parser import (
    CodeSegment,
    CodeSegmentReport,
    DocStatus,
)
from pydolce.core.rules.rules import DEFAULT_PREFIX, Rule, RuleContext
from pydolce.core.utils import extract_json_object


def ruled_check_prompts(
    function_code: str,
    rules: list[str],
) -> tuple[str, str]:
    """
    Create system and user prompts for the model to check if docstring follows the defined rules.

    This will NOT check parameters, returns values, or any other section but the
    main description of the docstring.

    This will NOT check for completeness, only for CRITICAL inconsistencies.

    Args:
        function_code (str): The Python function code to analyze
        rules (list[str]): List of rules to check, each as a string

    Returns:
        tuple[str, str]: Tuple of (system_prompt, user_prompt)
    """

    rules_str = "\n".join(rules)
    system_prompt = """You are an expert Python docstring analyzer. Your task is to analyze if a Python function docstring follows a set of defined rules."""

    system_prompt += f"""
Analysis scopes:
- DOCSTRING: The entire docstring, including all sections.
- DESCRIPTION: The main description of the docstring.
- PARAM_DESCRIPTION: The description of each parameter in the docstring.
- RETURN_DESCRIPTION: The description of the return value in the docstring.
- DOC_PARAM: The entire parameter section of the docstring.
- PARAMS: The parameters in the function signature.
- CODE: The actual code of the function.

RULES TO CHECK:
{rules_str}
"""

    system_prompt += """
Go rule by rule, and check if the docstring violates any of them independently of the others. For each rule use only the scope information provided in the rule description to determine if the rule is violated or not.

EXACT OUTPUT FORMAT IN JSON:

```
{
    "status": "[CORRECT/INCORRECT]",
    "issues": [List of specific rules references (DOCXXX) that were violated. Empty if status is CORRECT.]
    "descr": [List of specific descriptions of the issues found, one per issue. No more than one sentence. Empty if status is CORRECT.]
}
```

VERY IMPORTANT: NEVER ADD ANY EXTRA COMENTARY OR DESCRIPTION. STICK TO THE EXACT OUTPUT FORMAT.
"""

    user_prompt = f"""
Check this code:
```python
{function_code.strip()}
```
"""
    return system_prompt, user_prompt


def _report_from_llm_response(
    json_resp: dict, segment: CodeSegment
) -> CodeSegmentReport:
    if json_resp["status"] == DocStatus.CORRECT.value:
        return CodeSegmentReport.correct(segment)

    if "issues" not in json_resp or not isinstance(json_resp["issues"], list):
        return CodeSegmentReport.unknown(
            segment,
            issues=[
                "Status is INCORRECT but no 'issues' field found or it's not a list in LLM response JSON"
            ],
        )

    if json_resp["issues"]:
        issues = []
        for i, issue in enumerate(json_resp["issues"]):
            ref_search = re.search(DEFAULT_PREFIX + r"\d{3}", issue)
            if ref_search is None:
                # Unknown issue format
                continue

            ref = ref_search[0]
            if not Rule.is_ref_registered(ref):
                # Unknown rule reference
                continue
            rule_descr = Rule.all_rules[ref].description
            issue_descr = (
                json_resp["descr"][i]
                if "descr" in json_resp and len(json_resp["descr"]) > i
                else ""
            )

            issue_str = f"{ref}: {rule_descr}"
            if issue_descr:
                issue_str += f" ({issue_descr})"
            issues.append(issue_str)
        json_resp["issues"] = issues

    return CodeSegmentReport(
        segment=segment,
        status=DocStatus.INCORRECT,
        issues=json_resp["issues"],
    )


def check_llm_rules(
    segment: CodeSegment, ctx: RuleContext, llm: LLMClient, rules: list[Rule]
) -> CodeSegmentReport:
    if any(r.prompter is None for r in rules):
        raise ValueError("All llm rules must have prompts")

    filtered_rules = {
        r: r.prompter(segment, ctx) for r in rules if r.prompter is not None
    }

    for key in list(filtered_rules.keys()):
        if not filtered_rules[key]:
            filtered_rules.pop(key)

    if not filtered_rules:
        return CodeSegmentReport.correct(segment)

    rules_list = [f"- {rule.ref}: {prompt}" for rule, prompt in filtered_rules.items()]
    sys_prompt, user_prompt = ruled_check_prompts(
        function_code=segment.code_str, rules=rules_list
    )
    response = llm.generate(
        prompt=user_prompt,
        system=sys_prompt,
    )

    json_resp_str = extract_json_object(response)

    if json_resp_str is None:
        return CodeSegmentReport.unknown(
            segment, issues=["No JSON object found in LLM response"]
        )

    if "status" not in json_resp_str:
        return CodeSegmentReport.unknown(
            segment, issues=["No 'status' field found in LLM response JSON"]
        )

    json_resp = json.loads(json_resp_str)
    return _report_from_llm_response(json_resp, segment)


def check_segment(
    segment: CodeSegment,
    config: DolceConfig,
    llm: LLMClient | None = None,
    ctx: RuleContext | None = None,
) -> CodeSegmentReport:
    assert config.rule_set is not None, "Rule set must be defined in config"

    ctx = RuleContext(config=config) if ctx is None else ctx
    quick_issues = config.rule_set.check(segment, ctx)
    if quick_issues:
        return CodeSegmentReport(
            segment=segment,
            status=DocStatus.INCORRECT,
            issues=quick_issues,
        )

    if llm is not None and segment.doc.strip():
        desc_report = check_llm_rules(segment, ctx, llm, config.rule_set.llm_rules())

        if desc_report.status != DocStatus.CORRECT:
            return desc_report

    return CodeSegmentReport.correct(segment)
