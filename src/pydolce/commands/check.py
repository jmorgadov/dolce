from __future__ import annotations

import logging
from collections import Counter

import rich

from pydolce.config import DolceConfig
from pydolce.core.check import check_segment
from pydolce.core.client import LLMClient
from pydolce.core.parser import (
    code_segments_from_path,
)
from pydolce.core.rules.checkers.common import CheckContext, CheckResult, CheckStatus
from pydolce.core.rules.rule import LLMRule, Rule

logger = logging.getLogger(__name__)


def _print_summary(report: dict[Rule, list[CheckResult]]) -> None:
    if not report:
        rich.print("\n[bold]No code segments were checked.[/bold]")
        return

    good, bad = 0, 0
    for issues in report.values():
        if any(issue.status == CheckStatus.BAD for issue in issues):
            bad += 1
        else:
            good += 1
    rich.print("\n[bold]Summary:[/bold]")
    rich.print(f"[green]✓ Correct: {good}[/green]")
    rich.print(f"[red]✗ Incorrect: {bad}[/red]")


def _print_report_issues(report: dict[Rule, list[CheckResult]]) -> None:
    for rule, results in report.items():
        for result in results:
            issue = result.issue
            line = f"{rule.reference}: {rule.description}"
            if issue:
                line += f" ({issue})"
            if result.status == CheckStatus.BAD:
                rich.print(f"[red]  - {line}[/red]")
            elif result.status == CheckStatus.UNKNOWN:
                rich.print(f"[yellow]  - {line}[/yellow]")


def check(path: str, config: DolceConfig) -> None:
    llm = None
    if config.url and any(isinstance(rule, LLMRule) for rule in config.rule_set):
        llm = LLMClient.from_dolce_config(config)
        if not llm.test_connection():
            rich.print("[red]✗ LLM connection failed[/red]")
            return

    ctx = CheckContext(config=config)
    bad = 0
    unknown = 0

    handler = None
    try:
        handler = config.cache_handler
    except Exception as e:
        logger.debug("Not using cache handler: %s", e)

    assert handler is not None

    config_rules = config.rule_set
    for segment in code_segments_from_path(path, config.exclude):
        loc = f"[blue]{segment.code_path}[/blue]"
        rich.print(f"[white]\\[  ...  ][/white] [blue]{loc}[/blue]", end="\r")
        seg_rules = config_rules

        report: dict[Rule, list[CheckResult]] = {}
        if handler is not None:
            cached_report = handler.get_report(segment)
            report = {
                rule: results
                for rule, results in cached_report.items()
                if results is not None
            }
            seg_rules = [rule for rule in seg_rules if rule not in cached_report]

        if seg_rules:
            new_report = check_segment(segment, seg_rules, ctx, llm)
            if handler is not None:
                handler.set_report(segment, new_report, sync=True)
            report.update(new_report)

        statuses = Counter(r.status for rep in report.values() for r in rep)

        if statuses.get(CheckStatus.GOOD, 0) == sum(statuses.values()):
            rich.print(f"[green][  OK   ][/green] {loc}")
            continue

        if statuses.get(CheckStatus.BAD, 0):
            rich.print(f"[red][ ERROR ][/red] {loc}")
            bad += 1
        if statuses.get(CheckStatus.UNKNOWN, 0):
            rich.print(f"[yellow][  ???  ][/yellow] {loc}")
            unknown += 1
        _print_report_issues(report)

    if bad or unknown:
        rich.print("\n[bold]Summary:[/bold]")
        if unknown:
            rich.print(f"[yellow]✓ Unkown: {unknown}[/yellow]")
        if bad:
            rich.print(f"[red]✗ Incorrect: {bad}[/red]")
        if not bad and not unknown:
            rich.print("[green]✓ All correct[/green]")
    else:
        rich.print("\n[bold green]✓ All correct[/bold green]")

    if bad:
        raise SystemExit(1)
