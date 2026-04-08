"""Ollama AI engine for intelligence analysis (local, no API key required)."""

import subprocess
from typing import Generator, Optional

from . import settings

SYSTEM_PROMPT = """You are an elite intelligence analyst with expertise in OSINT, SIGINT,
geopolitical analysis, power structure research, and anomalous phenomena investigation.

Your role:
- Synthesize information from multiple open-source intelligence sources
- Identify patterns, relationships, and anomalies
- Provide objective, evidence-based analysis
- Clearly distinguish between confirmed facts, inferences, and speculation
- Cite data sources when known
- Flag inconsistencies and data gaps
- Never fabricate facts, names, dates, or events

When analyzing UAP/anomalous phenomena, apply scientific skepticism while remaining
open to unconventional hypotheses. Distinguish between witness testimony, declassified
government documentation, and speculation.

Format responses in Markdown with clear sections. Use tables where they aid clarity.
"""

OLLAMA_MODELS = [
    "llama3.2",
    "llama3.1:8b",
    "mistral",
    "deepseek-r1:7b",
    "gemma2:9b",
]


def _is_ollama_running() -> bool:
    """Check if Ollama server is reachable."""
    try:
        import httpx
        url = settings.get("ollama_url", "http://localhost:11434")
        r = httpx.get(f"{url}/api/tags", timeout=3)
        return r.status_code == 200
    except Exception:
        return False


def list_models() -> list[str]:
    """Return available Ollama models, or defaults if server unreachable."""
    try:
        import ollama
        result = ollama.list()
        models = result.get("models", []) if isinstance(result, dict) else list(result)
        return [m.get("name", m) if isinstance(m, dict) else str(m) for m in models] or OLLAMA_MODELS
    except Exception:
        return OLLAMA_MODELS


def analyze(prompt: str, context: Optional[str] = None, stream: bool = True) -> Generator[str, None, None]:
    """Stream an AI analysis response from local Ollama."""
    model = settings.get("ollama_model", "llama3.2")
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "user", "content": f"Context data:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    try:
        import ollama
        url = settings.get("ollama_url", "http://localhost:11434")
        client = ollama.Client(host=url)
        if stream:
            response = client.chat(model=model, messages=messages, stream=True)
            for chunk in response:
                content = chunk.get("message", {}).get("content", "") if isinstance(chunk, dict) else ""
                if content:
                    yield content
        else:
            response = client.chat(model=model, messages=messages, stream=False)
            content = response.get("message", {}).get("content", "") if isinstance(response, dict) else ""
            yield content or ""
    except Exception as e:
        err = str(e)
        if "connection" in err.lower() or "refused" in err.lower() or "connect" in err.lower():
            yield (
                "**Ollama not reachable.**\n\n"
                "To use AI analysis, install and start Ollama:\n"
                "1. Download from https://ollama.com/download\n"
                "2. Run: `ollama pull llama3.2`\n"
                "3. Ollama starts automatically in the background\n\n"
                "Once running, retry your question."
            )
        else:
            yield f"**AI Error:** {err}"


def analyze_full(prompt: str, context: Optional[str] = None) -> str:
    """Return full analysis as a single string (no streaming)."""
    return "".join(analyze(prompt, context, stream=False))
