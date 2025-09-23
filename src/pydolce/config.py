from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cache, cached_property
from pathlib import Path
from typing import Any

import toml

from pydolce.core.cache import CacheHandler
from pydolce.core.parser import CodeSegmentType
from pydolce.types import RuleSet

DEFAULT_EXCLUDES = [
    "__init__.py",
    "setup.py",
    "conftest.py",
    "tests/*",
    "test_*.py",
    "*_test.py",
    "*/tests/*",
    ".venv",
    ".git",
    "dist",
]

DEFAULT_SCOPES = [
    "function",
    "class",
    "method",
]


@dataclass
class DolceConfig:
    """Configuration for Dolce"""

    # Rule selection options
    target: list[str] | None = None  # Specific rules to target
    disable: list[str] | None = None  # Specific rules to disable
    exclude: list[str] | None = None

    # Code segment options
    ignore_args: bool = True
    ignore_kwargs: bool = True
    ignore_private_functions: bool = True
    scopes: list[str] | None = None

    # Docstring style options
    ensure_style: str | None = None  # e.g., "google", "numpy", "sphinx"

    # LLM options
    provider: str = ""  # "ollama"
    url: str = ""  # "http://localhost:11434"
    model: str = ""  # "qwen3:8b"
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = 2000
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    # This are initialized after parsing pyproject.toml
    rule_set: RuleSet | None = None
    # segment_types: set[CodeSegmentType] | None = None
    # _cache_handler: CacheHandler | None = None

    @cached_property
    def scopes_types(self) -> set[CodeSegmentType]:
        """Returns the set of CodeSegmentTypes based on the current scopes."""
        return {
            CodeSegmentType.from_str(scope) for scope in (self.scopes or DEFAULT_SCOPES)
        }

    @cached_property
    def segment_types(self) -> set[CodeSegmentType]:
        """Lazily initializes and returns the set of CodeSegmentTypes based on the current scopes."""
        return {CodeSegmentType.from_str(scope) for scope in self.scopes_types}

    @cached_property
    def cache_handler(self) -> CacheHandler:
        """Lazily initializes and returns the CacheHandler based on the current rule set."""
        if self.rule_set is None:
            raise ValueError("RuleSet must be defined to use CacheHandler.")
        return CacheHandler(self.rule_set)

    @staticmethod
    def from_pyproject() -> DolceConfig:
        """
        Parses the pyproject.toml file and returns a DolceConfig instance with parsed settings.

        Returns:
            DolceConfig: A DolceConfig object initialized with configuration parameters extracted from the pyproject.toml file, including rule sets, excludes, and API key settings.
        """
        pyproject_path = Path("pyproject.toml")
        if not pyproject_path.exists():
            return DolceConfig()

        pyproject = toml.load(pyproject_path)
        tool = pyproject.get("tool", {})
        config = tool.get("dolce", {})

        config = {k.replace("-", "_"): v for k, v in config.items()}

        if "target" in config or "disable" in config:
            config["rule_set"] = RuleSet(
                target=config.get("target", None), disable=config.get("disable", None)
            )
        else:
            config["rule_set"] = RuleSet()

        if "exclude" not in config:
            config["exclude"] = DEFAULT_EXCLUDES

        api_key_env_var = config.get("api_key", None)
        config["api_key"] = (
            None if api_key_env_var is None else os.environ.get(api_key_env_var, None)
        )

        scopes = config.get("scopes", DEFAULT_SCOPES)
        config["segment_types"] = {CodeSegmentType.from_str(scope) for scope in scopes}

        return DolceConfig(**config)

    def update(self, **kwargs: Any) -> None:
        """Updates the object's attributes with provided keyword arguments, only setting non-None values for existing attributes."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
