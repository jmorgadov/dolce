from typing import Callable

from pydolce.core.rules.checkers.structural import (
    missing_class_docstring,
    missing_func_docstring,
)
from pydolce.core.rules.rule import CheckContext


def test_missing_func_docstring(
    func_code_segments: Callable, ctx: CheckContext
) -> None:
    def func_with_invalid_docstring() -> int:
        return 3

    segment = func_code_segments(func_with_invalid_docstring)[0]

    result = missing_func_docstring(segment, ctx)
    assert result is not None
    assert not result.passed


def test_missing_class_docstring(
    class_code_segments: Callable, ctx: CheckContext
) -> None:
    code_str = """
class ClassWithNoDocstring:
    def method(self) -> int:
        return 3
"""

    segment = class_code_segments(code_str)[0]

    result = missing_class_docstring(segment, ctx)
    assert result is not None
    assert not result.passed
