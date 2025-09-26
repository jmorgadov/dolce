from __future__ import annotations

from collections import Counter
from pathlib import Path

import rich

from pydolce.config import DolceConfig
from pydolce.core.check import check_segment
from pydolce.core.client import LLMClient
from pydolce.core.errors import CacheError
from pydolce.core.parser import (
    code_segments_from_path,
)
from pydolce.core.rules.checkers.common import CheckContext, CheckResult, CheckStatus
from pydolce.core.rules.rule import LLMRule, Rule


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
    assert config.rule_set is not None

    llm = None
    if config.url and any(
        isinstance(rule, LLMRule) is not None for rule in config.rule_set
    ):
        llm = LLMClient.from_dolce_config(config)
        if not llm.test_connection():
            rich.print("[red]✗ Connection failed[/red]")
            return

    ctx = CheckContext(config=config)
    total = 0
    bad = 0
    unknown = 0
    for segment in code_segments_from_path(path, config.exclude):
        total += 1
        loc = f"[blue]{segment.code_path}[/blue]"
        rich.print(f"[white]\\[  ...  ][/white] [blue]{loc}[/blue]", end="\r")

        report = check_segment(segment, config, llm, ctx)

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

    if total:
        rich.print("\n[bold]Summary:[/bold]")
        if unknown:
            rich.print(f"[yellow]✓ Unkown: {unknown}[/yellow]")
        if bad:
            rich.print(f"[red]✗ Incorrect: {bad}[/red]")
        if not bad and not unknown:
            rich.print("[green]✓ All correct[/green]")

    if bad:
        raise SystemExit(1)
