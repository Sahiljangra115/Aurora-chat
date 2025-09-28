from __future__ import annotations

import logging
from typing import Dict, Any, List

import requests

logger = logging.getLogger(__name__)


class OllamaClient:
    """Simple HTTP wrapper for interacting with a local Ollama instance."""

    def __init__(self, api_base: str = "http://localhost:11434") -> None:
        self.api_base = api_base.rstrip("/")

    def list_models(self) -> List[str]:
        response = requests.get(f"{self.api_base}/api/tags", timeout=10)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.exception("Failed to list Ollama models: %s", exc)
            raise RuntimeError("Unable to reach Ollama. Is it running?") from exc

        data = response.json()
        return [model.get("name") for model in data.get("models", []) if model.get("name")]

    def chat(
        self,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        payload = {
            "model": model,
            "messages": messages,
            "options": {
                "temperature": temperature,
                "top_p": top_p,
            },
            "stream": False,
        }

        response = requests.post(f"{self.api_base}/api/chat", json=payload, timeout=120)
        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.exception("Ollama chat failed: %s", exc)
            error_payload = None
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {"error": response.text}
            raise RuntimeError(error_payload.get("error", "Ollama request failed")) from exc

        return response.json()
