from typing import Annotated

import rich
import typer

import pydolce
from pydolce.config import DolceConfig
from pydolce.rules.rules import Rule

app = typer.Typer()


@app.command()
def gen() -> None:
    rich.print("[blue]Coming soon...[/blue]")


@app.command()
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
        typer.Option(
            "--model",
            help="Model name to use (default: codestral for Ollama)",
        ),
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


@app.command()
def rules() -> None:
    last_group = 0
    for rule in Rule.all_rules.values():
        if rule.group != last_group:
            rich.print(f"[bold magenta]\n{rule.group_name} rules:[/bold magenta]")
            last_group = rule.group
        rich.print(
            f"[cyan][{rule.ref}][/cyan] [white]{rule.name + ' ':.<30}[/white] {rule.description}"
        )


@app.callback()
def main_callback() -> None:
    version = pydolce.__version__
    rich.print(f"[magenta]Dolce - {version}[/magenta]\n")


def main() -> None:
    app()
