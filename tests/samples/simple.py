def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number."""
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
