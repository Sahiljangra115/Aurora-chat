from __future__ import annotations

import logging
from typing import Any, Dict, List

from flask import Flask, jsonify, render_template, request

from config import settings
from services.openrouter_client import OpenRouterClient
from services.ollama_client import OllamaClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("aurora-chat")


def create_app() -> Flask:
    app = Flask(__name__)

    openrouter_client = OpenRouterClient(api_base=settings.openrouter_api_base)
    ollama_client = OllamaClient(api_base=settings.ollama_api_base)

    provider_map = {provider.id: provider for provider in settings.providers()}

    @app.route("/")
    def index() -> str:
        template_config = settings.as_template_context()
        template_config["AVAILABLE_PROVIDERS"] = [
            {
                **provider,
                "description": provider_map[provider["id"]].description,
            }
            for provider in template_config["AVAILABLE_PROVIDERS"]
        ]
        return render_template("index.html", config=template_config, title="Aurora Chat")

    @app.get("/api/config")
    def api_config() -> Any:
        return jsonify(settings.as_template_context())

    @app.get("/health")
    def health() -> Any:
        return jsonify({"status": "ok"})

    @app.get("/api/models")
    def api_models() -> Any:
        provider_id = request.args.get("provider", settings.default_provider)
        provider = provider_map.get(provider_id)
        if not provider:
            return jsonify({"error": f"Unknown provider '{provider_id}'"}), 400

        if provider.type != "local":
            return jsonify({"models": []})

        try:
            models = ollama_client.list_models()
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 502

        return jsonify({"models": models})

    @app.post("/api/chat")
    def api_chat() -> Any:
        payload: Dict[str, Any] = request.get_json(force=True, silent=True) or {}
        provider_id: str = payload.get("provider") or settings.default_provider
        provider = provider_map.get(provider_id)
        if not provider:
            return jsonify({"error": f"Unknown provider '{provider_id}'"}), 400

        model = payload.get("model") or provider.default_model
        if not model:
            return jsonify({"error": "Model is required"}), 400

        temperature = float(payload.get("temperature", 0.7))
        top_p = float(payload.get("top_p", 0.9))

        history: List[Dict[str, str]] = payload.get("history") or []
        if not history:
            message = payload.get("message")
            if not message:
                return jsonify({"error": "Message is required"}), 400
            history = [{"role": "user", "content": message}]

        try:
            if provider.type == "remote":
                api_key = (
                    payload.get("api_key")
                    or request.headers.get("X-Api-Key")
                    or settings.openrouter_api_key
                )
                response = openrouter_client.chat(
                    messages=history,
                    model=model,
                    api_key=api_key or "",
                    temperature=temperature,
                    top_p=top_p,
                )
                message = response["choices"][0]["message"]["content"].strip()
                usage = response.get("usage")

            else:
                response = ollama_client.chat(
                    messages=history,
                    model=model,
                    temperature=temperature,
                    top_p=top_p,
                )
                message = response.get("message", {}).get("content", "").strip()
                usage = response.get("eval_count")

        except ValueError as error:
            return jsonify({"error": str(error)}), 400
        except RuntimeError as error:
            return jsonify({"error": str(error)}), 502

        if not message:
            message = "No response"

        logger.info("Provider %s responded with %d characters", provider_id, len(message))

        return jsonify({
            "message": message,
            "usage": usage,
        })

    return app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

