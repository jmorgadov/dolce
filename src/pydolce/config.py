from __future__ import annotations

import os
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Any

import toml

from pydolce.core.cache import CacheHandler
from pydolce.core.parser import CodeSegmentType
from pydolce.core.rules import filters
from pydolce.core.rules.rulesets import (
    ALL_RULES,
    DEFAULT_RULES,
    RULE_REFERENCES,
    RuleSet,
)

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

DEFAULT_SCOPES = ["function", "class", "method", "property"]


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

    @cached_property
    def rule_set(self) -> RuleSet:
        if self.target is None and self.disable is None:
            return DEFAULT_RULES

        rules = filters.only(self.target, ALL_RULES) if self.target else DEFAULT_RULES
        if self.disable:
            rules = filters.exclude(self.disable, rules)

        return rules

    @cached_property
    def segment_types(self) -> set[CodeSegmentType]:
        """Lazily initializes and returns the set of CodeSegmentTypes based on the current scopes."""
        return {
            CodeSegmentType.from_str(scope) for scope in (self.scopes or DEFAULT_SCOPES)
        }

    @cached_property
    def cache_handler(self) -> CacheHandler:
        """Lazily initializes and returns the CacheHandler based on the current rule set."""
        return CacheHandler()

    def validate(self) -> None:
        """Validates the configuration to ensure all required fields are set correctly."""
        if invalid_refs := [
            ref for ref in (self.disable or []) if ref not in RULE_REFERENCES
        ]:
            raise ValueError(f"Invalid rule references in target: {invalid_refs}")

        if invalid_refs := [
            ref for ref in (self.target or []) if ref not in RULE_REFERENCES
        ]:
            raise ValueError(f"Invalid rule references in disable: {invalid_refs}")

        valid_scopes = [scope.lower() for scope in CodeSegmentType.__members__.keys()]
        if self.scopes is not None and (
            invalid_scopes := [
                scope for scope in self.scopes if scope.lower() not in valid_scopes
            ]
        ):
            raise ValueError(
                f"Invalid scopes: {invalid_scopes}. "
                "Supported scopes are 'function', 'class', 'method'."
            )

        if self.ensure_style is not None and self.ensure_style.lower() not in {
            "google",
            "numpy",
            "sphinx",
            "rest",
            "epy",
        }:
            raise ValueError(
                f"Invalid docstring style: {self.ensure_style}. "
                "Supported styles are 'google', 'numpy', 'sphinx', 'rest', 'epy'."
            )

        if self.url and (not self.model or not self.provider):
            raise ValueError("Both model and provider must be set if url is provided.")

        if self.temperature < 0.0 or self.temperature > 1.0:
            raise ValueError("Temperature must be between 0.0 and 1.0.")

        if self.timeout <= 0:
            raise ValueError("Timeout must be a positive integer.")

        if self.max_retries < 0:
            raise ValueError("Max retries must be a non-negative integer.")

        if self.retry_delay < 0.0:
            raise ValueError("Retry delay must be a non-negative float.")

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

        if "exclude" not in config:
            config["exclude"] = DEFAULT_EXCLUDES

        api_key_env_var = config.get("api_key", None)
        config["api_key"] = (
            None if api_key_env_var is None else os.environ.get(api_key_env_var, None)
        )

        config = DolceConfig(**config)
        config.validate()
        return config

    def update(self, **kwargs: Any) -> None:
        """Updates the object's attributes with provided keyword arguments, only setting non-None values for existing attributes."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
