import ast
import difflib
from pathlib import Path

import rich
import rich.syntax

from pydolce.config import DolceConfig
from pydolce.core.client import LLMClient, LLMError
from pydolce.core.parser import CodeSegment, ModuleHeaders, code_segments_from_path
from pydolce.core.suggest import suggest_from_segment


def _process_segment(
    segment: CodeSegment,
    config: DolceConfig,
    llm: LLMClient,
    module_headers: ModuleHeaders | None = None,
) -> str | None:
    syntax = rich.syntax.Syntax(
        segment.code_str,
        "python",
        theme="ansi_dark",
        background_color="#181818",
    )
    rich.print("[bold]Suggesting docstring for:[/bold]")
    rich.print(syntax)

    try:
        suggestion = suggest_from_segment(segment, config, llm, module_headers)
    except LLMError as e:
        rich.print(f"[red]✗ Could not get suggestion: {e}[/red]")
        return None

    rich.print("[bold]\nSuggested docstring:[/bold]")
    syntax = rich.syntax.Syntax(
        suggestion, "python", theme="ansi_dark", background_color="#181818"
    )
    rich.print(syntax)
    return suggestion


def _process_accepted_suggestion(
    accepted_docstrings: dict[Path, list[tuple[int, int, str]]],
) -> None:
    for filepath, mods in accepted_docstrings.items():
        old_file_content = filepath.read_text()
        file_lines = old_file_content.splitlines(keepends=True)

        backward_mods = sorted(mods, key=lambda x: x[0], reverse=True)

        for lineno, col, docstring in backward_mods:
            indent = "    " * ((col // 4) + 1)  # Assuming 4 spaces per indent level
            docstring_lines = [indent + line + "\n" for line in docstring.splitlines()]

            file_lines.insert(lineno, "".join(docstring_lines))

        new_content = "".join(file_lines)

        old_vs_new = difflib.unified_diff(
            old_file_content.splitlines(keepends=True),
            new_content.splitlines(keepends=True),
            fromfile=str(filepath),
            tofile=str(filepath) + " (modified)",
            lineterm="",
        )
        old_vs_new_str = "".join(old_vs_new)

        sintax = rich.syntax.Syntax(
            old_vs_new_str, "diff", theme="ansi_dark", background_color="#181818"
        )
        rich.print("[bold]Changes[/bold]")
        rich.print(sintax)

        rich.print(
            f"[blue]Do you want to save the changes to {filepath}? [Y/n]:[/blue]",
            end=" ",
        )

        user_input = input().strip().lower()
        if user_input not in ["", "y", "yes"]:
            rich.print("[yellow]✗ Changes not saved by user[/yellow]")
            continue

        filepath.write_text(new_content)


def suggest(path: Path | str, config: DolceConfig) -> None:
    llm = None

    if config.url:
        llm = LLMClient.from_dolce_config(config)
        if not llm.test_connection():
            rich.print("[red]✗ Connection failed[/red]")
            return

    assert llm is not None

    accepted_docstrings: dict[Path, list[tuple[int, int, str]]] = {}

    curr_path = None
    module_headers = None
    regected = 0
    for segment in code_segments_from_path(path, config.exclude):
        if curr_path != segment.file_path:
            curr_path = segment.file_path
            module_headers = ModuleHeaders(curr_path)

        if segment.has_doc or not isinstance(
            segment.code_node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            continue

        if segment.code_node.name.startswith("_"):
            continue

        suggestion = _process_segment(segment, config, llm, module_headers)
        if suggestion is None:
            continue

        rich.print(
            "[blue]\nDo you accept this suggestion? [Y/n]:[/blue]",
            end=" ",
        )

        user_input = input().strip().lower()
        if user_input not in ["", "y", "yes"]:
            rich.print("[yellow]\n✗ Suggestion rejected by user[/yellow]")
            regected += 1
            continue

        if segment.file_path not in accepted_docstrings:
            accepted_docstrings[segment.file_path] = []

        dline = segment.lineno
        dcol = segment.col_offset
        accepted_docstrings[segment.file_path].append((dline, dcol, suggestion))

    if not accepted_docstrings:
        if regected > 0:
            rich.print("[yellow]No docstrings accepted.[/yellow]")
        else:
            rich.print("[green]No docstrings to suggest.[/green]")
        return

    _process_accepted_suggestion(accepted_docstrings)
