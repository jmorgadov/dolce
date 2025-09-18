from typing import Callable

from pydolce.rules.checkers._2xx_style import invalid_docstring_style
from pydolce.rules.rules import RuleContext


def test_invalid_docstring_style(code_segment_from: Callable, ctx: RuleContext) -> None:
    def func_with_invalid_docstring_style() -> int:
        """This is a docstring using numpy style.

        Returns
        -------
        int
            The return value.
        """
        return 3

    segment = code_segment_from(func_with_invalid_docstring_style)[0]
    ctx.config.update(ensure_style="google")

    result = invalid_docstring_style(segment, ctx)
    assert result is not None
    assert not result.passed
