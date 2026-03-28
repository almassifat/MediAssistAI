"""
Configuration module for MediAssist AI.
Handles environment variables and application settings.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Set

from dotenv import load_dotenv

# 🔥 Try multiple locations (bulletproof)
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = CURRENT_DIR.parent  # mediassist_ai/
ROOT_DIR = PROJECT_DIR.parent     # mediassist_ai_project/

# Try loading .env from all possible places
load_dotenv(PROJECT_DIR / ".env", override=True)
load_dotenv(ROOT_DIR / ".env", override=True)
load_dotenv(".env", override=True)


class Settings:
    """Centralized application settings."""

    def __init__(self) -> None:
        # --- LLM ---
        self.groq_api_key: str | None = os.getenv("GROQ_API_KEY")
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama3-8b-8192")

        # --- App ---
        self.temp_upload_dir: Path = Path(
            os.getenv("TEMP_UPLOAD_DIR", "temp_uploads")
        )

        # --- File types ---
        self.allowed_extensions: Set[str] = {
            ext.strip()
            for ext in os.getenv(
                "ALLOWED_EXTENSIONS", "png,jpg,jpeg,pdf"
            ).split(",")
        }

    def ensure_directories(self) -> None:
        self.temp_upload_dir.mkdir(parents=True, exist_ok=True)

    def debug(self) -> None:
        masked = None
        if self.groq_api_key:
            masked = self.groq_api_key[:6] + "..." + self.groq_api_key[-4:]

        print("🔥 GROQ_API_KEY:", masked)
        print("🔥 MODEL:", self.groq_model)
        print("🔥 ENV CWD:", os.getcwd())
        print("🔥 PROJECT_DIR:", PROJECT_DIR)


# Singleton
settings = Settings()

# Debug (keep this ON)
settings.debug()