"""
OCR service for MediAssist AI.

This module implements a simple OCR pipeline for both images and
PDFs.  It relies on ``pytesseract`` for optical character recognition
when Tesseract is available.  If Tesseract is not installed or
initialisation fails, the service falls back to a stub that returns
a clear error message.  PDF files are converted to images using
``pdf2image``.

The OCR functions return plain text with minimal normalisation.  In
production you may wish to apply more sophisticated post‑processing to
correct common OCR errors and join broken lines.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List

from PIL import Image
from pdf2image import convert_from_path

try:
    import pytesseract  # type: ignore[import]
    TESSERACT_AVAILABLE = True
except Exception:
    TESSERACT_AVAILABLE = False

logger = logging.getLogger(__name__)


def extract_text_from_image(path: Path) -> str:
    """Extract text from a single image file using OCR.

    Parameters
    ----------
    path: Path
        Path to the image file to process.

    Returns
    -------
    str
        The extracted text, or a message explaining why OCR failed.
    """
    logger.info("Performing OCR on image: %s", path)
    if not TESSERACT_AVAILABLE:
        # Inform the caller that OCR cannot be performed in this environment.
        return (
            "[OCR unavailable] Tesseract is not installed in this environment, "
            "so the image could not be processed."
        )
    try:
        with Image.open(path) as img:
            # Convert image to RGB just in case.  Tesseract handles
            # different modes but RGB is a safe default.
            img = img.convert("RGB")
            text = pytesseract.image_to_string(img)
            return text
    except Exception as e:
        logger.error("Error during image OCR: %s", e, exc_info=True)
        return f"[OCR error] {e}"


def extract_text_from_pdf(path: Path) -> str:
    """Extract text from a PDF by converting each page to an image.

    Parameters
    ----------
    path: Path
        Path to the PDF file to process.

    Returns
    -------
    str
        The concatenated text from all pages, or an error message.
    """
    logger.info("Performing OCR on PDF: %s", path)
    try:
        pages = convert_from_path(str(path))
    except Exception as e:
        logger.error("Could not convert PDF to images: %s", e, exc_info=True)
        return f"[PDF conversion error] {e}"
    texts: List[str] = []
    for idx, page in enumerate(pages):
        tmp_path = path.with_suffix(f"_{idx}.png")
        try:
            page.save(tmp_path, format="PNG")
            page_text = extract_text_from_image(tmp_path)
            texts.append(page_text)
        finally:
            # Clean up the temporary image file.
            try:
                tmp_path.unlink()
            except Exception:
                pass
    return "\n".join(texts)


def extract_text_from_file(path: Path) -> str:
    """Determine the file type and extract text accordingly.

    This helper function inspects the file suffix and dispatches to
    either ``extract_text_from_image`` or ``extract_text_from_pdf``.  If
    the extension is not recognised it returns an explanatory message.
    """
    suffix = path.suffix.lower().lstrip(".")
    if suffix in {"png", "jpg", "jpeg"}:
        return extract_text_from_image(path)
    if suffix == "pdf":
        return extract_text_from_pdf(path)
    return f"[Unsupported file type] Cannot extract text from .{suffix} files."
