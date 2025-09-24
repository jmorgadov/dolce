from __future__ import annotations

from pathlib import Path
from typing import Counter

import rich

from pydolce.config import DolceConfig
from pydolce.core.check import check_segment
from pydolce.core.client import LLMClient
from pydolce.core.errors import CacheError
from pydolce.core.parser import (
    CodeSegmentReport,
    DocStatus,
    code_segments_from_path,
)
from pydolce.core.rules.checkers.common import CheckContext
from pydolce.core.rules.rule import LLMRule

# from pydolce.core.rules.rule import CheckContext


def _print_summary(responses: list[CodeSegmentReport]) -> None:
    statuses_count = Counter(resp.status for resp in responses)
    rich.print("\n[bold]Summary:[/bold]")
    if DocStatus.CORRECT in statuses_count:
        rich.print(f"[green]✓ Correct: {statuses_count[DocStatus.CORRECT]}[/green]")
    if DocStatus.INCORRECT in statuses_count:
        rich.print(f"[red]✗ Incorrect: {statuses_count[DocStatus.INCORRECT]}[/red]")


def _print_report_issues(report: CodeSegmentReport) -> None:
    for issue in report.issues:
        rich.print(f"[red]  - {issue}[/red]")


def check(path: str, config: DolceConfig) -> None:
    checkpath = Path(path)
    assert config.rule_set is not None

    llm = None
    if config.url and any(
        isinstance(rule, LLMRule) is not None for rule in config.rule_set
    ):
        llm = LLMClient.from_dolce_config(config)
        if not llm.test_connection():
            rich.print("[red]✗ Connection failed[/red]")
            return

    reports: list[CodeSegmentReport] = []

    try:
        handler = config.cache_handler
    except CacheError as e:
        rich.print(f"[red][ ERROR ][/red] {e}")
        return

    ctx = CheckContext(config=config)
    for segment in code_segments_from_path(checkpath, config.exclude):
        loc = f"[blue]{segment.code_path}[/blue]"
        rich.print(f"[white]\\[  ...  ][/white] [blue]{loc}[/blue]", end="\r")

        report = handler.get_check(segment) or check_segment(segment, config, llm, ctx)
        handler.set_check(
            segment, report, sync=llm is not None
        )  # Sync every time if LLM is used

        if report.status == DocStatus.INCORRECT:
            rich.print(f"[red][ ERROR ][/red] {loc}")
            _print_report_issues(report)

        elif report.status == DocStatus.UNKNOWN:
            rich.print(f"[yellow][  INV  ][/yellow] {loc}")
            for issues in report.issues:
                rich.print(f"[yellow]  - {issues}[/yellow]")
        else:
            rich.print(f"[green][  OK   ][/green] {loc}")

        reports.append(report)

    handler.sync_cache()

    _print_summary(reports)

    if any(report.status == DocStatus.INCORRECT for report in reports):
        raise SystemExit(1)
