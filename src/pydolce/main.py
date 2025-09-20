from typing import Annotated

import rich
import typer

import pydolce
from pydolce.config import DolceConfig
from pydolce.core.rules.rules import Rule

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
    help="Rewrite docstrings to conform to the specified style",
)
def restyle(
    path: Annotated[
        str,
        typer.Argument(
            help="Path to the Python file or directory to check",
        ),
    ] = ".",
    style: Annotated[
        str,
        typer.Argument(
            help="Docstring style to use for restyling (overrides config)",
        ),
    ] = "google",
) -> None:
    _config = DolceConfig.from_pyproject()
    _config.update(ensure_style=style)
    pydolce.restyle(path, _config)


@app.command(
    help="List all available rules with their references and descriptions",
)
def rules() -> None:
    last_group = 0
    for rule in Rule.all_rules.values():
        if rule.group != last_group:
            rich.print(f"[bold magenta]\n{rule.group_name} rules:[/bold magenta]")
            last_group = rule.group
        rich.print(
            f"[cyan][{rule.ref}][/cyan] [white]{rule.name + ' ':.<35}[/white] {rule.description}"
        )


@app.command(
    help="Show migration mapping from pydoclint, pydocstyle, and docsig to Dolce rule references",
)
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
