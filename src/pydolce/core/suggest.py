import ast
import json

import docstring_parser

from pydolce.config import DolceConfig
from pydolce.core.client import LLMClient
from pydolce.core.errors import LLMResponseError
from pydolce.core.parser import CodeSegment, CodeSegmentType, ModuleHeaders
from pydolce.core.utils import doc_style_from_str, extract_json_object

SYSTEM_DOC_SUGGESTION_TEMPLATE = """You are an expert Python understander. Your task is to suggest a description of certain elements of a given Python code.

The user may give you a a description of the module where the code is located for you to have a better context.

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


def _extract_items_to_describe(
    segment: CodeSegment,
) -> list[str] | None:
    assert isinstance(
        segment.code_node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
    )

    node = segment.code_node

    if node.name.startswith("_"):
        return None  # Skip private or protected functions

    items = [
        '"code_simple_description": [Header of the docstring. A brief short description of what it is this code for (not saying what does it do).]',
    ]

    if segment.is_property() or segment.seg_type == CodeSegmentType.Class:
        return items

    for param in segment.params or {}:
        items.append(f'"param_{param}": "[description of the parameter {param}]"')

    if segment.is_generator and segment.generator_type:
        items.append('"yields": "[description of the yielded value]"')
    elif segment.returns and segment.returns != "None":
        items.append('"return": "[description of the return value]"')

    # Dummy heuristic but good enough for now
    if "raise" in segment.code_str:
        items.append(
            '"raises": {dictionary with exception that the functions explicitly raises. Keys are the exception names and values are their descriptions. If no exceptions are raised, use an empty dictionary.}'
        )

    return items


def _suggest(
    llm: LLMClient,
    segment: CodeSegment,
    items_to_describe: list[str],
    module_headers: ModuleHeaders | None = None,
) -> str:
    items_to_describe_str = (
        "{\n    "
        + (",\n    ".join(items_to_describe) if items_to_describe else "")
        + "\n}"
    )

    user_prompt = USER_DOC_SUGGESTION_TEMPLATE.format(
        code=segment.code_str,
    )

    if module_headers is not None:
        user_prompt += f"\n\nModule context:\n```python\n{module_headers}\n```\n"

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

        elif key == "raises" and isinstance(descr, dict) and descr:
            _docstring_str += "Raises\n------\n"
            for exc, description in descr.items():
                _docstring_str += f"{exc}\n    {description}\n"

    _docstring_str += '"""'
    return _docstring_str


def suggest_from_segment(
    segment: CodeSegment,
    config: DolceConfig,
    llm: LLMClient,
    module_headers: ModuleHeaders | None = None,
) -> str:
    style = doc_style_from_str(
        config.ensure_style if config.ensure_style is not None else "google"
    )
    if style is None:
        raise ValueError("Invalid docstring style")

    if segment.has_doc or not isinstance(
        segment.code_node,
        (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.ClassDef,
        ),
    ):
        raise ValueError("Suggestion can only be made for segments without docstring")

    items_to_describe = _extract_items_to_describe(segment)
    if not items_to_describe:
        return ""

    suggestion = _suggest(
        llm,
        segment,
        items_to_describe=items_to_describe,
        module_headers=module_headers,
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
            style=style,
        )

        suggestion = suggestion.replace('    """:', '"""')  # Fix docstring indentation

    return suggestion
