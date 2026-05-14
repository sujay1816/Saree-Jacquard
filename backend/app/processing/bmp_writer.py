"""
BMP file generation.

Two output types:

  1. Shuttle masks (write_shuttle_bmp): 24-bit RGB BMPs where the pixels
     of one shuttle's color are written as BLACK (0,0,0) and everything else
     as WHITE (255,255,255). This matches the user-supplied sample format
     exactly (verified against 720_brokt_jari.bmp etc.).

  2. Color preview (write_color_preview_png): a full-color quantized preview
     PNG showing every shuttle in its actual RGB color. Not for the loom -
     just for the designer to confirm the conversion looks right.

We use Pillow for writing because OpenCV's BMP writer has some compatibility
quirks with older jacquard software (different header byte ordering in edge
cases). Pillow's BMP output is the most conventional.
"""

from __future__ import annotations

import io

import numpy as np
from PIL import Image


def make_shuttle_mask_rgb(labels: np.ndarray, shuttle_index: int) -> np.ndarray:
    """
    Build the HxWx3 uint8 RGB array for one shuttle's mask BMP.

    Pixels where labels == shuttle_index -> BLACK (thread active)
    All other pixels -> WHITE (thread inactive)

    Matches the convention in the user-provided sample BMPs.
    """
    mask_2d = labels == shuttle_index  # HxW bool
    # Start with all white
    out = np.full((labels.shape[0], labels.shape[1], 3), 255, dtype=np.uint8)
    # Black where the shuttle is active
    out[mask_2d] = [0, 0, 0]
    return out


def write_shuttle_bmp_bytes(labels: np.ndarray, shuttle_index: int) -> bytes:
    """
    Generate the shuttle BMP file content as bytes (24-bit RGB BMP).

    Pillow's default BMP writer produces 24-bit RGB BMP with the
    BITMAPINFOHEADER format expected by virtually all jacquard software.
    Verified to match the structure of the user-provided sample files.
    """
    rgb = make_shuttle_mask_rgb(labels, shuttle_index)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    # Explicit BMP format. Pillow infers depth from mode='RGB' -> 24 bits.
    img.save(buf, format="BMP")
    return buf.getvalue()


def write_color_preview_png_bytes(
    labels: np.ndarray, palette_rgb: np.ndarray
) -> bytes:
    """
    Build the full-color preview PNG by painting each label with its palette color.

    `palette_rgb` is a (K, 3) uint8 array. The labels array contains values
    in [0, K-1]; index 0 is background, 1..K-1 are shuttle colors.
    """
    # Vectorized lookup: result[i, j] = palette_rgb[labels[i, j]]
    rgb = palette_rgb[labels]  # produces HxWx3
    rgb = np.ascontiguousarray(rgb, dtype=np.uint8)
    img = Image.fromarray(rgb, mode="RGB")
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def write_shuttle_thumbnail_png_bytes(
    labels: np.ndarray, shuttle_index: int, max_size: int = 400
) -> bytes:
    """
    Small PNG thumbnail of a shuttle mask, used for the result panel preview
    in the frontend (NOT for the loom output). Aspect ratio preserved.

    Black-on-white at thumbnail resolution so the designer can see at a
    glance where each shuttle fires.
    """
    rgb = make_shuttle_mask_rgb(labels, shuttle_index)
    img = Image.fromarray(rgb, mode="RGB")
    img.thumbnail((max_size, max_size), Image.NEAREST)
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=True)
    return buf.getvalue()
