from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import toml

from pydolce.rules.rules import RuleSet

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


@dataclass
class DolceConfig:
    """Configuration for Dolce"""

    # Check options
    target: list[str] | None = None  # Specific rules to target
    disable: list[str] | None = None  # Specific rules to disable
    exclude: list[str] | None = None
    ignore_args: bool = False
    ignore_kwargs: bool = False

    rule_set: RuleSet | None = None

    # LLM options
    provider: str = "ollama"
    url: str = "http://localhost:11434"
    model: str = "qwen3:8b"
    api_key: str | None = None
    temperature: float = 0.0
    max_tokens: int | None = 2000
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    def describe(self) -> str:
        """Return a string description of the configuration."""

        desc = f"Provider: {self.provider}\n"
        desc += f"URL: {self.url}\n"
        desc += f"Model: {self.model}\n"
        if self.api_key:
            desc += "API Key: [REDACTED]\n"
        else:
            desc += "API Key: Not Set\n"
        return desc

    @staticmethod
    def from_pyproject() -> DolceConfig:
        """Load configuration from pyproject.toml if available."""
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

        return DolceConfig(**config)

    def update(self, **kwargs: Any) -> None:
        """Update configuration attributes."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
