"""
utils/llm.py — Thin wrapper around Groq API
"""

import json
import re
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL


_client = None

def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def chat(system: str, user: str, temperature: float = 0.4, max_tokens: int = 2048) -> str:
    """Single-turn chat completion. Returns the assistant text."""
    client = get_client()
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user",   "content": user},
        ],
        temperature=temperature,
        max_tokens=max_tokens,
    )
    return response.choices[0].message.content.strip()


def chat_json(system: str, user: str, temperature: float = 0.3) -> dict | list:
    """
    Like chat() but expects JSON back.
    Strips markdown fences and parses. Raises ValueError on failure.
    """
    raw = chat(system, user + "\n\nRespond ONLY with valid JSON. No explanation, no markdown fences.", temperature)
    # strip possible ```json ... ``` wrappers
    clean = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw.strip())
    try:
        return json.loads(clean)
    except json.JSONDecodeError as e:
        raise ValueError(f"LLM returned invalid JSON:\n{raw}\n\nError: {e}")
