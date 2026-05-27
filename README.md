# A.R.I.S. — Advanced Responsive Intelligence System

A JARVIS-style holographic AI assistant for superheroes — and anyone else who wants a sleek, conversational AI companion. Beautiful sci-fi chat interface backed by your choice of LLM.

![A.R.I.S. Screenshot](screenshot.png)

## ✦ Features

- **Holographic UI** — Animated orb, waveform thinking indicator, floating particles, sci-fi grid background
- **Two backends** — OpenAI-compatible API (OpenRouter, Together, Groq, etc.) or local Hermes Agent CLI
- **Fully in-character** — A.R.I.S. stays in persona: British butler crossed with supercomputer, dry wit included
- **Single binary** — One Python file, zero dependencies beyond stdlib
- **Mobile responsive** — Works on phone, tablet, or wall-mounted display
- **Suggestion chips** — Quick-start prompts for new commanders

## ✦ Quick Start

```bash
# 1. Clone
git clone https://github.com/achraf/aris.git
cd aris

# 2. Configure
cp .env.example .env
# Edit .env — add your OpenRouter or OpenAI API key

# 3. Launch
python server.py

# 4. Open
# http://localhost:8892
```

## ✦ Backends

### OpenAI-compatible (default)

Works with any provider that speaks the OpenAI chat completions API:

```env
BACKEND=openai
OPENAI_API_KEY=sk-or-v1-...
OPENAI_BASE_URL=https://openrouter.ai/api/v1
OPENAI_MODEL=deepseek/deepseek-chat
```

**Free models that work well:**
- `deepseek/deepseek-chat` (OpenRouter, very cheap)
- `google/gemini-2.0-flash-001` (OpenRouter, free tier)
- `meta-llama/llama-3.3-70b-instruct` (OpenRouter, free tier)

### Hermes CLI (local)

For existing [Hermes Agent](https://github.com/nousresearch/hermes-agent) setups:

```env
BACKEND=hermes
HERMES_BIN=/path/to/hermes
HERMES_MODEL=deepseek/deepseek-chat
```

## ✦ Project Structure

```
aris/
├── server.py          # Backend — HTTP server + LLM proxy
├── index.html         # Frontend — the holographic UI
├── .env.example       # Configuration template
└── README.md          # You're reading it
```

## ✦ How It Works

1. Browser loads `index.html` — the sci-fi chat interface
2. User types a message → `POST /chat` to the Python server
3. Server builds the prompt with A.R.I.S.'s system persona + conversation history
4. Forwards to your LLM backend (API or local Hermes)
5. Returns the response → rendered in the chat with typing animation

No frameworks. No build step. No API keys exposed to the client.

## ✦ Customization

**Change the AI persona** — Edit the `SYSTEM_PROMPT` variable in `server.py`. Want a sarcastic AI? A medieval scribe? A Star Trek computer? Just rewrite the prompt.

**Change the port** — Set `PORT=8080` in `.env`

**Add voice** — The frontend is vanilla HTML/JS. Add Web Speech API for voice input and the browser's built-in TTS for output in under 20 lines.

## ✦ License

MIT — do whatever you want with it.

---

*"At your service, sir." — A.R.I.S.*
