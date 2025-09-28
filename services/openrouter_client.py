from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

import requests

logger = logging.getLogger(__name__)


class OpenRouterClient:
    """Lightweight wrapper around the OpenRouter chat completions API."""

    def __init__(self, api_base: str) -> None:
        self.api_base = api_base.rstrip("/")
        self.endpoint = f"{self.api_base}/chat/completions"

    def chat(
        self,
        messages: List[Dict[str, Any]],
        model: str,
        api_key: str,
        temperature: float = 0.7,
        top_p: float = 0.9,
    ) -> Dict[str, Any]:
        if not api_key:
            raise ValueError("OpenRouter API key is required for remote providers")

        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "top_p": top_p,
        }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "localhost",
            "X-Title": "Aurora Chat",
        }

        response = requests.post(self.endpoint, json=payload, headers=headers, timeout=60)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            logger.exception("OpenRouter request failed: %s", exc)
            error_payload: Optional[Dict[str, Any]] = None
            try:
                error_payload = response.json()
            except ValueError:
                error_payload = {"error": response.text}
            raise RuntimeError(error_payload.get("error", "OpenRouter request failed")) from exc

        data = response.json()
        if "choices" not in data or not data["choices"]:
            raise RuntimeError("OpenRouter returned no choices")

        return data
