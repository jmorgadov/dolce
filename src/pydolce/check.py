from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Counter

import rich

from pydolce.client import LLMClient, LLMConfig
from pydolce.config import DolceConfig
from pydolce.parser import (
    CodeSegment,
    CodeSegmentReport,
    DocStatus,
    code_docs_from_path,
)
from pydolce.rules.rules import DEFAULT_PREFIX, Rule, RuleContext


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


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start : i + 1]

    return None


def _print_summary(responses: list[CodeSegmentReport]) -> None:
    statuses_count = Counter(resp.status for resp in responses)
    rich.print("\n[bold]Summary:[/bold]")
    if DocStatus.CORRECT in statuses_count:
        rich.print(f"[green]✓ Correct: {statuses_count[DocStatus.CORRECT]}[/green]")
    if DocStatus.INCORRECT in statuses_count:
        rich.print(f"[red]✗ Incorrect: {statuses_count[DocStatus.INCORRECT]}[/red]")


def check_description(
    codeseg: CodeSegment, ctx: RuleContext, llm: LLMClient, rules: list[Rule]
) -> CodeSegmentReport | None:
    assert all(r.prompter is not None for r in rules), "All llm rules must have prompts"

    rule_prompts = [r.prompter(codeseg, ctx) for r in rules if r.prompter is not None]
    filtered_rules = [r for r, rp in zip(rules, rule_prompts, strict=True) if rp]

    if not filtered_rules:
        return CodeSegmentReport.correct()

    rules_list = [
        f"- {rule.ref}: {prompt}"
        for rule, prompt in zip(filtered_rules, rule_prompts, strict=True)
    ]
    sys_prompt, user_prompt = ruled_check_prompts(
        function_code=codeseg.code_str, rules=rules_list
    )
    response = llm.generate(
        prompt=user_prompt,
        system=sys_prompt,
    )

    json_resp_str = _extract_json_object(response)

    if json_resp_str is None:
        rich.print(
            "  [yellow]⚠ Invalid response from model. Ignoring function[/yellow]"
        )
        return None

    json_resp = json.loads(json_resp_str)

    if json_resp["status"] == DocStatus.CORRECT.value:
        return CodeSegmentReport.correct()

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
        status=DocStatus.INCORRECT,
        issues=json_resp["issues"],
    )


def check(path: str, config: DolceConfig) -> None:
    checkpath = Path(path)
    assert config.rule_set is not None

    llm = None
    if config.url and config.rule_set.contains_llm_rules():
        llm = LLMClient(LLMConfig.from_dolce_config(config))
        if not llm.test_connection():
            rich.print("[red]✗ Connection failed[/red]")
            return

    reports: list[CodeSegmentReport] = []

    ctx = RuleContext(config=config)

    for pair in code_docs_from_path(checkpath, config.exclude):
        loc = f"[blue]{pair.code_path}[/blue]"
        rich.print(f"[  ...  ] [blue]{loc}[/blue]", end="\r")

        quick_issues = config.rule_set.check(pair, ctx)
        if quick_issues:
            rich.print(f"[red][ ERROR ][/red] {loc}")
            report = CodeSegmentReport(
                status=DocStatus.INCORRECT,
                issues=quick_issues,
            )
            for issue in report.issues:
                rich.print(f"[red]  - {issue}[/red]")
            reports.append(report)
            continue

        if llm is not None and pair.doc.strip():
            desc_report = check_description(pair, ctx, llm, config.rule_set.llm_rules())
            if desc_report is None:
                continue

            if desc_report.status != DocStatus.CORRECT:
                reports.append(desc_report)
                rich.print(f"[red][ ERROR ][/red] {loc}")
                for issue in desc_report.issues:
                    rich.print(f"[red]  - {issue}[/red]")
                continue

        reports.append(CodeSegmentReport.correct())
        rich.print(f"[green][  OK   ][/green] {loc}")

    _print_summary(reports)
