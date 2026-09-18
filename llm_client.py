#!/usr/bin/env python3
"""Sqlantra unified LLM client: OpenRouter first, local Ollama fallback.

Strategy:
1. OPENROUTER_API_KEY set  -> OpenRouter chat-completions, free models,
   rotates through a fallback list on 429/HTTP errors, resets to primary.
2. Otherwise               -> local Ollama (kept for offline development).

Never prints credentials. The API key is read from the environment only.
"""

import json
import os
import time
import urllib.request
import urllib.error

DEFAULT_OPENROUTER_MODEL = "nvidia/nemotron-3-super-120b-a12b:free"
OPENROUTER_FALLBACK_MODELS = [
    "nvidia/nemotron-3-super-120b-a12b:free",
    "nvidia/nemotron-3.5-lightning:free",
    "google/gemma-4-26b-a4b-it:free",
    "google/gemma-4-31b-it:free",
]
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "qwen3.5:2b-q4_K_M")


def _openrouter_enabled() -> bool:
    return bool(os.environ.get("OPENROUTER_API_KEY"))


def _call_openrouter(prompt: str, timeout: int) -> str:
    key = os.environ["OPENROUTER_API_KEY"]
    models = list(OPENROUTER_FALLBACK_MODELS)
    last_err = None
    for i, model in enumerate(models):
        body = {
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 512,
            "temperature": 0.1,
        }
        retries = 3
        for attempt in range(retries):
            try:
                req = urllib.request.Request(
                    OPENROUTER_URL,
                    data=json.dumps(body).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {key}",
                    },
                )
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    out = json.loads(resp.read().decode())
                    return out["choices"][0]["message"]["content"].strip()
            except urllib.error.HTTPError as e:
                last_err = e
                if e.code == 429:
                    time.sleep(3 * (attempt + 1))
                    continue
                break
            except Exception as e:
                last_err = e
                if attempt < retries - 1:
                    time.sleep(2)
        if i < len(models) - 1:
            last_err = None
    raise last_err if last_err else RuntimeError("OpenRouter failed")


def _call_ollama(prompt: str, timeout: int) -> str:
    body = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 512},
    }
    req = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode()).get("response", "").strip()


def call_llm(prompt: str, timeout: int = 60) -> str:
    """Best-effort LLM completion.

    Returns model text on success, or a string starting with
    "Error calling LLM:" when every backend fails.
    """
    try:
        if _openrouter_enabled():
            return _call_openrouter(prompt, timeout)
        return _call_ollama(prompt, timeout)
    except Exception as e:
        return f"Error calling LLM: {e}"