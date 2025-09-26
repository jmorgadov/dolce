from __future__ import annotations

import json
import logging
import re

from pydolce.config import DolceConfig
from pydolce.core.client import LLMClient
from pydolce.core.parser import (
    CodeSegment,
)
from pydolce.core.prompts import (
    CHECK_SYSTEM_PROMPT_TEMPLATE,
    CHECK_USER_PROMPT_TEMPLATE,
)
from pydolce.core.rules.checkers.common import CheckContext, CheckResult, CheckStatus
from pydolce.core.rules.filters import only_llm, only_static
from pydolce.core.rules.rule import DEFAULT_PREFIX, LLMRule, Rule, StaticRule
from pydolce.core.rules.rulesets import RULE_BY_REF, RULE_REFERENCES
from pydolce.core.utils import extract_json_object

logger = logging.getLogger(__name__)


def _report_from_llm_response(
    json_resp: dict, segment: CodeSegment, rules: list[Rule]
) -> dict[Rule, list[CheckResult]]:
    if json_resp["status"].lower() == CheckStatus.GOOD.value:
        return {rule: [CheckResult.good()] for rule in rules}

    if "issues" not in json_resp or not isinstance(json_resp["issues"], list):
        return {
            rule: [
                CheckResult.unknown(
                    "Status is INCORRECT but no 'issues' field found or it's not a list in LLM response JSON"
                )
            ]
            for rule in rules
        }

    report: dict[Rule, list[CheckResult]] = {}
    for i, issue in enumerate(json_resp.get("issues", [])):
        # if json_resp["issues"]:
        ref_search = re.search(DEFAULT_PREFIX + r"\d{3}", issue)
        if ref_search is None:
            continue

        ref = ref_search[0]
        if ref not in RULE_REFERENCES:
            # Unknown rule reference
            continue
        rule = RULE_BY_REF[ref]
        if rule not in report:
            report[rule] = []

        issue_descr = (
            json_resp["descr"][i]
            if "descr" in json_resp and len(json_resp["descr"]) > i
            else ""
        )
        report[rule].append(CheckResult.bad(issue_descr))

        # issue_str = f"{ref}: {rule_descr}"
        # if issue_descr:
        #     issue_str += f" ({issue_descr})"
        # issues.append(issue_str)
    # json_resp["issues"] = issues

    report.update({rule: [CheckResult.good()] for rule in rules if rule not in report})

    return report

    # return CodeSegmentReport(
    #     segment=segment,
    #     status=DocStatus.INCORRECT,
    #     issues=json_resp["issues"],
    # )


def check_llm_rules(
    segment: CodeSegment, ctx: CheckContext, llm: LLMClient, rules: list[Rule]
) -> dict[Rule, list[CheckResult]] | None:
    if any(not isinstance(r, LLMRule) for r in rules):
        raise ValueError("All llm rules must have prompts")

    filtered_rules = {r: r.validator(segment, ctx) for r in rules}

    for key in list(filtered_rules.keys()):
        if not filtered_rules[key]:
            filtered_rules.pop(key)

    if not filtered_rules:
        return {}

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
        return {
            rule: [CheckResult.unknown("No JSON object found in LLM response")]
            for rule in rules
        }

    if "status" not in json_resp_str:
        return {
            rule: [CheckResult.unknown("No 'status' field found in LLM response JSON")]
            for rule in rules
        }

    json_resp = json.loads(json_resp_str)
    return _report_from_llm_response(json_resp, segment, rules)


def check_segment(
    segment: CodeSegment,
    config: DolceConfig,
    llm: LLMClient | None = None,
    ctx: CheckContext | None = None,
) -> dict[Rule, list[CheckResult]]:
    ctx = CheckContext(config=config) if ctx is None else ctx

    handler = None
    try:
        handler = config.cache_handler
    except Exception as e:
        logger.debug("Not using cache handler: %s", e)
        pass

    report: dict[Rule, list[CheckResult]] = {}

    for rule in only_static(config.rule_set):
        if rule.scopes is not None and segment.seg_type not in rule.scopes:
            continue

        assert isinstance(rule, StaticRule)
        if (
            handler is not None
            and (cached_result := handler.get_check(segment, rule)) is not None
        ):
            report.update({rule: cached_result})
            continue

        results = list(rule.check(segment, ctx))

        if not results:
            continue

        report.update({rule: list(results)})

        if handler is not None:
            handler.set_check(segment, rule, results, sync=True, override=True)

    if llm is None:
        return report

    llm_rules = list(only_llm(config.rule_set))
    llm_rules_to_check: list[Rule] = []

    if handler is not None:
        for rule in llm_rules:
            if rule.scopes is not None and segment.seg_type not in rule.scopes:
                continue
            assert isinstance(rule, LLMRule)
            if (cached_result := handler.get_check(segment, rule)) is not None:
                report.update({rule: cached_result})
                continue

            llm_rules_to_check.append(rule)
    else:
        llm_rules_to_check = llm_rules

    if llm_rules_to_check and segment.doc.strip():
        llm_report = check_llm_rules(segment, ctx, llm, llm_rules_to_check)
        if llm_report is not None:
            report.update(llm_report)

    if handler is not None:
        for rule, rule_report in report.items():
            if rule in llm_rules_to_check:
                handler.set_check(segment, rule, rule_report, sync=True, override=True)

    return report
