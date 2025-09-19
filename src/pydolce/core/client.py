from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

import requests

from pydolce.config import DolceConfig

logger = logging.getLogger(__name__)


class ProviderType(Enum):
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    TOGETHER = "together"
    GENERIC_OPENAI = "generic_openai"  # For any OpenAI-compatible API


@dataclass
class LLMConfig:
    """Configuration for LLM client"""

    base_url: str
    model: str
    api_key: str | None = None
    provider: ProviderType | None = None
    temperature: float = 0.1
    max_tokens: int | None = None
    timeout: int = 120
    max_retries: int = 3
    retry_delay: float = 1.0

    @staticmethod
    def from_dolce_config(config: DolceConfig) -> LLMConfig:
        """Create LLMConfig from DolceConfig"""
        provider = ProviderType(config.provider.lower()) if config.provider else None
        return LLMConfig(
            base_url=config.url,
            model=config.model,
            api_key=config.api_key,
            provider=provider,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            timeout=config.timeout,
            max_retries=config.max_retries,
            retry_delay=config.retry_delay,
        )


class LLMError(Exception):
    """Base exception for LLM operations"""

    pass


class LLMClient:
    """Universal LLM client supporting multiple providers"""

    def __init__(self, config: LLMConfig):
        self.config = config
        self.provider = self._detect_provider()
        self.headers = self._build_headers()

    @staticmethod
    def from_dolce_config(config: DolceConfig) -> LLMClient:
        """Create LLMClient from DolceConfig"""
        llm_config = LLMConfig.from_dolce_config(config)
        return LLMClient(llm_config)

    def _detect_provider(self) -> ProviderType:
        """Auto-detect provider based on URL if not specified"""
        if self.config.provider:
            return self.config.provider

        url = self.config.base_url.lower()
        if "localhost:11434" in url or ("/api" in url and "ollama" in url):
            return ProviderType.OLLAMA
        elif "api.openai.com" in url:
            return ProviderType.OPENAI
        elif "api.anthropic.com" in url:
            return ProviderType.ANTHROPIC
        elif "api.groq.com" in url:
            return ProviderType.GROQ
        elif "api.together.xyz" in url:
            return ProviderType.TOGETHER
        else:
            return ProviderType.GENERIC_OPENAI  # Assume OpenAI-compatible

    def _build_headers(self) -> Dict[str, str]:
        """Build headers based on provider"""
        headers = {"Content-Type": "application/json"}

        if self.config.api_key:
            if self.provider == ProviderType.ANTHROPIC:
                headers["x-api-key"] = self.config.api_key
                headers["anthropic-version"] = "2023-06-01"
            else:
                headers["Authorization"] = f"Bearer {self.config.api_key}"

        return headers

    def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using the configured LLM"""
        for attempt in range(self.config.max_retries):
            try:
                if self.provider == ProviderType.OLLAMA:
                    return self._ollama_generate(prompt, **kwargs)
                elif self.provider == ProviderType.ANTHROPIC:
                    return self._anthropic_generate(prompt, **kwargs)
                else:
                    # OpenAI-compatible (covers OpenAI, Groq, Together, etc.)
                    return self._openai_generate(prompt, **kwargs)

            except requests.exceptions.RequestException as e:
                if attempt == self.config.max_retries - 1:
                    raise LLMError(
                        f"Failed after {self.config.max_retries} attempts: {e}"
                    ) from e
                logger.warning("Attempt %d failed: %s", attempt + 1, e)
                time.sleep(
                    self.config.retry_delay * (2**attempt)
                )  # Exponential backoff
        raise LLMError("Unreachable code reached in generate()")

    def _ollama_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate using Ollama API"""
        data = {
            "model": self.config.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": kwargs.get("temperature", self.config.temperature),
                "num_predict": kwargs.get("max_tokens", self.config.max_tokens),
            },
        }

        # Add any additional Ollama-specific options
        if "system" in kwargs:
            data["system"] = kwargs["system"]

        response = requests.post(
            f"{self.config.base_url}/api/generate",
            headers=self.headers,
            json=data,
            timeout=self.config.timeout,
        )
        response.raise_for_status()

        result = response.json()
        return result["response"]

    def _openai_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate using OpenAI-compatible API"""
        messages = kwargs.get("messages", [{"role": "user", "content": prompt}])

        # If prompt is provided directly, use it as user message
        if isinstance(prompt, str) and "messages" not in kwargs:
            messages = [{"role": "user", "content": prompt}]
            if "system" in kwargs:
                messages.insert(0, {"role": "system", "content": kwargs["system"]})

        data = {
            "model": self.config.model,
            "messages": messages,
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }

        # Add provider-specific parameters
        if self.provider == ProviderType.GROQ:
            # Groq has some specific parameters
            data.update({"top_p": kwargs.get("top_p", 1.0), "stream": False})

        endpoint = "/chat/completions"
        if self.provider == ProviderType.TOGETHER:
            endpoint = "/v1/chat/completions"
        elif not self.config.base_url.endswith(("/v1", "/api")):
            endpoint = "/v1/chat/completions"

        response = requests.post(
            f"{self.config.base_url}{endpoint}",
            headers=self.headers,
            json=data,
            timeout=self.config.timeout,
        )
        response.raise_for_status()

        result = response.json()
        return result["choices"][0]["message"]["content"]

    def _anthropic_generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate using Anthropic API"""
        data = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens or 1000),
            "messages": [{"role": "user", "content": prompt}],
            "temperature": kwargs.get("temperature", self.config.temperature),
        }

        if "system" in kwargs:
            data["system"] = kwargs["system"]

        response = requests.post(
            f"{self.config.base_url}/v1/messages",
            headers=self.headers,
            json=data,
            timeout=self.config.timeout,
        )
        response.raise_for_status()

        result = response.json()
        return result["content"][0]["text"]

    def list_models(self) -> List[str]:
        """List available models (works for Ollama and OpenAI-compatible)"""
        try:
            if self.provider == ProviderType.OLLAMA:
                response = requests.get(
                    f"{self.config.base_url}/api/tags", timeout=self.config.timeout
                )
                response.raise_for_status()
                models = response.json().get("models", [])
                return [model["name"] for model in models]
            else:
                response = requests.get(
                    f"{self.config.base_url}/models",
                    headers=self.headers,
                    timeout=self.config.timeout,
                )
                response.raise_for_status()
                models = response.json().get("data", [])
                return [model["id"] for model in models]
        except Exception as e:
            logger.warning("Failed to list models: %s", e)
            return []

    def test_connection(self) -> bool:
        """Test if the LLM service is available"""
        try:
            if self.provider == ProviderType.OLLAMA:
                response = requests.get(f"{self.config.base_url}/api/tags", timeout=5)
                return response.status_code == 200
            else:
                test_prompt = "Hi"
                self.generate(test_prompt, max_tokens=1)
                return True
        except Exception:
            return False
