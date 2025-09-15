def fibonacci(n: int) -> int:
    """Return the nth Fibonacci number."""
    return n if n <= 1 else fibonacci(n - 1) + fibonacci(n - 2)


def add(a: int, b: int) -> int:
    """Multiply two integers."""
    return a + b


def subtract(a: int, b: int) -> int:
    return a - b
