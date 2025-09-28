from typing import Annotated

import rich
import typer

import pydolce
from pydolce.config import DolceConfig
from pydolce.core.rules.rule import RuleGroup
from pydolce.core.rules.rulesets import ALL_RULES

app = typer.Typer()


@app.command(help="Check docstrings in the specified Python file or directory")
def check(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to the Python file or directory to check",
        ),
    ] = ".",
    ignore_missing: Annotated[
        bool | None, typer.Option(help="Ignore functions without docstrings")
    ] = None,
    model: Annotated[
        str | None,
        typer.Option("--model", help="Model name to use"),
    ] = None,
    no_llm: Annotated[
        bool | None,
        typer.Option(
            "--no-llm",
            help="Disable LLM-based checks, even if configured",
            is_flag=True,
            show_default=True,
        ),
    ] = None,
) -> None:
    _config = DolceConfig.from_pyproject()
    _config.update(ignore_missing=ignore_missing, model=model)
    if no_llm:
        _config.update(url="")
    pydolce.check(
        path=path,
        config=_config,
    )


@app.command(
    help="Suggest docstrings for functions/methods without docstrings",
)
def suggest(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to the Python file or directory to check",
        ),
    ] = ".",
    style: Annotated[
        str | None,
        typer.Option(
            "--style",
            help="Docstring style to use for suggestions (overrides config)",
        ),
    ] = None,
) -> None:
    _config = DolceConfig.from_pyproject()
    _config.update(ensure_style=style)

    if not _config.url:
        rich.print(
            "[red]✗ LLM not configured. Please set it up in pyproject.toml like:\n[/red]"
        )
        rich.print(
            """\\[tool.dolce]
url = "http://localhost:11434"
model = "qwen3:8b"
provider = "ollama"
"""
        )
        return
    pydolce.suggest(path, _config)


@app.command(
    name="format",
    help="Rewrite docstrings to conform to the specified style",
)
def format_docs(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to the Python file or directory to check",
        ),
    ] = ".",
    style: Annotated[
        str | None,
        typer.Argument(
            help=(
                "Docstring style to use for restyling (overrides config). "
                "Must be one of: google, numpy, sphinx, rest, epy. "
                "If not specified, the style from the config will be used."
            )
        ),
    ] = None,
) -> None:
    _config = DolceConfig.from_pyproject()
    if style is None:
        if _config.ensure_style is None:
            rich.print(
                "[red]✗ Docstring style must be specified via --style "
                "or in the config file by setting ensure_style.[/red]"
            )
            return
        style = _config.ensure_style
    _config.update(ensure_style=style)
    pydolce.format_docs(path, _config)


@app.command(
    help="List all available rules with their references and descriptions",
)
def rules() -> None:
    last_group = 0
    for rule in sorted(ALL_RULES, key=lambda r: r.reference):
        if rule.group != last_group:
            rich.print(
                f"[bold magenta]\n{RuleGroup(rule.group).name.lower().capitalize()} rules:[/bold magenta]"
            )
            last_group = rule.group
        rich.print(
            f"[cyan][{rule.reference}][/cyan] [white]{rule.name + ' ':.<35}[/white] {rule.description}"
        )


@app.callback()
def main_callback() -> None:
    version = pydolce.__version__
    rich.print(f"[magenta]Dolce - {version}[/magenta]\n")


def main() -> None:
    app()
