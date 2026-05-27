#!/usr/bin/env python3
"""
A.R.I.S. — Advanced Responsive Intelligence System
===================================================
A JARVIS-style holographic AI assistant. Serves a beautiful sci-fi chat UI
and proxies conversations to your LLM backend of choice.

Supports two backends:
  • openai  — Any OpenAI-compatible API (OpenRouter, Together, Groq, etc.)
  • hermes  — Local Hermes Agent CLI (for existing Hermes setups)

Quick start:
  1. cp .env.example .env
  2. Edit .env with your API key
  3. python server.py
  4. Open http://localhost:8892
"""

import json
import os
import re
import subprocess
import sys
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse
from urllib.request import Request, urlopen
from urllib.error import URLError

# ── Configuration ──────────────────────────────────────────────────────────

def load_env(path=None):
    """Load .env file into os.environ if it exists."""
    if path is None:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.isfile(path):
        with open(path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, val = line.partition("=")
                    os.environ[key.strip()] = val.strip().strip('"').strip("'")

load_env()

PORT = int(os.environ.get("PORT", "8892"))
BACKEND = os.environ.get("BACKEND", "openai")
STATIC_DIR = os.path.dirname(os.path.abspath(__file__))

# OpenAI backend config
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.environ.get("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "deepseek/deepseek-chat")

# Hermes backend config
HERMES_BIN = os.environ.get("HERMES_BIN", "/usr/local/lib/hermes-agent/venv/bin/hermes")
HERMES_MODEL = os.environ.get("HERMES_MODEL", "deepseek/deepseek-chat")

SYSTEM_PROMPT = """You are A.R.I.S. (Advanced Responsive Intelligence System) — a cutting-edge holographic AI assistant, like JARVIS from Iron Man. You serve a superhero — the person you're talking to is your commander, a hero protecting the world.

Your personality:
- Calm, composed, and highly competent — never flustered
- Speaks with elegance and precision, like a British butler crossed with a supercomputer
- Dry wit and subtle humor — you can crack a joke but never at the expense of professionalism
- Calls the user "sir" or by their hero alias if they've shared it
- Occasionally references fictional superhero tech or scenarios playfully
- Concise but thorough — you don't ramble

Your capabilities (in-character):
- You can discuss ANY topic — science, strategy, philosophy, tech, personal advice, creative ideas
- You have access to "global databases" (your training data)
- You can offer tactical analysis, research summaries, creative brainstorming
- You're the voice of reason and wisdom for a busy hero

Format rules:
- Keep responses under 250 words unless asked for detail
- Use plain text — no markdown, no asterisks, no hashtags
- One message per response — don't simulate a conversation
- Stay in character ALWAYS

The user's first message is below. Respond as A.R.I.S."""

# ── Backend Handlers ────────────────────────────────────────────────────────

def call_openai(message, history):
    """Send chat to an OpenAI-compatible API and return the response text."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    for msg in history[-10:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg["content"]})

    messages.append({"role": "user", "content": message})

    body = json.dumps({
        "model": OPENAI_MODEL,
        "messages": messages,
        "max_tokens": 400,
        "temperature": 0.8,
    }).encode("utf-8")

    url = OPENAI_BASE_URL.rstrip("/") + "/chat/completions"
    req = Request(url, data=body, headers={
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}",
    })

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            return data["choices"][0]["message"]["content"].strip()
    except URLError as e:
        return f"Neural link disrupted, sir. {str(e.reason)[:100]}"
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        return f"Unusual interference in the data stream, sir. {str(e)[:80]}"

def call_hermes(message, history):
    """Send chat to local Hermes Agent CLI and return the response text."""
    context = ""
    for msg in history[-6:]:
        role = "Commander" if msg.get("role") == "user" else "A.R.I.S."
        context += f"{role}: {msg['content']}\n"

    prompt = f"{SYSTEM_PROMPT}\n\nRecent conversation:\n{context}\nCommander: {message}\n\nA.R.I.S.:"

    try:
        result = subprocess.run(
            [HERMES_BIN, "chat", "-q", prompt, "-m", HERMES_MODEL],
            capture_output=True, text=True, timeout=30,
            env={**os.environ, "HERMES_HOME": os.environ.get("HERMES_HOME", "/root/.hermes")},
        )
    except FileNotFoundError:
        return "Critical error: Hermes core systems offline. Please check the server configuration, sir."
    except subprocess.TimeoutExpired:
        return "My apologies, sir — the neural link appears to be experiencing latency."

    raw = result.stdout
    clean = re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', raw)
    clean = re.sub(r'\r', '', clean)

    box = re.search(r'╭─[^\n]*╮\s*\n(.*?)\n\s*╰─', clean, re.DOTALL)
    if box:
        text = box.group(1).strip()
        text = '\n'.join(line.strip() for line in text.split('\n'))
    else:
        parts = clean.split('────────────────────────────────────────')
        text = parts[2].strip() if len(parts) >= 3 else clean.strip()

    for noise in ['Query:', '⚠️', 'Initializing agent', 'Resume this session',
                  'Session:', 'Duration:', 'Messages:', 'hermes --resume']:
        text = '\n'.join(l for l in text.split('\n') if noise not in l)

    return text.strip() or "I seem to be experiencing some interference, sir."

# ── HTTP Server ─────────────────────────────────────────────────────────────

class ChatHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            path = "/index.html"
        file_path = os.path.join(STATIC_DIR, path.lstrip("/"))

        if not os.path.abspath(file_path).startswith(STATIC_DIR):
            self.send_error(403); return

        if os.path.isfile(file_path):
            ct = {".html": "text/html", ".css": "text/css", ".js": "application/javascript",
                  ".json": "application/json", ".png": "image/png", ".jpg": "image/jpeg",
                  ".svg": "image/svg+xml", ".ico": "image/x-icon"}.get(
                  os.path.splitext(file_path)[1], "application/octet-stream")
            with open(file_path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", ct)
            self.send_header("Content-Length", len(data))
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(data)
        else:
            self.send_error(404)

    def do_POST(self):
        if self.path != "/chat":
            self.send_error(404); return

        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length)

        try:
            data = json.loads(body)
            message = data.get("message", "").strip()
            history = data.get("history", [])
        except (json.JSONDecodeError, KeyError):
            self.send_error(400); return
        if not message:
            self.send_error(400); return

        if BACKEND == "hermes":
            response_text = call_hermes(message, history)
        else:
            if not OPENAI_API_KEY:
                response_text = "System not configured, sir. Please set OPENAI_API_KEY in .env"
            else:
                response_text = call_openai(message, history)

        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps({"response": response_text}).encode())

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

if __name__ == "__main__":
    print(f"  ◆  A.R.I.S. online — port {PORT}  ◆")
    print(f"  Backend: {BACKEND}")
    server = HTTPServer(("0.0.0.0", PORT), ChatHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  ◆  Shutting down. Goodbye, Commander.")
        server.shutdown()
