"""Groq AI engine for intelligence analysis."""

import os
from typing import Generator, Optional

from groq import Groq

from . import settings
from .config import DEFAULT_MODEL

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


def _client() -> Groq:
    key = settings.get("groq_api_key") or os.environ.get("GROQ_API_KEY", "")
    if not key:
        raise ValueError(
            "No Groq API key configured. Run: intel settings set groq_api_key <key>"
        )
    return Groq(api_key=key)


def analyze(prompt: str, context: Optional[str] = None, stream: bool = True) -> Generator[str, None, None]:
    """Stream an AI analysis response."""
    model = settings.get("model", DEFAULT_MODEL)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    if context:
        messages.append({"role": "user", "content": f"Context data:\n{context}"})
    messages.append({"role": "user", "content": prompt})

    client = _client()
    if stream:
        with client.chat.completions.stream(
            model=model,
            messages=messages,
            max_tokens=4096,
            temperature=0.3,
        ) as s:
            for chunk in s:
                delta = chunk.choices[0].delta.content
                if delta:
                    yield delta
    else:
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            max_tokens=4096,
            temperature=0.3,
        )
        yield resp.choices[0].message.content or ""


def analyze_full(prompt: str, context: Optional[str] = None) -> str:
    """Return full analysis as a single string (no streaming)."""
    return "".join(analyze(prompt, context, stream=False))
