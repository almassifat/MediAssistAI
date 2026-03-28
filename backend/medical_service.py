"""
Orchestration layer for MediAssist AI.

Improved version with:
- safer prompting
- structured parameter-first reasoning
- better summaries
- safer fallback when parsing fails
"""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import List, Tuple

from fastapi import UploadFile

from .config import settings
from .llm_service import call_llm
from .models import DetectedParameter
from .ocr_service import extract_text_from_file
from .parser_service import parse_report_text

logger = logging.getLogger(__name__)


def _save_upload_file(upload_file: UploadFile, destination_dir: Path) -> Path:
    """
    Safely save uploaded file.
    """
    filename = upload_file.filename or f"upload_{uuid.uuid4().hex}.dat"
    filename = Path(filename).name
    dest_path = destination_dir / filename

    with dest_path.open("wb") as buffer:
        buffer.write(upload_file.file.read())

    return dest_path


def _build_parameter_block(parameters: List[DetectedParameter]) -> str:
    """
    Convert detected parameters into a structured prompt block.
    """
    if not parameters:
        return "No structured medical parameters could be reliably extracted."

    lines = []
    for param in parameters:
        lines.append(
            f"- {param.name}: {param.value} "
            f"(Reference: {param.reference_range}, Status: {param.status})"
        )
    return "\n".join(lines)


def _build_summary(parameters: List[DetectedParameter], language: str) -> str:
    """
    Build a concise deterministic summary from parsed parameters.
    """
    abnormal = [p for p in parameters if p.status in {"low", "high"}]

    if language.lower().startswith("en"):
        if not parameters:
            return (
                "OCR text was extracted, but structured lab values could not be "
                "reliably identified from this report."
            )

        if not abnormal:
            return "No abnormal values were confidently detected in the parsed report."

        items = ", ".join(f"{p.name} is {p.status}" for p in abnormal[:3])
        return f"Detected abnormal findings: {items}."

    if not parameters:
        return (
            "রিপোর্ট থেকে OCR টেক্সট পাওয়া গেছে, তবে নির্ভরযোগ্যভাবে "
            "স্ট্রাকচার্ড মেডিকেল মান শনাক্ত করা যায়নি।"
        )

    if not abnormal:
        return "পার্স করা রিপোর্টে নিশ্চিতভাবে কোনো অস্বাভাবিক মান শনাক্ত হয়নি।"

    items = ", ".join(f"{p.name} {p.status}" for p in abnormal[:3])
    return f"অস্বাভাবিক ফলাফল শনাক্ত হয়েছে: {items}."


def _build_analysis_prompt(
    cleaned_text: str,
    parameters: List[DetectedParameter],
    language: str,
) -> str:
    """
    Build a safer, parameter-aware prompt.
    """
    parameter_block = _build_parameter_block(parameters)

    if parameters:
        reliability_note = (
            "Use the structured extracted parameters as the primary source of truth. "
            "Use OCR text only as supporting context. "
            "Do not invent values that are not listed in structured parameters."
        )
    else:
        reliability_note = (
            "Structured parameter extraction failed or returned no confident values. "
            "Do not claim exact lab values unless they are clearly supported by the OCR text. "
            "Be cautious and explicitly mention uncertainty."
        )

    return f"""
You are a careful medical report explanation assistant.

Your job is to explain a lab report in a patient-friendly and safe way.

Rules:
1. Never invent values.
2. Prefer structured extracted parameters over OCR text.
3. If structured extraction failed, clearly state uncertainty.
4. Do not give a final diagnosis.
5. Keep language simple and understandable.
6. Respond in {language}.

{reliability_note}

Structured extracted parameters:
{parameter_block}

OCR text:
{cleaned_text}

Please provide:
1. Short summary
2. Important abnormal findings
3. Explanation of each abnormal value
4. Possible common causes in simple terms
5. What the patient should do next
""".strip()


def _build_qa_prompt(report_text: str, question: str, language: str) -> str:
    """
    Build a safer prompt for follow-up Q&A.
    """
    return f"""
You are a careful medical assistant.

Answer the user's question using only the report content provided below.
Do not invent values.
If the answer is uncertain, say so clearly.
Do not provide a final diagnosis.
Use simple and safe language.
Respond in {language}.

Report:
{report_text}

Question:
{question}
""".strip()


def analyze_report(
    upload_file: UploadFile,
    language: str = "English",
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
            logger.debug("Could not delete temp file: %s", temp_path)

    cleaned_text, parameters = parse_report_text(raw_text)

    summary = _build_summary(parameters, language)
    prompt = _build_analysis_prompt(cleaned_text, parameters, language)
    explanation = call_llm(prompt)

    if not explanation or not explanation.strip():
        if language.lower().startswith("en"):
            explanation = (
                "The report was processed, but a detailed explanation could not be generated."
            )
        else:
            explanation = (
                "রিপোর্ট প্রক্রিয়াকরণ হয়েছে, কিন্তু বিস্তারিত ব্যাখ্যা তৈরি করা যায়নি।"
            )

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
    language: str = "English",
) -> str:
    prompt = _build_qa_prompt(report_text, question, language)
    answer = call_llm(prompt)

    if not answer or not answer.strip():
        if language.lower().startswith("en"):
            return "A reliable answer could not be generated from the report."
        return "রিপোর্ট থেকে নির্ভরযোগ্য উত্তর তৈরি করা যায়নি।"

    return answer