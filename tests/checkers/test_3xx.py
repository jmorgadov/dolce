from typing import Callable, Generator

from pydolce.rules.checkers._3xx_signature import (
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
from pydolce.rules.rules import RuleContext


def test_duplicate_params(code_segment_from_func: Callable) -> None:
    def func_with_duplicate_params(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.
            param (int): The parameter.

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_duplicate_params)[0]

    result = duplicate_params(segment, None)
    assert result is not None
    assert not result.passed


def test_missing_param(code_segment_from_func: Callable, ctx: RuleContext) -> None:
    def func_with_missing_param(param1: int, param2: str) -> None:
        """This is a docstring.

        Args:
            param1 (int): The first parameter.

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_missing_param)[0]

    result = missing_param(segment, ctx)
    assert result is not None
    assert not result.passed


def test_missing_param_description(code_segment_from_func: Callable) -> None:
    def func_with_missing_param_description(param: int) -> None:
        """This is a docstring.

        Args:
            param (int):

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_missing_param_description)[0]

    result = missing_param_description(segment, None)
    assert result is not None
    assert not result.passed


def test_missing_param_type(code_segment_from_func: Callable) -> None:
    def func_with_missing_param_type(param: int) -> None:
        """This is a docstring.

        Args:
            param: The parameter.

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_missing_param_type)[0]

    result = missing_param_type(segment, None)
    assert result is not None
    assert not result.passed


def test_wrong_param_type(code_segment_from_func: Callable) -> None:
    def func_with_wrong_param_type(param: int) -> None:
        """This is a docstring.

        Args:
            param (str): The parameter.

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_wrong_param_type)[0]

    result = wrong_param_type(segment, None)
    assert result is not None
    assert not result.passed


def test_params_does_not_exist(code_segment_from_func: Callable) -> None:
    def func_with_params_does_not_exist(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.
            non_existent_param (str): This parameter does not exist in the signature.

        Returns:
            None
        """
        return None

    segment = code_segment_from_func(func_with_params_does_not_exist)[0]

    result = params_does_not_exist(segment, None)
    assert result is not None
    assert not result.passed


def test_missing_return(code_segment_from_func: Callable, ctx: RuleContext) -> None:
    def func_with_missing_return(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        return param

    segment = code_segment_from_func(func_with_missing_return)[0]

    result = missing_return(segment, ctx)
    assert result is not None
    assert not result.passed

    # Should ignore generators
    def generator_with_missing_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        yield param

    segment = code_segment_from_func(generator_with_missing_yield)[0]
    result = missing_return(segment, ctx)
    assert result is None  # Should be ignored


def test_missing_return_description(code_segment_from_func: Callable) -> None:
    def func_with_missing_return_description(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            int:
        """
        return param

    segment = code_segment_from_func(func_with_missing_return_description)[0]

    result = missing_return_description(segment, None)
    assert result is not None
    assert not result.passed


def test_wrong_return_type(code_segment_from_func: Callable) -> None:
    def func_with_wrong_return_type(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            str: The return value.
        """
        return str(param)

    segment = code_segment_from_func(func_with_wrong_return_type)[0]

    result = wrong_return_type(segment, None)
    assert result is not None
    assert not result.passed


def test_unnecessary_return(code_segment_from_func: Callable, ctx: RuleContext) -> None:
    def func_with_unnecessary_return(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            None:
        """
        return param

    segment = code_segment_from_func(func_with_unnecessary_return)[0]

    result = unnecessary_return(segment, ctx)
    assert result is not None
    assert not result.passed

    # Should ignore generators
    def generator_with_unnecessary_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            int: The yield value.
        """
        yield param

    segment = code_segment_from_func(generator_with_unnecessary_yield)[0]
    result = unnecessary_return(segment, ctx)
    assert result is None  # Should be ignored


def test_return_on_property(code_segment_from_str: Callable, ctx: RuleContext) -> None:
    code = """class Foo:
    @property
    def property_with_return(self) -> int:
        \"\"\"This is a docstring.

        Returns:
            int: The return value.
        \"\"\"
        return 42
"""

    segment = next(seg for seg in code_segment_from_str(code) if seg.lineno == 3)

    result = return_on_property(segment, ctx)
    assert result is not None
    assert not result.passed


def test_missing_yield(code_segment_from_func: Callable, ctx: RuleContext) -> None:
    def generator_with_missing_yield(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.
        """
        yield param

    segment = code_segment_from_func(generator_with_missing_yield)[0]

    result = missing_yield(segment, ctx)
    assert result is not None
    assert not result.passed

    # Should ignore non-generators
    def func_with_missing_return(param: int) -> int:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Returns:
            int: The return value.
        """
        return param

    segment = code_segment_from_func(func_with_missing_return)[0]
    result = missing_yield(segment, ctx)
    assert result is None  # Should be ignored


def test_missing_yield_description(code_segment_from_func: Callable) -> None:
    def generator_with_missing_yield_description(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            int:
        """
        yield param

    segment = code_segment_from_func(generator_with_missing_yield_description)[0]

    result = missing_yield_description(segment, None)
    assert result is not None
    assert not result.passed


def test_wrong_yield_type(code_segment_from_func: Callable) -> None:
    def generator_with_wrong_yield_type(param: int) -> Generator[int]:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            str: The yield value.
        """
        yield str(param)

    segment = code_segment_from_func(generator_with_wrong_yield_type)[0]

    result = wrong_yield_type(segment, None)
    assert result is not None
    assert not result.passed


def test_unnecessary_yield(code_segment_from_func: Callable, ctx: RuleContext) -> None:
    def func_with_unnecessary_return(param: int) -> None:
        """This is a docstring.

        Args:
            param (int): The parameter.

        Yields:
            None: The return value.
        """
        return param

    segment = code_segment_from_func(func_with_unnecessary_return)[0]
    result = unnecessary_yield(segment, ctx)
    assert result is not None
    assert not result.passed
