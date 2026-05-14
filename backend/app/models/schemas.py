"""
Pydantic models for API request/response payloads.

The convert endpoint takes the image as a multipart upload (handled by FastAPI's
UploadFile) and the other parameters as form fields. We use these schemas mostly
to document and validate the conversion settings.
"""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field

from app.config import (
    MAX_CARDS,
    MAX_PINS,
    MAX_SHUTTLES,
    MIN_CARDS,
    MIN_PINS,
    MIN_SHUTTLES,
)


class ConversionSettings(BaseModel):
    """
    Settings the user submits with their image for a single conversion job.

    Note: the actual API uses Form() parameters for multipart compatibility;
    this model documents what each field means and is used in tests.
    """

    pins: int = Field(..., ge=MIN_PINS, le=MAX_PINS, description="Output BMP width")
    cards: int = Field(..., ge=MIN_CARDS, le=MAX_CARDS, description="Output BMP height")
    shuttles: int = Field(
        ..., ge=MIN_SHUTTLES, le=MAX_SHUTTLES, description="Number of thread shuttles"
    )


class PaletteEntry(BaseModel):
    """One shuttle in the discovered palette."""

    shuttle_number: int = Field(..., description="1-based shuttle index")
    name: str = Field(..., description="Default filename without extension")
    rgb: Tuple[int, int, int] = Field(..., description="RGB color (0-255)")
    hex: str = Field(..., description="Hex color string, e.g. #aabbcc")
    pixel_count: int = Field(..., description="Number of pixels assigned to this shuttle")
    pixel_fraction: float = Field(
        ..., description="Fraction of total image pixels (0-1)"
    )


class BackgroundInfo(BaseModel):
    """The auto-detected background color (not exported as a BMP)."""

    rgb: Tuple[int, int, int]
    hex: str
    pixel_count: int
    pixel_fraction: float


class ConversionResponse(BaseModel):
    """
    Metadata returned alongside the downloadable zip.

    The actual binary zip is returned as the response body via StreamingResponse;
    this model is used internally to build the palette.json file included in
    the zip, and is documented for any future JSON-only endpoint.
    """

    palette: List[PaletteEntry]
    background: BackgroundInfo
    output_size: Tuple[int, int] = Field(..., description="(pins, cards)")
    original_size: Tuple[int, int]


class ErrorResponse(BaseModel):
    """Standard error payload."""

    error: str
    suggestion: Optional[str] = None
