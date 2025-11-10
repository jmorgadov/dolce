from typing import Callable, Generator

from pydolce.core.rules.checkers.signature import (
    duplicate_params,
    missing_param,
    missing_param_description,
    missing_param_type,
    missing_return,
    missing_return_description,
    missing_yield,
    missing_yield_description,
    params_does_not_exist,
    return_on_property,
    unnecessary_return,
    unnecessary_yield,
    wrong_param_type,
    wrong_return_type,
    wrong_yield_type,
)
from pydolce.core.rules.rule import CheckContext


def test_duplicate_params(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_duplicate_params(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.
            param (int): The parameter.

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_duplicate_params)[0]

    for result in duplicate_params(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_missing_param(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_missing_param(param1: int, param2: str) -> None:
        """This is a docstring.

        Args:
            param1 (int): The first parameter.

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_missing_param)[0]

    for result in missing_param(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_missing_param_description(
    func_code_segments: Callable, ctx: CheckContext
) -> None:
    def func_with_missing_param_description(param: int) -> None:
        """This is a docstring.

        Args:
            param (int):

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_missing_param_description)[0]

    for result in missing_param_description(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_missing_param_type(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_missing_param_type(param: int) -> None:
        """This is a docstring.

        Args:
            param: The parameter.

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_missing_param_type)[0]

    for result in missing_param_type(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_wrong_param_type(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_wrong_param_type(param: int) -> None:
        """This is a docstring.

        Args:
            param (str): The parameter.

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_wrong_param_type)[0]

    for result in wrong_param_type(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_params_does_not_exist(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_params_does_not_exist(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.
            non_existent_param (str): This parameter does not exist in the signature.

        Returns:
            None
        """
        return None

    segment = func_code_segments(func_with_params_does_not_exist)[0]

    for result in params_does_not_exist(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_missing_return(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_missing_return(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        return param

    segment = func_code_segments(func_with_missing_return)[0]

    for result in missing_return(segment, ctx):
        assert result is not None
        assert result.is_bad

    # Should ignore generators
    def generator_with_missing_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        yield param

    segment = func_code_segments(generator_with_missing_yield)[0]
    for result in missing_return(segment, ctx):
        assert result is None  # Should be ignored


def test_missing_return_description(
    func_code_segments: Callable, ctx: CheckContext
) -> None:
    def func_with_missing_return_description(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            int:
        """
        return param

    segment = func_code_segments(func_with_missing_return_description)[0]

    for result in missing_return_description(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_wrong_return_type(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_wrong_return_type(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            str: The return value.
        """
        return str(param)

    segment = func_code_segments(func_with_wrong_return_type)[0]

    for result in wrong_return_type(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_unnecessary_return(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_unnecessary_return(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            None:
        """
        return param

    segment = func_code_segments(func_with_unnecessary_return)[0]

    for result in unnecessary_return(segment, ctx):
        assert result is not None
        assert result.is_bad

    # Should ignore generators
    def generator_with_unnecessary_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            int: The yield value.
        """
        yield param

    segment = func_code_segments(generator_with_unnecessary_yield)[0]
    for result in unnecessary_return(segment, ctx):
        assert result is None  # Should be ignored


def test_return_on_property(
    property_code_segments: Callable, ctx: CheckContext
) -> None:
    code = """class Foo:
    @property
    def property_with_return(self) -> int:
        \"\"\"This is a docstring.

        Returns:
            int: The return value.
        \"\"\"
        return 42
"""

    segment = property_code_segments(code)[0]

    for result in return_on_property(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_missing_yield(func_code_segments: Callable, ctx: CheckContext) -> None:
    def generator_with_missing_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        yield param

    segment = func_code_segments(generator_with_missing_yield)[0]

    for result in missing_yield(segment, ctx):
        assert result is not None
        assert result.is_bad

    # Should ignore non-generators
    def func_with_missing_return(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            int: The return value.
        """
        return param

    segment = func_code_segments(func_with_missing_return)[0]
    for result in missing_yield(segment, ctx):
        assert result is None  # Should be ignored


def test_missing_yield_description(
    func_code_segments: Callable, ctx: CheckContext
) -> None:
    def generator_with_missing_yield_description(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            int:
        """
        yield param

    segment = func_code_segments(generator_with_missing_yield_description)[0]

    for result in missing_yield_description(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_wrong_yield_type(func_code_segments: Callable, ctx: CheckContext) -> None:
    def generator_with_wrong_yield_type(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            str: The yield value.
        """
        yield str(param)

    segment = func_code_segments(generator_with_wrong_yield_type)[0]

    for result in wrong_yield_type(segment, ctx):
        assert result is not None
        assert result.is_bad


def test_unnecessary_yield(func_code_segments: Callable, ctx: CheckContext) -> None:
    def func_with_unnecessary_return(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            None: The return value.
        """
        return param

    segment = func_code_segments(func_with_unnecessary_return)[0]
    for result in unnecessary_yield(segment, ctx):
        assert result is not None
        assert result.is_bad
