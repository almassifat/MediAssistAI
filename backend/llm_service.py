"""
Language model service for MediAssist AI.

Improved version with:
- safer error handling
- cleaner fallback responses
- stronger prompt grounding
- reduced debug noise
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import requests

from .config import settings

logger = logging.getLogger(__name__)


GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"


def _fallback_response(prompt: str) -> str:
    """
    Safe fallback when LLM is unavailable.
    """
    lower_prompt = prompt.lower()

    if "bangla" in lower_prompt or "বাংলা" in lower_prompt:
        return (
            "দুঃখিত, এই মুহূর্তে AI ব্যাখ্যা সেবা পাওয়া যাচ্ছে না। "
            "তবে রিপোর্টটি প্রক্রিয়াকরণ হয়েছে। অনুগ্রহ করে পরে আবার চেষ্টা করুন "
            "অথবা একজন যোগ্য ডাক্তারের পরামর্শ নিন।"
        )

    return (
        "AI explanation is currently unavailable. "
        "However, the report was processed successfully. "
        "Please try again later or consult a licensed doctor for interpretation."
    )


def call_llm(
    prompt: str,
    model: Optional[str] = None,
    api_key: Optional[str] = None,
    max_tokens: int = 600,
) -> str:
    """
    Send prompt to Groq LLM and return generated response.
    """
    resolved_model = model or settings.groq_model or "llama-3.1-8b-instant"
    resolved_api_key = api_key or settings.groq_api_key

    if not resolved_api_key:
        logger.warning("No GROQ_API_KEY configured. Using fallback response.")
        return _fallback_response(prompt)

    headers = {
        "Authorization": f"Bearer {resolved_api_key}",
        "Content-Type": "application/json",
    }

    payload: Dict[str, Any] = {
        "model": resolved_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a careful medical report explanation assistant. "
                    "Only use the information explicitly provided in the prompt. "
                    "Do not invent lab values, diagnoses, or findings. "
                    "If data is incomplete or uncertain, clearly say so. "
                    "Explain results in simple, patient-friendly language. "
                    "Do not replace a doctor's judgment. "
                    "Avoid repetition and keep the answer structured and clear."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    try:
        response = requests.post(
            GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=30,
        )
        response.raise_for_status()

        data = response.json()

        choices = data.get("choices")
        if not choices:
            logger.error("Groq response missing 'choices': %s", data)
            return _fallback_response(prompt)

        message = choices[0].get("message", {})
        content = message.get("content", "")

        if not content or not content.strip():
            logger.warning("Groq returned empty content.")
            return _fallback_response(prompt)

        output = content.strip()
        output = output.replace("\n\n\n", "\n\n")

        return output

    except requests.exceptions.Timeout:
        logger.error("Groq request timed out.")
        return _fallback_response(prompt)

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response is not None else "unknown"
        error_text = e.response.text[:300] if e.response is not None else "no response body"
        logger.error("HTTP error from Groq (%s): %s", status_code, error_text)

        if status_code in (401, 403):
            return "Language model authentication failed. Please check API configuration."
        if status_code == 429:
            return "Language model rate limit exceeded. Please try again shortly."

        return _fallback_response(prompt)

    except requests.exceptions.RequestException as e:
        logger.error("Network error while calling Groq: %s", e, exc_info=True)
        return _fallback_response(prompt)

    except Exception as e:
        logger.error("Unexpected LLM error: %s", e, exc_info=True)
        return _fallback_response(prompt)