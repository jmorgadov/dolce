import difflib
from pathlib import Path

import docstring_parser
import rich

from pydolce.config import DolceConfig
from pydolce.core.parser import code_segments_from_path
from pydolce.core.utils import doc_style_from_str


def _process_restyled_file(
    filepath: Path, old_lines: list[str], new_lines: list[str]
) -> None:
    old_vs_new = list(
        difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=str(filepath) + " (before)",
            tofile=str(filepath) + " (after)",
            lineterm="",
        )
    )
    if old_vs_new:
        rich.print("[bold]Changes[/bold]")
        diff_syntax = rich.syntax.Syntax(
            "".join(old_vs_new),
            "diff",
            theme="ansi_dark",
            background_color="#181818",
        )
        rich.print(diff_syntax)
        # TODO: add confirmation prompt
        filepath.write_text("".join(new_lines), encoding="utf-8")
        rich.print(f"[green]✔ Updated {filepath}[/green]")
    else:
        rich.print(f"[green]✔ No changes needed in {filepath}[/green]")


def restyle(path: Path | str, config: DolceConfig) -> None:
    if config.ensure_style is None:
        raise ValueError("Docstring style must be specified in config for restyling")

    curr_file_old_lines = None
    curr_file_lines = None
    curr_file = None
    for segment in code_segments_from_path(path, config.exclude):
        if not segment.has_doc or segment.parsed_doc is None:
            continue

        curr_style = segment.parsed_doc.style
        if (
            curr_style is not None
            and curr_style.name.lower() == config.ensure_style.lower()
        ):
            continue

        if curr_file != segment.file_path:
            if (
                curr_file is not None
                and curr_file_old_lines is not None
                and curr_file_lines is not None
            ):
                _process_restyled_file(
                    curr_file,
                    old_lines=curr_file_old_lines,
                    new_lines=curr_file_lines,
                )
            curr_file = segment.file_path
            curr_file_lines = curr_file.read_text(encoding="utf-8").splitlines(
                keepends=True
            )
            curr_file_old_lines = curr_file_lines.copy()

        assert curr_file_lines is not None

        new_style = doc_style_from_str(config.ensure_style)
        if new_style is None:
            raise ValueError(f"Invalid docstring style: {config.ensure_style}")
        new_docstring = docstring_parser.compose(segment.parsed_doc, style=new_style)

        if "\n" not in new_docstring:
            new_docstring = f'"""{new_docstring}"""'
        else:
            new_docstring = f'"""\n{new_docstring}\n"""\n'

        new_doc_lines = new_docstring.splitlines(keepends=True)
        new_doc_lines = [
            " " * (segment.col_offset + 4) + line for line in new_doc_lines
        ]

        # remove old lines
        assert segment.doc_lineno is not None and segment.doc_end_lineno is not None

        for i in range(segment.doc_end_lineno - 1, segment.doc_lineno - 2, -1):
            curr_file_lines.pop(i)

        # insert new lines
        for i, line in enumerate(new_doc_lines):
            curr_file_lines.insert(segment.doc_lineno + i - 1, line)

    if (
        curr_file is not None
        and curr_file_old_lines is not None
        and curr_file_lines is not None
    ):
        _process_restyled_file(
            curr_file,
            old_lines=curr_file_old_lines,
            new_lines=curr_file_lines,
        )
