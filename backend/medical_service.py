"""
Orchestration layer for MediAssist AI.

Improved version with better prompt quality, cleaner summary,
and stronger medical explanations.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple
import uuid

from fastapi import UploadFile

from .config import settings
from .llm_service import call_llm
from .ocr_service import extract_text_from_file
from .parser_service import parse_report_text
from .models import DetectedParameter


logger = logging.getLogger(__name__)


def _save_upload_file(upload_file: UploadFile, destination_dir: Path) -> Path:
    """Safely save uploaded file"""

    # 🔥 FIX: handle None filename + avoid overwrite
    filename = upload_file.filename or f"upload_{uuid.uuid4().hex}.dat"
    filename = Path(filename).name  # sanitize

    dest_path = destination_dir / filename

    with dest_path.open("wb") as buffer:
        buffer.write(upload_file.file.read())

    return dest_path


def analyze_report(
    upload_file: UploadFile,
    language: str = "English"
) -> Tuple[str, str, List[DetectedParameter], str, str]:

    settings.ensure_directories()

    temp_path = _save_upload_file(upload_file, settings.temp_upload_dir)
    logger.info("Saved uploaded file to %s", temp_path)

    try:
        raw_text = extract_text_from_file(temp_path)
    finally:
        try:
            temp_path.unlink()
        except Exception:
            pass

    # ---------------- CLEAN + PARSE ---------------- #
    cleaned_text, parameters = parse_report_text(raw_text)

    # ---------------- 🔥 IMPROVED PROMPT ---------------- #
    prompt = f"""
You are a professional medical assistant.

Analyze the following medical report carefully.

Provide:

1. Short summary (2–3 lines)
2. Important abnormal findings
3. Explanation of each abnormal value (what it means)
4. Possible causes (simple terms)
5. What the patient should do next

Use clear and patient-friendly language.

Respond in {language}.

Report:
{cleaned_text}
"""

    explanation = call_llm(prompt)

    # ---------------- 🔥 BETTER SUMMARY ---------------- #
    try:
        summary = explanation.split("\n")[0][:200].strip()
    except Exception:
        summary = explanation[:200]

    if not summary:
        summary = "Summary could not be generated."

    # ---------------- DISCLAIMER ---------------- #
    if language.lower().startswith("en"):
        disclaimer = (
            "This report explanation is for educational purposes only. "
            "It does not constitute medical advice. Always consult a licensed doctor."
        )
    else:
        disclaimer = (
            "এই ব্যাখ্যাটি শুধুমাত্র শিক্ষামূলক উদ্দেশ্যে। চিকিৎসা সংক্রান্ত সিদ্ধান্তের জন্য "
            "সর্বদা যোগ্য ডাক্তারের পরামর্শ নিন।"
        )

    return cleaned_text, summary, parameters, explanation, disclaimer


def answer_report_question(
    report_text: str,
    question: str,
    language: str = "English"
) -> str:

    prompt = f"""
You are a medical assistant.

Answer the following question based on the report.

Be accurate, simple, and safe.

Language: {language}

Report:
{report_text}

Question:
{question}
"""

    return call_llm(prompt)