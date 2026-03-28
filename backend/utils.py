"""
Utility functions for MediAssist AI backend.

This module defines small helper functions used across the backend.
Currently only safe filename generation is provided, but additional
utility functions can be added here without cluttering service modules.
"""

from __future__ import annotations

import re
import uuid
from pathlib import Path


def secure_filename(filename: str) -> str:
    """Sanitise an arbitrary filename into a safe representation.

    All characters other than letters, numbers, dots and underscores
    are removed.  Leading dots are stripped to avoid hidden files.
    If the filename becomes empty, a random UUID is used instead.  The
    original extension is preserved.
    """
    name, ext = (filename.rsplit(".", 1) + [""])[:2]
    name = re.sub(r"[^A-Za-z0-9_.-]", "", name)
    name = name.lstrip(".")  # avoid hidden file names
    if not name:
        name = uuid.uuid4().hex
    return f"{name}.{ext}" if ext else name


def is_allowed_extension(path: Path, allowed_extensions: set[str]) -> bool:
    """Check whether a file path has an allowed extension."""
    return path.suffix.lstrip(".").lower() in allowed_extensions
