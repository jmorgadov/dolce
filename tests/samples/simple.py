from typing import Generator


def foo() -> None:
    print("foo")


def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number.

    Args
    ----
    n : int
        The position in the Fibonacci sequence.

    Returns
    -------
    int
        The nth Fibonacci number
    """
    return n if n <= 1 else fibonacci(n - 1) + fibonacci(n - 2)


def subtract(a: int, b: int) -> int:
    """Subtract two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.
    Returns:
        int: The difference of the two integers.
    """
    return a - b


def bar() -> None:
    """Example bar function

    Yields
    ------
    None
    """
    print("bar")


def baz() -> Generator:
    """Only Yieds 42"""
    yield 42


def abc() -> Generator:
    """Only yieds 35

    Yields:
        str: The number 35
    """
    yield 35
