from typing import Callable

from pydolce.core.rules.checkers.style import invalid_docstring_style
from pydolce.core.rules.rule import CheckContext


def test_invalid_docstring_style(
    func_code_segments: Callable, ctx: CheckContext
) -> None:
    def func_with_invalid_docstring_style() -> int:
        """This is a docstring using numpy style.

        Returns
        -------
        int
            The return value.
        """
        return 3

    segment = func_code_segments(func_with_invalid_docstring_style)[0]
    ctx.config.update(ensure_style="google")

    for result in invalid_docstring_style(segment, ctx):
        assert result is not None
        assert result.is_bad
