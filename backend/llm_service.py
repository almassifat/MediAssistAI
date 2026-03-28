"""
Language model service for MediAssist AI.

Improved version with better prompt control, safer handling,
and higher-quality responses.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)


def call_llm(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 600,   # 🔥 slightly increased for better answers
) -> str:
    """
    Send prompt to Groq LLM and return generated response.
    """

    model = model or settings.groq_model or "llama-3.1-8b-instant"
    api_key = api_key or settings.groq_api_key

    # ---------------- DEBUG ---------------- #
    masked_key = api_key[:6] + "..." + api_key[-4:] if api_key else None
    print("🔥 LLM DEBUG → KEY:", masked_key)
    print("🔥 LLM DEBUG → MODEL:", model)

    # ---------------- FALLBACK ---------------- #
    if not api_key:
        logger.warning("No GROQ_API_KEY → using fallback response")

        preview = prompt[:200]

        return (
            f"Summary: {preview}...\n"
            f"Explanation: LLM unavailable because GROQ_API_KEY is not configured."
        )

    # ---------------- REQUEST SETUP ---------------- #
    url = "https://api.groq.com/openai/v1/chat/completions"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an expert medical assistant. "
                    "Explain lab reports clearly, accurately, and safely. "
                    "Avoid repetition. Use structured explanations. "
                    "If values are abnormal, explain why and what it means."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.3,   # 🔥 slightly higher → more natural output
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30,
        )

        print("🔥 LLM STATUS:", response.status_code)
        print("🔥 LLM RAW RESPONSE:", response.text[:400])

        response.raise_for_status()

        data = response.json()

        if "choices" not in data:
            logger.error("Invalid response structure: %s", data)
            return "LLM ERROR → Invalid response format from API."

        output = data["choices"][0]["message"]["content"].strip()

        # 🔥 CLEAN OUTPUT (important)
        output = output.replace("\n\n\n", "\n\n").strip()

        return output

    # ---------------- HTTP ERROR ---------------- #
    except requests.exceptions.HTTPError as e:
        error_body = e.response.text if e.response is not None else "No response body"
        logger.error("HTTP error from Groq: %s", error_body)
        return f"LLM ERROR → {error_body}"

    # ---------------- NETWORK / OTHER ERROR ---------------- #
    except Exception as e:
        logger.error("LLM API call failed: %s", e, exc_info=True)
        return "LLM ERROR → Unable to reach language model."