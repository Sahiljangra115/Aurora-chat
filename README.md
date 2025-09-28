# Aurora Chat Bot

A modern plug-and-play chat interface that runs entirely on your machine. Connect to OpenRouter-backed models (Gemini, Claude, Qwen, etc.) or switch to a local Ollama model without leaving the page. The project serves a responsive landing page, a persistent chat UI, and a Flask API that brokers requests to cloud or local providers.

## ✨ Features

- Responsive landing page with a dark glassmorphism aesthetic
- Session-aware chat interface with localStorage persistence and quick provider switching
- Flask backend API with health, model discovery, and chat endpoints
- Remote provider support through OpenRouter (Gemini, Claude, Qwen, and more)
- Local model support via Ollama with automatic detection of installed models
- Simple configuration through `.env` and per-session overrides stored in the browser

## 🚀 Quick start

```bash
# 1. Clone the repository
git clone https://github.com/Sahiljangra115/Aurora-chat.git
cd Aurora-chat

# 2. Create a virtual environment (optional but recommended)
python -m venv .venv
source .venv/bin/activate

# 3. Install backend dependencies
pip install -r requirements.txt

# 4. Configure environment values
cp .env.example .env
# Edit .env to add your OpenRouter API key or adjust defaults

# 5. Launch the Flask development server
flask --app main run --debug
# The site is now available at http://localhost:5000
```

> **Tip:** If you prefer `python -m flask run`, set `export FLASK_APP=main` first (or use `set` on Windows).

## ⚙️ Configuration

Environment configuration lives in `.env` (see `.env.example` for defaults):

| Variable               | Purpose                                                                               |
| ---------------------- | ------------------------------------------------------------------------------------- |
| `API_BASE_URL`         | Base path for API routes exposed to the frontend. Default: `/api`.                    |
| `DEFAULT_PROVIDER`     | Provider auto-selected on first load. Default: `openrouter`.                          |
| `OPENROUTER_API_KEY`   | Optional server-side OpenRouter key fallback. Users can also supply keys per session. |
| `OPENROUTER_API_BASE`  | Override the OpenRouter endpoint (useful for proxies).                                |
| `*_DEFAULT_MODEL`      | Configure initial models for each remote provider.                                    |
| `ALLOW_OLLAMA`         | Enable/disable local provider option (`true`/`false`).                                |
| `OLLAMA_API_BASE`      | URL to your Ollama instance (defaults to `http://localhost:11434`).                   |
| `OLLAMA_DEFAULT_MODEL` | Default local model name to prefill.                                                  |

Per-user preferences—provider, model, temperature, API key—are stored securely in the browser via `localStorage` and only sent to your local backend.

## 🧠 Using local models with Ollama

1. [Install Ollama](https://ollama.com/) and start it (`ollama serve`).
2. Pull at least one model, for example:
   ```bash
   ollama pull llama3
   ```
3. Keep Ollama running and start the Flask app. The UI will display “Ollama (Local)” if `ALLOW_OLLAMA=true`.
4. When selected, the app fetches your available models via `/api/models` and no API key is required.

## 🔌 API routes

| Method | Route                         | Description                                                                   |
| ------ | ----------------------------- | ----------------------------------------------------------------------------- |
| `GET`  | `/`                           | Landing page + chat UI                                                        |
| `GET`  | `/health`                     | Lightweight readiness probe                                                   |
| `GET`  | `/api/config`                 | Returns public configuration for the frontend                                 |
| `GET`  | `/api/models?provider=ollama` | Lists locally available Ollama models                                         |
| `POST` | `/api/chat`                   | Sends chat history to the selected provider and returns the assistant message |

Requests to `/api/chat` accept:

```json
{
  "provider": "openrouter",
  "model": "openrouter/openai/gpt-4o-mini",
  "message": "Hello there!",
  "history": [{ "role": "user", "content": "Hello there!" }],
  "temperature": 0.7,
  "top_p": 0.9,
  "api_key": "sk-..." // optional when server .env already has OPENROUTER_API_KEY
}
```

## 🗂️ Project structure

```
.
├── config.py              # Environment-driven settings + provider catalog
├── main.py                # Flask application factory and routes
├── services/
│   ├── ollama_client.py   # Local Ollama helper
│   └── openrouter_client.py # OpenRouter REST helper
├── static/
│   ├── css/styles.css     # Global styles for landing + chat
│   ├── js/app.js          # Frontend logic & API integration
│   └── favicon.svg        # App icon
├── templates/
│   ├── base.html
│   └── index.html
├── .env.example           # Starter environment file
└── requirements.txt       # Backend dependencies
```

## 🧩 Development notes

- Run `python -m compileall .` after edits to ensure there are no syntax issues.
- The frontend uses vanilla JS; you can extend it with your favourite framework if needed.
- For production, consider setting `FLASK_ENV=production` and placing Flask behind a production-grade server (Gunicorn, uvicorn, etc.).

## 🤝 Contributing

Pull requests, issues, and feature ideas are welcome. If you add additional providers (e.g., Azure OpenAI, Hugging Face Inference), update both `config.py` and the README so others can benefit.
