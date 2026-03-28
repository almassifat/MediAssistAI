"""
Medical-grade OCR service for MediAssist AI.

Features:
- Google Vision OCR as primary engine
- Tesseract OCR as fallback
- Supports images and PDFs
- Light preprocessing for medical reports
"""

from __future__ import annotations

import io
import logging
import os
from pathlib import Path

from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageOps

logger = logging.getLogger(__name__)

# ---------------- GOOGLE OCR ---------------- #
GOOGLE_OCR_AVAILABLE = False
vision = None
vision_client = None

try:
    from google.cloud import vision_v1 as vision  # type: ignore

    # Optional debug:
    # logger.info("GOOGLE_APPLICATION_CREDENTIALS=%s", os.getenv("GOOGLE_APPLICATION_CREDENTIALS"))

    vision_client = vision.ImageAnnotatorClient()
    GOOGLE_OCR_AVAILABLE = True
    logger.info("Google Vision OCR initialized successfully.")
except Exception as e:
    logger.warning("Google OCR init failed: %s", e)
    GOOGLE_OCR_AVAILABLE = False

# ---------------- TESSERACT OCR ---------------- #
TESSERACT_AVAILABLE = False
pytesseract = None

try:
    import pytesseract  # type: ignore

    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    _ = pytesseract.get_tesseract_version()
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR initialized successfully.")
except Exception as e:
    logger.warning("Tesseract init failed: %s", e)
    TESSERACT_AVAILABLE = False

SUPPORTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg"}


# ---------------- PREPROCESSING ---------------- #
def preprocess_image(img: Image.Image) -> Image.Image:
    """
    Preprocess image for OCR while preserving medical report structure.
    """
    processed = img.convert("L")
    processed = ImageOps.autocontrast(processed)
    processed = processed.filter(ImageFilter.SHARPEN)
    return processed


# ---------------- CLEANING ---------------- #
def clean_text(text: str) -> str:
    """
    Clean OCR output while preserving line structure.
    """
    lines = text.splitlines()
    cleaned_lines: list[str] = []

    for line in lines:
        normalized = " ".join(line.strip().split())
        if len(normalized) < 2:
            continue
        cleaned_lines.append(normalized)

    return "\n".join(cleaned_lines)


# ---------------- GOOGLE OCR ---------------- #
def extract_text_google(img: Image.Image) -> str:
    """
    Extract text using Google Vision OCR.
    Uses document_text_detection for better structured/report OCR.
    """
    if not GOOGLE_OCR_AVAILABLE or vision is None or vision_client is None:
        raise RuntimeError("Google OCR is not available.")

    img_bytes = io.BytesIO()

    # Save as RGB PNG for best compatibility
    rgb_img = img.convert("RGB")
    rgb_img.save(img_bytes, format="PNG")
    content = img_bytes.getvalue()

    image = vision.Image(content=content)
    response = vision_client.document_text_detection(image=image)

    if response.error.message:
        raise RuntimeError(f"Google Vision API error: {response.error.message}")

    if response.full_text_annotation and response.full_text_annotation.text:
        return clean_text(response.full_text_annotation.text)

    if response.text_annotations:
        return clean_text(response.text_annotations[0].description)

    return ""


# ---------------- TESSERACT OCR ---------------- #
def extract_text_tesseract(img: Image.Image) -> str:
    """
    Extract text using Tesseract OCR.
    """
    if not TESSERACT_AVAILABLE or pytesseract is None:
        raise RuntimeError("Tesseract OCR is not available.")

    text = pytesseract.image_to_string(
        img,
        config="--oem 3 --psm 6",
    )
    return clean_text(text)


# ---------------- OCR DISPATCH ---------------- #
def extract_text_from_pil_image(img: Image.Image) -> str:
    """
    OCR a PIL image using Google first, then Tesseract fallback.
    """
    processed = preprocess_image(img)

    if GOOGLE_OCR_AVAILABLE:
        try:
            text = extract_text_google(processed)
            if text.strip():
                return text
            logger.warning("Google OCR returned empty text. Falling back to Tesseract.")
        except Exception as e:
            logger.warning("Google OCR failed. Falling back to Tesseract. Error: %s", e)

    if TESSERACT_AVAILABLE:
        return extract_text_tesseract(processed)

    return "[OCR unavailable] Neither Google OCR nor Tesseract is available."


# ---------------- IMAGE OCR ---------------- #
def extract_text_from_image(path: Path) -> str:
    logger.info("Running OCR on image: %s", path)

    try:
        with Image.open(path) as img:
            return extract_text_from_pil_image(img)
    except Exception as e:
        logger.error("Image OCR failed: %s", e, exc_info=True)
        return f"[OCR error] {e}"


# ---------------- PDF OCR ---------------- #
def extract_text_from_pdf(path: Path) -> str:
    logger.info("Running OCR on PDF: %s", path)

    try:
        pages = convert_from_path(str(path), dpi=300)
    except Exception as e:
        logger.error("PDF conversion failed: %s", e, exc_info=True)
        return f"[PDF conversion error] {e}"

    page_texts: list[str] = []

    for i, page in enumerate(pages, start=1):
        try:
            text = extract_text_from_pil_image(page)
            if text.strip():
                page_texts.append(text)
            else:
                logger.warning("OCR returned empty text for PDF page %d.", i)
        except Exception as e:
            logger.error("OCR failed on PDF page %d: %s", i, e, exc_info=True)

    if not page_texts:
        return "[OCR error] No text could be extracted from the PDF."

    return "\n\n".join(page_texts)


# ---------------- MAIN ROUTER ---------------- #
def extract_text_from_file(path: Path) -> str:
    """
    Route OCR request based on file extension.
    """
    suffix = path.suffix.lower().lstrip(".")

    if suffix in SUPPORTED_IMAGE_EXTENSIONS:
        return extract_text_from_image(path)

    if suffix == "pdf":
        return extract_text_from_pdf(path)

    return f"[Unsupported file type] .{suffix}"