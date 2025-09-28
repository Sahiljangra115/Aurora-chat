from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()


@dataclass
class Provider:
    id: str
    label: str
    type: str
    default_model: str | None = None
    description: str | None = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "type": self.type,
            "default_model": self.default_model,
            "description": self.description,
        }


@dataclass
class Settings:
    api_base_url: str = field(default_factory=lambda: os.getenv("API_BASE_URL", "/api"))
    default_provider: str = field(default_factory=lambda: os.getenv("DEFAULT_PROVIDER", "openrouter"))
    openrouter_api_base: str = field(default_factory=lambda: os.getenv("OPENROUTER_API_BASE", "https://openrouter.ai/api/v1"))
    openrouter_api_key: str | None = field(default_factory=lambda: os.getenv("OPENROUTER_API_KEY"))
    ollama_api_base: str = field(default_factory=lambda: os.getenv("OLLAMA_API_BASE", "http://localhost:11434"))
    allow_ollama: bool = field(default_factory=lambda: os.getenv("ALLOW_OLLAMA", "true").lower() in {"1", "true", "yes"})

    def providers(self) -> List[Provider]:
        provider_specs = [
            Provider(
                id="openrouter",
                label="OpenRouter",
                type="remote",
                default_model=os.getenv("OPENROUTER_DEFAULT_MODEL", "x-ai/grok-4-fast:free"),
                description="Use any OpenRouter-compatible model by providing your OpenRouter API key."
            ),
            Provider(
                id="gemini",
                label="Gemini via OpenRouter",
                type="remote",
                default_model=os.getenv("GEMINI_DEFAULT_MODEL", "google/gemini-pro-1.5"),
                description="Gemini access proxied through OpenRouter. Requires an OpenRouter key."
            ),
            Provider(
                id="claude",
                label="Claude via OpenRouter",
                type="remote",
                default_model=os.getenv("CLAUDE_DEFAULT_MODEL", "anthropic/claude-3.5-sonnet"),
                description="Claude models served through OpenRouter with the same API key."
            ),
            Provider(
                id="qwen",
                label="Qwen via OpenRouter",
                type="remote",
                default_model=os.getenv("QWEN_DEFAULT_MODEL", "qwen/qwen2.5-7b-instruct"),
                description="Qwen models via OpenRouter for multilingual tasks."
            ),
        ]

        if self.allow_ollama:
            provider_specs.append(
                Provider(
                    id="ollama",
                    label="Ollama (Local)",
                    type="local",
                    default_model=os.getenv("OLLAMA_DEFAULT_MODEL", "llama3"),
                    description="Use any model available in your local Ollama installation."
                )
            )

        return provider_specs

    def as_template_context(self) -> Dict[str, Any]:
        return {
            "API_BASE_URL": self.api_base_url,
            "DEFAULT_PROVIDER": self.default_provider,
            "AVAILABLE_PROVIDERS": [provider.to_dict() for provider in self.providers()],
        }


settings = Settings()
