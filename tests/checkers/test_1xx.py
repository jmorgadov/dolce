from typing import Callable

from pydolce.rules.checkers._1xx_structural import (
    missing_class_docstring,
    missing_func_docstring,
)


def test_missing_func_docstring(code_segment_from: Callable) -> None:
    def func_with_invalid_docstring() -> int:
        return 3

    segment = code_segment_from(func_with_invalid_docstring)

    result = missing_func_docstring(segment, None)
    assert result is not None
    assert not result.passed


def test_missing_class_docstring(code_segment_from: Callable) -> None:
    return  # TODO implement class checking

    class ClassWithInvalidDocstring:
        def method(self) -> int:
            return 3

    segment = code_segment_from(ClassWithInvalidDocstring)

    result = missing_class_docstring(segment, None)
    assert result is not None
    assert not result.passed
