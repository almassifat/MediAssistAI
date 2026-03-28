"""
Parser service for MediAssist AI.

Improved version with filtering, better OCR cleanup,
and more reliable parameter detection.
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from .models import DetectedParameter

logger = logging.getLogger(__name__)


# 🔥 Only allow known medical parameters (very important)
VALID_TESTS = {
    "hemoglobin",
    "rbc",
    "wbc",
    "platelet",
    "neutrophils",
    "lymphocytes",
    "monocytes",
    "eosinophils",
    "basophils",
    "hematocrit",
    "mcv",
    "mch",
    "mchc",
}


# Improved regex (slightly stricter)
LINE_PATTERN = re.compile(
    r"^(?P<name>[A-Za-z][A-Za-z \-/]*)\s+"
    r"(?P<value>[0-9]+(?:\.[0-9]+)?)\s*"
    r"(?:\S+)?\s+"
    r"(?P<low>[0-9]+(?:\.[0-9]+)?)\s*[-–]\s*"
    r"(?P<high>[0-9]+(?:\.[0-9]+)?)",
    re.MULTILINE,
)


def _clean_text(text: str) -> str:
    """Improve OCR text quality"""
    text = text.replace("\n", " ")
    text = re.sub(r"[\u00a0\t]+", " ", text)
    text = re.sub(r"\r\n?", "\n", text)
    text = re.sub(r" {2,}", " ", text)
    return text.strip()


def parse_report_text(text: str) -> Tuple[str, List[DetectedParameter]]:
    """Parse OCR text and extract valid medical parameters"""

    cleaned = _clean_text(text)

    parameters: List[DetectedParameter] = []

    for match in LINE_PATTERN.finditer(cleaned):
        name = match.group("name").strip().lower()

        # 🔥 FILTER OUT GARBAGE (MOST IMPORTANT FIX)
        if name not in VALID_TESTS:
            logger.debug("Skipping unknown parameter: %s", name)
            continue

        value_str = match.group("value")
        low_str = match.group("low")
        high_str = match.group("high")

        try:
            value = float(value_str)
            low = float(low_str)
            high = float(high_str)
        except ValueError:
            logger.debug("Skipping non-numeric line: %s", match.group(0))
            continue

        # 🔥 EXTRA SAFETY (avoid OCR nonsense)
        if high < low or value > 1000:
            logger.debug("Skipping invalid range/value: %s", match.group(0))
            continue

        # Determine status
        if value < low:
            status = "low"
        elif value > high:
            status = "high"
        else:
            status = "normal"

        param = DetectedParameter(
            name=name.capitalize(),
            value=value_str,
            reference_range=f"{low_str} - {high_str}",
            status=status,
        )

        parameters.append(param)

        logger.debug(
            "Detected parameter: %s = %s (%s-%s) → %s",
            name,
            value_str,
            low_str,
            high_str,
            status,
        )

    return cleaned, parameters