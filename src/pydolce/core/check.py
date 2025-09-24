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
from pydolce.core.prompts import (
    CHECK_SYSTEM_PROMPT_TEMPLATE,
    CHECK_USER_PROMPT_TEMPLATE,
)
from pydolce.core.rules.checkers.common import CheckContext
from pydolce.core.rules.filters import only_llm, only_static
from pydolce.core.rules.rule import DEFAULT_PREFIX, LLMRule, Rule
from pydolce.core.rules.rulesets import RULE_BY_REF, RULE_REFERENCES
from pydolce.core.utils import extract_json_object


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
            if ref not in RULE_REFERENCES:
                # Unknown rule reference
                continue
            rule_descr = RULE_BY_REF[ref].description
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
    segment: CodeSegment, ctx: CheckContext, llm: LLMClient, rules: list[Rule]
) -> CodeSegmentReport:
    if any(not isinstance(r, LLMRule) for r in rules):
        raise ValueError("All llm rules must have prompts")

    filtered_rules = {r: r.validator(segment, ctx) for r in rules}

    for key in list(filtered_rules.keys()):
        if not filtered_rules[key]:
            filtered_rules.pop(key)

    if not filtered_rules:
        return CodeSegmentReport.correct(segment)

    rules_list = [
        f"- {rule.reference}: {prompt}" for rule, prompt in filtered_rules.items()
    ]

    sys_prompt = CHECK_SYSTEM_PROMPT_TEMPLATE.format(rules="\n".join(rules_list))
    user_prompt = CHECK_USER_PROMPT_TEMPLATE.format(code=segment.code_str)
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
    ctx: CheckContext | None = None,
) -> CodeSegmentReport:
    ctx = CheckContext(config=config) if ctx is None else ctx
    issues = []

    for rule in only_static(config.rule_set):
        if rule.scopes is not None and segment.seg_type not in rule.scopes:
            continue

        result = rule.validator(segment, ctx)
        if result is None or result.passed:
            continue
        if not result.issues:
            issues.append(f"{rule.reference}: {rule.description}")
            continue
        for error in result.issues:
            issues.append(f"{rule.reference}: {rule.description} ({error})")

    if issues:
        return CodeSegmentReport(
            segment=segment,
            status=DocStatus.INCORRECT,
            issues=issues,
        )

    llm_rules = list(only_llm(config.rule_set))

    if llm is not None and llm_rules and segment.doc.strip():
        llm_report = check_llm_rules(segment, ctx, llm, llm_rules)
        if llm_report.status != DocStatus.CORRECT:
            return llm_report

    return CodeSegmentReport.correct(segment)
