import ast
import difflib
import json
from pathlib import Path

import docstring_parser
import rich
import rich.syntax

from pydolce.client import LLMClient
from pydolce.config import DolceConfig
from pydolce.parser import CodeSegment, code_docs_from_path
from pydolce.utils import extract_json_object

SYSTEM_SUMMARY_TEMPLATE = """You are an expert Python code understander. Your task is to provide a concise summary of a given Python code based on its code.

EXACT OUTPUT FORMAT IN TEXT:
```
[summary]
```

You MUST ONLY provide the summary, without any additional text or formatting, nor your thinking process.

NEVER provide any other information but the summary.
"""

SYSTEM_DOC_SUGGESTION_TEMPLATE = """You are an expert Python understander. Your task is to suggest a description of certain elements of a given Python code.

Ensure the descriptions are CLEAR, CONCISE, INFORMATIVE, SIMPLE.

Do not add any extra sections that are not needed, but ensure all relevant sections are present.

EXACT OUTPUT FORMAT IN JSON:
```
{items_to_describe}
```

NEVER provide any other information but the JSON.
"""

USER_DOC_SUGGESTION_TEMPLATE = """```python
{code}
```
"""


def _extract_function_items_to_describe(
    segment: CodeSegment,
) -> list[str] | None:
    assert isinstance(segment.code_node, (ast.FunctionDef, ast.AsyncFunctionDef))

    node = segment.code_node

    if node.name.startswith("_"):
        return None  # Skip private or protected functions

    if segment.is_property():
        # It's a property, only describe the return value if any
        return None

    items = [
        '"code_simple_description": [Header of the docstring. A brief short description of what the code does.]'
    ]
    for param in segment.params or {}:
        items.append(f'"param_{param}": "[description of the parameter {param}]"')

    if segment.is_generator and segment.generator_type:
        items.append('"yields": "[description of the yielded value]"')
    elif segment.returns and segment.returns != "None":
        items.append('"return": "[description of the return value]"')

    # TODO: Handle raises

    return items


def _suggest(
    llm: LLMClient,
    segment: CodeSegment,
    file_content: str,
    items_to_describe: list[str],
) -> str:
    syntax = rich.syntax.Syntax(
        segment.code_str,
        "python",
        theme="ansi_dark",
        background_color="#181818",
    )
    rich.print("[bold]Suggesting docstring for:[/bold]")
    rich.print(syntax)

    context = file_content.splitlines(keepends=True)
    context_str = "".join(
        context[max(0, segment.lineno - 15) : min(segment.endlineno + 14, len(context))]
    )

    items_to_describe_str = (
        "{\n    "
        + (",\n    ".join(items_to_describe) if items_to_describe else "")
        + "\n}"
    )

    user_prompt = (
        USER_DOC_SUGGESTION_TEMPLATE.format(
            code=segment.code_str,
        )
        + f"\nCONTEXT:\n```python\n{context_str}\n```"
    )

    suggestion = llm.generate(
        prompt=user_prompt,
        system=SYSTEM_DOC_SUGGESTION_TEMPLATE.format(
            items_to_describe=items_to_describe_str
        ),
    ).strip()
    return suggestion


def _extract_suggestion_from_response(response: str) -> str:
    start = response.find('"""')
    if start == -1:
        return response.strip()

    end = response.find('"""', start + 3)
    if end == -1:
        return response[start + 3 :].strip()

    # Check if there's a language specifier after the first ```
    first_line_end = response.find("\n", start + 3)
    if first_line_end != -1 and first_line_end < end:
        return response[first_line_end + 1 : end].strip()

    return response[start + 3 : end].strip()


def _temporal_docstring(segment: CodeSegment, sugg_json: dict) -> str:
    _docstring_str = '"""'

    if "code_simple_description" in sugg_json:
        if len(sugg_json) == 1:
            _docstring_str += sugg_json["code_simple_description"]
        else:
            _docstring_str += "\n" + sugg_json["code_simple_description"] + "\n\n"

    if any(k.startswith("param_") for k in sugg_json.keys()):
        _docstring_str += "Parameters\n"
        _docstring_str += "----------\n"

    for key, descr in sugg_json.items():
        if key.startswith("param_"):
            param_name = key[len("param_") :]
            param_type = segment.params.get(param_name) if segment.params else None
            if param_name and descr:
                if param_type:
                    _docstring_str += f"{param_name} : {param_type}\n    {descr}\n"
                else:
                    _docstring_str += f"{param_name} : \n    {descr}\n"

        elif key in ["return", "yield"]:
            return_type = (
                segment.returns
                if segment.returns and segment.returns != "None"
                else None
            )
            if return_type is None:
                continue
            if key == "return":
                _docstring_str += "Returns\n"
                _docstring_str += "-------\n"
            else:
                _docstring_str += "Yields\n"
                _docstring_str += "------\n"

            _docstring_str += f"{return_type}\n    {descr}\n"

    _docstring_str += '"""'

    return _docstring_str


def suggest(path: Path | str, config: DolceConfig) -> None:
    llm = None

    if config.url:
        llm = LLMClient.from_dolce_config(config)
        if not llm.test_connection():
            rich.print("[red]✗ Connection failed[/red]")
            return

    assert llm is not None

    accepted_docstrings: dict[Path, list[tuple[int, int, str]]] = {}

    last_path = None
    file_content = ""
    regected = 0
    for segment in code_docs_from_path(path, config.exclude):
        if segment.has_doc or not isinstance(
            segment.code_node,
            (ast.FunctionDef, ast.AsyncFunctionDef),  # Only support functions for now
        ):
            continue

        if segment.code_path != last_path:
            last_path = Path(segment.file_path)
            file_content = last_path.read_text()

        items_to_describe = _extract_function_items_to_describe(segment)
        if not items_to_describe:
            continue

        suggestion = _suggest(
            llm,
            segment,
            file_content,
            items_to_describe=items_to_describe,
        )

        if suggestion is None:
            rich.print("[red]✗ No suggestion received[/red]")
            continue

        sugg_json_str = extract_json_object(suggestion)
        if not sugg_json_str:
            rich.print("[red]✗ No JSON object found in the response[/red]")
            continue

        sugg_json = json.loads(sugg_json_str)

        _docstring_str = _temporal_docstring(segment, sugg_json)

        if not _docstring_str.find("\n"):
            suggestion = _docstring_str
        else:
            suggestion = docstring_parser.compose(
                docstring_parser.parse(
                    _docstring_str, style=docstring_parser.DocstringStyle.NUMPYDOC
                ),
                style=docstring_parser.DocstringStyle.GOOGLE,
            )

            suggestion = suggestion.replace(
                '    """:', '"""'
            )  # Fix docstring indentation

        rich.print("[bold]\nSuggested docstring:[/bold]")
        syntax = rich.syntax.Syntax(
            suggestion, "python", theme="ansi_dark", background_color="#181818"
        )
        rich.print(syntax)

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

    # Now, apply the accepted docstrings to the files

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
