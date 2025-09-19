import ast
import inspect
from typing import Callable

import pytest

from pydolce.config import DolceConfig
from pydolce.core.parser import CodeSegment, CodeSegmentVisitor
from pydolce.core.rules.rules import RuleContext


def _unindent_all_possible(code: str) -> str:
    lines = code.splitlines()
    # Find the minimum indentation level (ignoring empty lines)
    min_indent = None
    for line in lines:
        stripped_line = line.lstrip()
        if stripped_line:  # Ignore empty or whitespace-only lines
            indent = len(line) - len(stripped_line)
            if min_indent is None or indent < min_indent:
                min_indent = indent

    if min_indent is None:
        return code  # All lines are empty or whitespace

    # Remove the minimum indentation from all lines
    unindented_lines = [
        line[min_indent:] if len(line) >= min_indent else line for line in lines
    ]
    return "\n".join(unindented_lines)


@pytest.fixture
def ctx() -> RuleContext:
    return RuleContext(config=DolceConfig())


@pytest.fixture
def code_segment_from_func() -> Callable[[Callable], CodeSegment]:
    def _code_segment_from(func: Callable) -> list[CodeSegment]:
        code_str = inspect.getsource(func)
        code_str = _unindent_all_possible(code_str)
        visitor = CodeSegmentVisitor("dummy.py")
        visitor.visit(ast.parse(code_str))
        return visitor.segments

    return _code_segment_from


@pytest.fixture
def code_segment_from_str() -> Callable[[str], list[CodeSegment]]:
    def _code_segment_from(code_str: str) -> list[CodeSegment]:
        code_str = _unindent_all_possible(code_str)
        visitor = CodeSegmentVisitor("dummy.py")
        visitor.visit(ast.parse(code_str))
        return visitor.segments

    return _code_segment_from
