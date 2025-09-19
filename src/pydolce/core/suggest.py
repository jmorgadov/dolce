import ast
import json

import docstring_parser

from pydolce.config import DolceConfig
from pydolce.core.client import LLMClient
from pydolce.core.errors import LLMResponseError
from pydolce.core.parser import CodeSegment
from pydolce.core.utils import extract_json_object

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
    items_to_describe: list[str],
) -> str:
    items_to_describe_str = (
        "{\n    "
        + (",\n    ".join(items_to_describe) if items_to_describe else "")
        + "\n}"
    )

    user_prompt = USER_DOC_SUGGESTION_TEMPLATE.format(
        code=segment.code_str,
    )

    suggestion = llm.generate(
        prompt=user_prompt,
        system=SYSTEM_DOC_SUGGESTION_TEMPLATE.format(
            items_to_describe=items_to_describe_str
        ),
    ).strip()
    return suggestion


def _build_temporal_docstring(segment: CodeSegment, sugg_json: dict) -> str:
    _docstring_str = '"""'

    if "code_simple_description" in sugg_json:
        if len(sugg_json) == 1:
            _docstring_str += sugg_json["code_simple_description"]
        else:
            _docstring_str += "\n" + sugg_json["code_simple_description"] + "\n\n"

    if any(k.startswith("param_") for k in sugg_json.keys()):
        _docstring_str += "Parameters\n----------\n"

    for key, descr in sugg_json.items():
        if key.startswith("param_"):
            param_name = key[len("param_") :]
            param_type = segment.params.get(param_name) if segment.params else None
            if param_name and descr:
                _docstring_str += f"{param_name} : "
                if param_type:
                    _docstring_str += f"{param_type}\n"
                _docstring_str += f"    {descr}\n"

        elif key in ["return", "yield"]:
            return_type = (
                segment.returns
                if segment.returns and segment.returns != "None"
                else None
            )
            if return_type is None:
                continue

            _section = key.capitalize() + "s"
            _docstring_str += f"{_section}\n" + "-" * len(_section) + "\n"
            _docstring_str += f"{return_type}\n    {descr}\n"

    _docstring_str += '"""'
    return _docstring_str


def suggest_from_segment(
    segment: CodeSegment, config: DolceConfig, llm: LLMClient
) -> str:
    if segment.has_doc or not isinstance(
        segment.code_node,
        (ast.FunctionDef, ast.AsyncFunctionDef),  # Only support functions for now
    ):
        raise ValueError("Suggestion can only be made for segments without docstring")

    items_to_describe = _extract_function_items_to_describe(segment)
    if not items_to_describe:
        return ""

    suggestion = _suggest(
        llm,
        segment,
        items_to_describe=items_to_describe,
    )

    sugg_json_str = extract_json_object(suggestion)
    if not sugg_json_str:
        raise LLMResponseError("No JSON object found in LLM response")

    sugg_json = json.loads(sugg_json_str)

    _docstring_str = _build_temporal_docstring(segment, sugg_json)

    if not _docstring_str.find("\n"):
        suggestion = _docstring_str
    else:
        suggestion = docstring_parser.compose(
            docstring_parser.parse(
                _docstring_str, style=docstring_parser.DocstringStyle.NUMPYDOC
            ),
            style=docstring_parser.DocstringStyle.GOOGLE,
        )

        suggestion = suggestion.replace('    """:', '"""')  # Fix docstring indentation

    return suggestion
