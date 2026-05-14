"""
/convert endpoint: takes a multipart upload + form fields, returns a zip.

We deliberately keep this thin. All real work happens in
app.processing.pipeline. The endpoint:
  - validates the form fields
  - reads and size-checks the uploaded file
  - calls run_pipeline
  - streams the zip back to the client
"""

from __future__ import annotations

import json
import logging
from typing import List, Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import Response

from app.config import (
    MAX_CARDS,
    MAX_PINS,
    MAX_SHUTTLES,
    MIN_CARDS,
    MIN_PINS,
    MIN_SHUTTLES,
)
from app.processing.pipeline import run_pipeline
from app.processing.validator import (
    ValidationError,
    validate_filename,
    validate_size,
)

logger = logging.getLogger(__name__)

router = APIRouter()


def _validation_error(message: str, suggestion: str = "") -> HTTPException:
    """Build a 422 HTTPException with a structured error+suggestion body."""
    return HTTPException(
        status_code=422,
        detail={"error": message, "suggestion": suggestion},
    )


@router.post("/convert")
async def convert(
    image: UploadFile = File(..., description="Saree image (JPG/PNG/WEBP)"),
    pins: int = Form(..., description="Output BMP width"),
    cards: int = Form(..., description="Output BMP height"),
    shuttles: int = Form(..., description="Number of thread shuttles"),
    # JSON-encoded list of shuttle filename overrides, e.g. '["red_silk","gold"]'
    shuttle_filenames: Optional[str] = Form(None),
):
    """
    Convert a saree image to jacquard shuttle BMPs.

    Returns: application/zip containing N shuttle BMPs + preview.png + palette.json.

    Error handling: validation errors return 422 with {error, suggestion}.
    Internal errors return 500.
    """
    # ---- Form validation ----
    if not (MIN_PINS <= pins <= MAX_PINS):
        raise _validation_error(
            f"Pins must be between {MIN_PINS} and {MAX_PINS}. You entered {pins}.",
            f"Set pins to a value in the range {MIN_PINS}-{MAX_PINS}.",
        )
    if not (MIN_CARDS <= cards <= MAX_CARDS):
        raise _validation_error(
            f"Cards must be between {MIN_CARDS} and {MAX_CARDS}. You entered {cards}.",
            f"Set cards to a value in the range {MIN_CARDS}-{MAX_CARDS}.",
        )
    if not (MIN_SHUTTLES <= shuttles <= MAX_SHUTTLES):
        raise _validation_error(
            f"Shuttle count must be between {MIN_SHUTTLES} and {MAX_SHUTTLES}.",
            f"Pick a value in the range {MIN_SHUTTLES}-{MAX_SHUTTLES}.",
        )

    # ---- File handling ----
    try:
        validate_filename(image.filename or "")
    except ValidationError as e:
        raise _validation_error(e.message, e.suggestion)

    image_bytes = await image.read()

    try:
        validate_size(image_bytes)
    except ValidationError as e:
        raise _validation_error(e.message, e.suggestion)

    # ---- Parse optional filename overrides ----
    filename_overrides: List[str] = []
    if shuttle_filenames:
        try:
            parsed = json.loads(shuttle_filenames)
            if isinstance(parsed, list):
                filename_overrides = [str(x) for x in parsed]
        except json.JSONDecodeError:
            raise _validation_error(
                "shuttle_filenames must be a JSON array of strings.",
                'Example: ["red_silk", "gold_zari"]',
            )

    # ---- Run pipeline ----
    try:
        result = run_pipeline(
            image_bytes=image_bytes,
            pins=pins,
            cards=cards,
            num_shuttles=shuttles,
            shuttle_filenames=filename_overrides or None,
        )
    except ValidationError as e:
        raise _validation_error(e.message, e.suggestion)
    except MemoryError:
        raise _validation_error(
            "Out of memory while processing. The image or output dimensions "
            "are too large.",
            "Try smaller pins/cards, fewer shuttles, or a smaller source image.",
        )
    except Exception as e:
        logger.exception("Pipeline failed")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Conversion failed unexpectedly.",
                "suggestion": (
                    "Try saving the source image as a standard sRGB JPG and "
                    "uploading again. If the problem persists, the image may "
                    "have an unusual color profile."
                ),
            },
        )

    # ---- Build response ----
    # Send back the zip as the body and put palette metadata in a custom header
    # so the frontend can render the swatches without unzipping client-side.
    headers = {
        "Content-Disposition": 'attachment; filename="jacquard-output.zip"',
        "X-Palette-Metadata": json.dumps(
            {
                "background": result.background_info,
                "shuttles": result.palette_entries,
                "output_size": list(result.output_size),
                "original_size": list(result.original_size),
            }
        ),
        # CORS exposure so the frontend can read X-Palette-Metadata
        "Access-Control-Expose-Headers": "X-Palette-Metadata, Content-Disposition",
    }
    return Response(
        content=result.zip_bytes,
        media_type="application/zip",
        headers=headers,
    )
