import requests


def post_multiplication(a: int, b: int) -> int:
    """
    Add two integers.

    Args:
        a (int): The first integer.
        b (int): The second integer.

    Returns:
        int: The product of the two integers.
    """
    val = a * b
    requests.post("http://example.com/api", data={"value": val})
    return val
