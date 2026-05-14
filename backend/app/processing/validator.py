"""
Input validation for uploaded images.

Each error includes a specific, actionable suggestion (not a generic message).
Validation failures raise ValidationError with .message and .suggestion fields,
which the API layer converts into HTTP responses.
"""

from __future__ import annotations

import io
from pathlib import Path
from typing import Tuple

from PIL import Image, UnidentifiedImageError

from app.config import (
    ALLOWED_EXTENSIONS,
    ALLOWED_FORMATS,
    MAX_UPLOAD_BYTES,
    MIN_INPUT_SHORT_EDGE,
)


class ValidationError(Exception):
    """Raised when an uploaded image fails validation."""

    def __init__(self, message: str, suggestion: str = ""):
        super().__init__(message)
        self.message = message
        self.suggestion = suggestion


def validate_filename(filename: str) -> None:
    """Reject files with unsupported extensions before we even read them."""
    if not filename:
        raise ValidationError(
            "No filename provided.",
            "Make sure the file is properly attached to the upload.",
        )

    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise ValidationError(
            f"Unsupported file extension: {ext or '(none)'}",
            f"Use JPG, PNG, or WEBP. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}",
        )


def validate_size(image_bytes: bytes) -> None:
    """Reject uploads above the byte cap."""
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        size_mb = len(image_bytes) / (1024 * 1024)
        max_mb = MAX_UPLOAD_BYTES / (1024 * 1024)
        raise ValidationError(
            f"File too large: {size_mb:.1f} MB",
            f"Maximum upload size is {max_mb:.0f} MB. "
            "Try compressing the image or reducing its resolution.",
        )


def validate_and_open(image_bytes: bytes) -> Tuple[Image.Image, Tuple[int, int]]:
    """
    Open the image with PIL and verify it's a real, supported, large-enough image.

    Returns (PIL Image in RGB mode, original (width, height)).

    Failure modes covered:
      - corrupt / not actually an image file
      - format not in our supported list
      - shortest side below the minimum

    We DO NOT enforce a maximum here; oversized images are resized in
    preprocess.py rather than rejected, per the spec.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        # PIL is lazy; force it to actually decode and verify.
        img.load()
    except (UnidentifiedImageError, OSError) as e:
        raise ValidationError(
            "Could not read the image file.",
            "The file may be corrupt or not actually an image. "
            "Try re-exporting as JPG or PNG from your image editor.",
        ) from e

    if img.format not in ALLOWED_FORMATS:
        raise ValidationError(
            f"Unsupported image format: {img.format}",
            f"Use JPG, PNG, or WEBP. Detected: {img.format}.",
        )

    width, height = img.size
    short_edge = min(width, height)
    if short_edge < MIN_INPUT_SHORT_EDGE:
        raise ValidationError(
            f"Image too small ({short_edge}px on the shortest side).",
            f"Upload an image at least {MIN_INPUT_SHORT_EDGE}px on its shortest side "
            "for usable weaving detail.",
        )

    # Always convert to RGB so the rest of the pipeline never has to worry
    # about RGBA, P (palette), L (grayscale), or CMYK inputs.
    if img.mode != "RGB":
        img = img.convert("RGB")

    return img, (width, height)
