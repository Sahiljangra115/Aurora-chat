const APP = (() => {
  const config = window.APP_CONFIG ?? {
    apiBaseUrl: "/api",
    availableProviders: [],
    defaultProvider: "openrouter",
  };

  const dom = {
    providerSelect: document.getElementById("provider"),
    modelInput: document.getElementById("model"),
    temperature: document.getElementById("temperature"),
    topP: document.getElementById("top_p"),
    apiKey: document.getElementById("apiKey"),
    providerDescription: document.getElementById("provider-description"),
    sessionForm: document.getElementById("session-form"),
    chatForm: document.getElementById("chat-form"),
    messageField: document.getElementById("message"),
    chatLog: document.getElementById("chat-log"),
    clearBtn: document.getElementById("clear-btn"),
  };

  const sessionKey = "aurora-chat-session";
  const historyKey = "aurora-chat-history";
  const providerIndex = Object.fromEntries(
    (config.availableProviders ?? []).map((provider) => [provider.id, provider])
  );
  const state = {
    history: loadHistory(),
    session: loadSession() ?? {
      provider: config.defaultProvider,
      model: "",
      temperature: 0.7,
      top_p: 0.9,
      apiKey: "",
    },
  };

  function loadSession() {
    try {
      const raw = localStorage.getItem(sessionKey);
      return raw ? JSON.parse(raw) : null;
    } catch (error) {
      console.warn("Failed to load session", error);
      return null;
    }
  }

  function loadHistory() {
    try {
      const raw = localStorage.getItem(historyKey);
      return raw ? JSON.parse(raw) : [];
    } catch (error) {
      console.warn("Failed to load history", error);
      return [];
    }
  }

  function saveSession(session) {
    state.session = session;
    try {
      localStorage.setItem(sessionKey, JSON.stringify(session));
    } catch (error) {
      console.warn("Failed to persist session", error);
    }
  }

  function persistHistory() {
    try {
      localStorage.setItem(historyKey, JSON.stringify(state.history));
    } catch (error) {
      console.warn("Failed to persist history", error);
    }
  }

  function populateProviders() {
    const select = dom.providerSelect;
    select.innerHTML = "";

    config.availableProviders.forEach((provider) => {
      const option = document.createElement("option");
      option.value = provider.id;
      option.textContent = provider.label;
      select.append(option);
    });

    if (state.session?.provider) {
      select.value = state.session.provider;
    } else if (config.defaultProvider) {
      select.value = config.defaultProvider;
    }

    applyProviderUi(select.value);
  }

  function hydrateSessionForm() {
    const session = state.session;
    if (!session) return;

    dom.providerSelect.value = session.provider ?? config.defaultProvider;
    dom.modelInput.value = session.model ?? "";
    dom.temperature.value = session.temperature ?? 0.7;
    dom.topP.value = session.top_p ?? 0.9;
    dom.apiKey.value = session.apiKey ?? "";
  }

  async function fetchDefaultModel(providerId) {
    const provider = providerIndex[providerId];
    if (!provider) return "";

    if (provider.type === "local") {
      try {
        const { data } = await axios.get(`${config.apiBaseUrl}/models`, {
          params: { provider: providerId },
        });
        if (data?.models?.length) {
          return data.models[0];
        }
        if (data?.error) {
          showToast(data.error, "error");
        }
      } catch (error) {
        console.warn("Failed to fetch local models", error);
        showToast("Could not reach your local model host", "error");
      }
    }

    return provider.default_model ?? "";
  }

  function applyProviderUi(providerId) {
    const provider = providerIndex[providerId];
    if (!provider) return;

    if (dom.providerDescription) {
      dom.providerDescription.textContent = provider.description ?? "";
    }

    if (provider.type === "local") {
      dom.apiKey.disabled = true;
      dom.apiKey.placeholder = "Local providers do not require API keys";
    } else {
      dom.apiKey.disabled = false;
      dom.apiKey.placeholder = "Enter API key (kept locally)";
    }
  }

  function appendMessage(role, content) {
    const messageEl = document.createElement("div");
    messageEl.className = `chat-message ${role}`;

    const roleEl = document.createElement("div");
    roleEl.className = "chat-role";
    roleEl.textContent = role === "assistant" ? "Assistant" : "You";

    const contentEl = document.createElement("div");
    contentEl.className = "chat-content";
    contentEl.textContent = content;

    messageEl.append(roleEl, contentEl);
    dom.chatLog.append(messageEl);
    dom.chatLog.scrollTo({ top: dom.chatLog.scrollHeight, behavior: "smooth" });

    return messageEl;
  }

  function clearChat() {
    state.history = [];
    dom.chatLog.innerHTML = "";
    persistHistory();
  }

  async function handleSessionSubmit(event) {
    event.preventDefault();
    const formData = new FormData(dom.sessionForm);
    const session = {
      provider: formData.get("provider") ?? config.defaultProvider,
      model: formData.get("model")?.toString().trim() ?? "",
      temperature: Number(formData.get("temperature") ?? 0.7),
      top_p: Number(formData.get("top_p") ?? 0.9),
      apiKey: formData.get("apiKey")?.toString().trim() ?? "",
    };

    saveSession(session);
    showToast("Session updated", "success");
  }

  async function handleChatSubmit(event) {
    event.preventDefault();
    const message = dom.messageField.value.trim();
    if (!message) return;
    if (!state.session?.provider) {
      showToast("Select a provider first", "error");
      return;
    }

    dom.messageField.value = "";
    state.history.push({ role: "user", content: message });
    appendMessage("user", message);
    persistHistory();
    setFormDisabled(true);

    const payload = {
      message,
      history: state.history,
      provider: state.session.provider,
      model: state.session.model,
      temperature: Number(state.session.temperature ?? dom.temperature.value),
      top_p: Number(state.session.top_p ?? dom.topP.value),
      api_key: state.session.apiKey,
    };

    const provider = providerIndex[state.session.provider];
    if (provider?.type !== "remote") {
      delete payload.api_key;
    }

    const placeholder = {
      role: "assistant",
      content: "Thinking…",
    };
    appendMessage(placeholder.role, placeholder.content);
    const placeholderEl = dom.chatLog.lastElementChild;

    try {
      const { data } = await axios.post(`${config.apiBaseUrl}/chat`, payload);
      const assistantMessage = data?.message ?? "No response";
      state.history.push({ role: "assistant", content: assistantMessage });
      persistHistory();
      placeholderEl.querySelector(".chat-content").textContent =
        assistantMessage;
    } catch (error) {
      console.error(error);
      const errorMsg =
        error?.response?.data?.error ?? error.message ?? "Unknown error";
      placeholderEl.querySelector(
        ".chat-content"
      ).textContent = `Error: ${errorMsg}`;
    } finally {
      setFormDisabled(false);
    }
  }

  function setFormDisabled(disabled) {
    dom.messageField.disabled = disabled;
    dom.chatForm.querySelector("button[type='submit']").disabled = disabled;
  }

  function showToast(message, variant = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${variant}`;
    toast.textContent = message;
    document.body.append(toast);
    setTimeout(() => {
      toast.classList.add("visible");
    }, 10);
    setTimeout(() => {
      toast.classList.remove("visible");
      setTimeout(() => toast.remove(), 250);
    }, 3000);
  }

  function initListeners() {
    dom.sessionForm?.addEventListener("submit", handleSessionSubmit);
    dom.chatForm?.addEventListener("submit", handleChatSubmit);
    dom.clearBtn?.addEventListener("click", () => {
      clearChat();
      showToast("Chat cleared", "info");
    });

    dom.providerSelect?.addEventListener("change", async (event) => {
      const providerId = event.target.value;
      applyProviderUi(providerId);
      const defaultModel = await fetchDefaultModel(providerId);
      dom.modelInput.value = defaultModel;
      state.session.provider = providerId;
      state.session.model = defaultModel;
      saveSession(state.session);
    });

    dom.temperature?.addEventListener("input", (event) => {
      state.session.temperature = Number(event.target.value);
      saveSession(state.session);
    });

    dom.topP?.addEventListener("input", (event) => {
      state.session.top_p = Number(event.target.value);
      saveSession(state.session);
    });

    dom.modelInput?.addEventListener("input", (event) => {
      state.session.model = event.target.value;
      saveSession(state.session);
    });

    dom.apiKey?.addEventListener("input", (event) => {
      state.session.apiKey = event.target.value;
      saveSession(state.session);
    });
  }

  async function bootstrap() {
    populateProviders();
    hydrateSessionForm();
    initListeners();

    applyProviderUi(dom.providerSelect.value);

    if (state.history.length) {
      state.history.forEach((message) => {
        appendMessage(message.role, message.content);
      });
    }

    if (!state.session.model) {
      const defaultModel = await fetchDefaultModel(dom.providerSelect.value);
      dom.modelInput.value = defaultModel;
      state.session.model = defaultModel;
      saveSession(state.session);
    }
  }

  return {
    bootstrap,
  };
})();

document.addEventListener("DOMContentLoaded", APP.bootstrap);
