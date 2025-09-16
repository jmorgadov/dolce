from typing import Annotated

import rich
import typer

import pydolce
from pydolce.config import DolceConfig

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
) -> None:
    _config = DolceConfig.from_pyproject()
    _config.update(ignore_missing=ignore_missing, model=model)
    pydolce.check(
        path=path,
        config=_config,
    )


@app.command()
def rules() -> None:
    for rule in pydolce.rules.rules.ALL_RULES:
        rich.print(f"- [cyan]{rule.ref}[/cyan]: {rule.description}")


@app.callback()
def main_callback() -> None:
    version = pydolce.__version__
    rich.print(f"[magenta]Dolce - {version}[/magenta]\n")


def main() -> None:
    app()
