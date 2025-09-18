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
            f"[cyan][{rule.ref}][/cyan] [white]{rule.name + ' ':.<35}[/white] {rule.description}"
        )


@app.command()
def migrations() -> None:
    if not Rule.pydoclint_mig:
        rich.print("[yellow]No pydoclint migration data available.[/yellow]")
    else:
        rich.print("[bold magenta]Pydoclint to Dolce migration:[/bold magenta]")
        for pydoclint_ref, dolce_ref in Rule.pydoclint_mig.items():
            rich.print(f"[cyan]{pydoclint_ref}[/cyan] -> [green]{dolce_ref}[/green]")

    if not Rule.pydocstyle_mig:
        rich.print("\n[yellow]No pydocstyle migration data available.[/yellow]")
    else:
        rich.print("\n[bold magenta]Pydocstyle to Dolce migration:[/bold magenta]")
        for pydocstyle_ref, dolce_ref in Rule.pydocstyle_mig.items():
            rich.print(f"[cyan]{dolce_ref}[/cyan] -> [green]{pydocstyle_ref}[/green]")

    if not Rule.docsig_mig:
        rich.print("\n[yellow]No docsig migration data available.[/yellow]")
    else:
        rich.print("\n[bold magenta]Docsig to Dolce migration:[/bold magenta]")
        for docsig_ref, dolce_ref in Rule.docsig_mig.items():
            rich.print(f"[cyan]{docsig_ref}[/cyan] -> [green]{dolce_ref}[/green]")


@app.callback()
def main_callback() -> None:
    version = pydolce.__version__
    rich.print(f"[magenta]Dolce - {version}[/magenta]\n")


def main() -> None:
    app()
