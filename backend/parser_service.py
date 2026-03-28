"""
Parser service for MediAssist AI.

Improved version:
- Preserves OCR line structure
- Supports aliases like Hb, HGB, WBC Count, Platelets
- More flexible regex for medical report rows
"""

from __future__ import annotations

import logging
import re
from typing import List, Tuple

from .models import DetectedParameter

logger = logging.getLogger(__name__)

# Canonical names + aliases
TEST_ALIASES = {
    "hemoglobin": "Hemoglobin",
    "haemoglobin": "Hemoglobin",
    "hb": "Hemoglobin",
    "hgb": "Hemoglobin",
    "rbc": "RBC",
    "rbc count": "RBC",
    "wbc": "WBC",
    "wbc count": "WBC",
    "total wbc count": "WBC",
    "platelet": "Platelet",
    "platelets": "Platelet",
    "platelet count": "Platelet",
    "neutrophils": "Neutrophils",
    "lymphocytes": "Lymphocytes",
    "monocytes": "Monocytes",
    "eosinophils": "Eosinophils",
    "basophils": "Basophils",
    "hematocrit": "Hematocrit",
    "haematocrit": "Hematocrit",
    "mcv": "MCV",
    "mch": "MCH",
    "mchc": "MCHC",
}

# Flexible line pattern:
# Name   Value   optional unit   Low-High
LINE_PATTERN = re.compile(
    r"(?P<name>[A-Za-z][A-Za-z .()/\-]*)\s+"
    r"(?P<value>\d+(?:\.\d+)?)\s*"
    r"(?:[A-Za-z%/.\d]+)?\s+"
    r"(?P<low>\d+(?:\.\d+)?)\s*[-–]\s*"
    r"(?P<high>\d+(?:\.\d+)?)",
    re.IGNORECASE,
)


def _clean_text(text: str) -> str:
    """
    Clean OCR text while preserving line structure.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[\u00a0\t]+", " ", text)

    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        line = " ".join(line.strip().split())
        if line:
            cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def _normalize_name(name: str) -> str | None:
    """
    Normalize OCR parameter names to canonical names.
    """
    name = name.strip().lower()
    name = re.sub(r"[().]", "", name)
    name = re.sub(r"\s+", " ", name)

    # direct hit
    if name in TEST_ALIASES:
        return TEST_ALIASES[name]

    # partial heuristics
    if "hemoglobin" in name or name in {"hb", "hgb"}:
        return "Hemoglobin"
    if "wbc" in name:
        return "WBC"
    if "rbc" in name:
        return "RBC"
    if "platelet" in name:
        return "Platelet"
    if "neutrophil" in name:
        return "Neutrophils"
    if "lymphocyte" in name:
        return "Lymphocytes"
    if "monocyte" in name:
        return "Monocytes"
    if "eosinophil" in name:
        return "Eosinophils"
    if "basophil" in name:
        return "Basophils"
    if "hematocrit" in name or "haematocrit" in name:
        return "Hematocrit"
    if "mcv" in name:
        return "MCV"
    if "mchc" in name:
        return "MCHC"
    if "mch" in name:
        return "MCH"

    return None


def parse_report_text(text: str) -> Tuple[str, List[DetectedParameter]]:
    """
    Parse OCR text and extract valid medical parameters.
    """
    cleaned = _clean_text(text)
    parameters: List[DetectedParameter] = []
    seen: set[tuple[str, str, str]] = set()

    for line in cleaned.split("\n"):
        match = LINE_PATTERN.search(line)
        if not match:
            continue

        raw_name = match.group("name").strip()
        normalized_name = _normalize_name(raw_name)

        if not normalized_name:
            logger.debug("Skipping unknown parameter: %s", raw_name)
            continue

        value_str = match.group("value")
        low_str = match.group("low")
        high_str = match.group("high")

        try:
            value = float(value_str)
            low = float(low_str)
            high = float(high_str)
        except ValueError:
            logger.debug("Skipping non-numeric line: %s", line)
            continue

        if high < low or value > 1000:
            logger.debug("Skipping invalid range/value: %s", line)
            continue

        if value < low:
            status = "low"
        elif value > high:
            status = "high"
        else:
            status = "normal"

        key = (normalized_name, value_str, f"{low_str}-{high_str}")
        if key in seen:
            continue
        seen.add(key)

        parameters.append(
            DetectedParameter(
                name=normalized_name,
                value=value_str,
                reference_range=f"{low_str} - {high_str}",
                status=status,
            )
        )

        logger.debug(
            "Detected parameter: %s = %s (%s-%s) -> %s",
            normalized_name,
            value_str,
            low_str,
            high_str,
            status,
        )

    return cleaned, parameters