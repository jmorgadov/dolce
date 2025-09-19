from typing import Callable

from pydolce.core.rules.checkers._1xx_structural import (
    missing_class_docstring,
    missing_func_docstring,
)
from pydolce.core.rules.rules import RuleContext


def test_missing_func_docstring(
    code_segment_from_func: Callable, ctx: RuleContext
) -> None:
    def func_with_invalid_docstring() -> int:
        return 3

    segment = code_segment_from_func(func_with_invalid_docstring)[0]

    result = missing_func_docstring(segment, ctx)
    assert result is not None
    assert not result.passed


def test_missing_class_docstring(code_segment_from_func: Callable) -> None:
    return  # TODO implement class checking

    class ClassWithInvalidDocstring:
        def method(self) -> int:
            return 3

    segment = code_segment_from_func(ClassWithInvalidDocstring)

    result = missing_class_docstring(segment, None)
    assert result is not None
    assert not result.passed
