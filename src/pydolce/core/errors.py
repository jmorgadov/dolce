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


class CacheError(Exception):
    """Exception raised for errors in the caching mechanism."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class ProjectRootNotFoundError(CacheError):
    """Exception raised when the project root cannot be found."""

    def __init__(self) -> None:
        self.message = "Could not determine project root. Please ensure you are running within a valid Python project."
        super().__init__(self.message)
