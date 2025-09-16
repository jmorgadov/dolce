from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import toml


@dataclass
class DolceConfig:
    """Configuration for Dolce"""

    # General options
    ignore_missing: bool = False
    exclude: list[str] | None = None

    # Check options
    check_signature: bool = True
    check_description: bool = True

    # Signature options
    docsig_config: dict[str, Any] | None = None

    # LLM options
    provider: str = "ollama"
    url: str = "http://localhost:11434"
    model: str = "codestral"
    api_key: str | None = None
    temperature: float = 0.1
    max_tokens: int | None = None
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
        desc += f"Ignore Missing: {self.ignore_missing}\n"
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

        api_key_env_var = config.get("api_key", None)
        config["api_key"] = (
            None if api_key_env_var is None else os.environ.get(api_key_env_var, None)
        )

        docsig = tool.get("docsig", {})
        docsig["no_ansi"] = True
        _docsig_config = {k.replace("-", "_"): v for k, v in docsig.items()}
        config["docsig_config"] = _docsig_config

        return DolceConfig(**config)

    def update(self, **kwargs: Any) -> None:
        """Update configuration attributes."""
        for key, value in kwargs.items():
            if value is not None and hasattr(self, key):
                setattr(self, key, value)
