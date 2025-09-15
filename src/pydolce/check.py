import json
from enum import Enum
from pathlib import Path
from typing import Counter

import rich

from pydolce.client import LLMClient, LLMConfig
from pydolce.config import DolceConfig
from pydolce.parser import code_docs_from_path


class DocStatus(Enum):
    CORRECT = "CORRECT"
    INCORRECT = "INCORRECT"
    MISSING = "MISSING"


def simple_check_prompts(
    function_code: str,
    existing_docstring: str,
) -> tuple[str, str]:
    """
    Create system and user prompts for the model to check docstring inconsistency.

    This will NOT check parameters, returns values, or any other section but the
    main description of the docstring.

    This will NOT check for completeness, only for CRITICAL inconsistencies.

    Args:
        function_code: The Python function code to analyze
        existing_docstring: Current docstring (if any)

    Returns:
        Tuple of (system_prompt, user_prompt)
    """

    system_prompt = """You are an expert Python code analyzer specializing in docstring validation. Your task is to analyze if a Python function docstring has critical inconsistencies with the actual code implementation.

ANALYSIS FOCUS:
- Check if the docstring match what the code actually does.
- Completeness is NOT a goal. ONLY check for CRITICAL INCONSISTENCIES.

ONLY analyze the function description. DO NOT analyze the parameters or return value.
If there is something in the code that is NOT mentioned in the docstring, it is NOT an issue.
JUST focus on what is documented, and if it matches the code.

EXACT OUTPUT FORMAT IN JSON:

```
{
"status": "[CORRECT/INCORRECT]",
"issues": [List of specific issues foundm, enumerated, one sentence max per issue. Empty list if no issues.]
}
```

VERY IMPORTANT: DO NOT ADD ANY EXTRA COMENTARY OR DESCRIPTION. STICK TO THE EXACT OUTPUT FORMAT.
"""

    user_prompt = f"""
```python
{function_code.strip()}
```

Current docstring:
```
{existing_docstring.strip()}
```
"""
    return system_prompt, user_prompt


def _extract_json_object(text: str) -> str | None:
    start = text.find("{")
    if start == -1:
        return None

    brace_count = 0
    in_string = False
    escape_next = False

    for i, char in enumerate(text[start:], start):
        if escape_next:
            escape_next = False
            continue

        if char == "\\":
            escape_next = True
            continue

        if char == '"' and not escape_next:
            in_string = not in_string
            continue

        if not in_string:
            if char == "{":
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0:
                    return text[start : i + 1]

    return None


def _print_summary(responses: list[dict]) -> None:
    statuses_count = Counter(resp["status"] for resp in responses)
    rich.print("\n[bold]Summary:[/bold]")
    if "CORRECT" in statuses_count:
        rich.print(f"[green]✓ Correct: {statuses_count['CORRECT']}[/green]")
    if "MISSING" in statuses_count:
        rich.print(f"[yellow]⚠ Missing: {statuses_count['MISSING']}[/yellow]")
    if "INCORRECT" in statuses_count:
        rich.print(f"[red]✗ Incorrect: {statuses_count['INCORRECT']}[/red]")


def check(path: str, config: DolceConfig) -> None:
    checkpath = Path(path)

    llm = LLMClient(LLMConfig.from_dolce_config(config))
    if not llm.test_connection():
        rich.print("[red]✗ Connection failed[/red]")
        return

    responses = []

    for pair in code_docs_from_path(checkpath):
        if config.ignore_missing and (not pair.doc or pair.doc.strip() == ""):
            continue

        rich.print(f"[blue]{pair.code_path}[/blue]", end=" ")

        if not pair.doc or pair.doc.strip() == "":
            rich.print("[yellow]Missing docstring.[/yellow]")
            responses.append(
                {
                    "status": DocStatus.MISSING.value,
                    "issues": [],
                }
            )
            continue

        sys_prompt, user_prompt = simple_check_prompts(
            function_code=pair.code,
            existing_docstring=pair.doc,
        )
        response = llm.generate(
            prompt=user_prompt,
            system=sys_prompt,
        )

        json_resp_str = _extract_json_object(response)

        if json_resp_str is None:
            rich.print(
                "[yellow]⚠ Invalid response from model. Ignoring function[/yellow]"
            )
            continue

        json_resp = json.loads(json_resp_str)

        if json_resp["status"] == DocStatus.CORRECT.value:
            rich.print("[green]✓ Correct[/green]")
        else:
            rich.print("[red]✗ Incorrect[/red]")
            for issue in json_resp["issues"]:
                rich.print(f"  - {issue}")

        responses.append(json_resp)

    _print_summary(responses)
