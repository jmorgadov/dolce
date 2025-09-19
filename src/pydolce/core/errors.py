class LLmError(Exception):
    """Base class for exceptions in this module."""

    pass


class LLMConnectionError(LLmError):
    """Exception raised for errors in the connection to the LLM service."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class LLMResponseError(LLmError):
    """Exception raised for errors in the response from the LLM service."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(f"Message: {self.message}")
