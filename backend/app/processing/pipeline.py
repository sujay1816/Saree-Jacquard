"""
Top-level orchestrator: image bytes + settings -> zip bytes.

Keeps the API endpoint thin and makes the pipeline easy to test in isolation.
"""

from __future__ import annotations

import io
import json
import zipfile
from dataclasses import dataclass
from typing import List, Tuple

from app.config import DEFAULT_SHUTTLE_NAMES
from app.processing.bmp_writer import (
    write_color_preview_png_bytes,
    write_shuttle_bmp_bytes,
    write_shuttle_thumbnail_png_bytes,
)
from app.processing.cleanup import enforce_minimum_motif_size, remove_speckle
from app.processing.preprocess import (
    apply_bilateral_filter,
    auto_resize_for_processing,
    pil_to_rgb_array,
    rgb_to_lab_pixels,
)
from app.processing.quantize import build_palette_metadata, quantize_image
from app.processing.resize import resize_labels_to_grid
from app.processing.validator import validate_and_open


@dataclass
class PipelineResult:
    """Returned to the API layer. The zip is the user-facing artifact."""

    zip_bytes: bytes
    palette_entries: list  # list of dict (see schemas.PaletteEntry)
    background_info: dict
    output_size: Tuple[int, int]   # (pins, cards)
    original_size: Tuple[int, int]  # (width, height)


def run_pipeline(
    image_bytes: bytes,
    pins: int,
    cards: int,
    num_shuttles: int,
    motif_cleanup: bool = False,
    motif_min_size: int = 2,
    shuttle_filenames: list | None = None,
) -> PipelineResult:
    """
    Run the full saree -> jacquard BMPs pipeline.

    Args:
        image_bytes: raw bytes of the uploaded JPG/PNG/WEBP.
        pins: output BMP width.
        cards: output BMP height.
        num_shuttles: number of thread shuttles to produce (2-8).
        motif_cleanup: if True, enforce minimum motif size.
        motif_min_size: minimum motif size in pixels when cleanup is on.
        shuttle_filenames: optional list of N filenames (no extension) to
            override the defaults. If None or shorter than N, defaults are
            used to fill in.

    Returns:
        PipelineResult containing the zip bytes and metadata.

    Raises:
        ValidationError: if the input image fails validation.
        Any underlying numpy/sklearn exceptions are allowed to propagate;
        the API layer wraps them in a generic 500 response.
    """
    # ---- 1. Validate and open ----
    pil_img, original_size = validate_and_open(image_bytes)

    # ---- 2. Pre-process ----
    working_img = auto_resize_for_processing(pil_img, pins, cards)
    rgb_array, image_shape = pil_to_rgb_array(working_img)
    smoothed = apply_bilateral_filter(rgb_array)
    lab_pixels = rgb_to_lab_pixels(smoothed)

    # ---- 3. Quantize ----
    qr = quantize_image(lab_pixels, image_shape, num_shuttles)

    # ---- 4. Cleanup ----
    labels = remove_speckle(qr.labels)
    if motif_cleanup and motif_min_size > 1:
        labels = enforce_minimum_motif_size(labels, motif_min_size)

    # ---- 5. Resize to loom grid ----
    final_labels = resize_labels_to_grid(labels, pins, cards)

    # ---- 6. Build palette metadata ----
    palette_entries, background_info = build_palette_metadata(
        qr, DEFAULT_SHUTTLE_NAMES
    )

    # Apply user-provided filename overrides if any
    if shuttle_filenames:
        for i, override in enumerate(shuttle_filenames):
            if i >= len(palette_entries):
                break
            cleaned = _sanitize_filename(override)
            if cleaned:
                palette_entries[i]["name"] = cleaned

    # ---- 7. Build zip ----
    zip_bytes = _build_zip(final_labels, qr.palette_rgb, palette_entries, background_info)

    return PipelineResult(
        zip_bytes=zip_bytes,
        palette_entries=palette_entries,
        background_info=background_info,
        output_size=(pins, cards),
        original_size=original_size,
    )


def _build_zip(
    final_labels,
    palette_rgb,
    palette_entries: List[dict],
    background_info: dict,
) -> bytes:
    """Pack the BMPs, preview PNG, and palette.json into a single zip."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # Shuttle BMPs
        for entry in palette_entries:
            shuttle_num = entry["shuttle_number"]
            filename = f"{entry['name']}.bmp"
            bmp_bytes = write_shuttle_bmp_bytes(final_labels, shuttle_num)
            zf.writestr(filename, bmp_bytes)

        # Color preview
        preview_bytes = write_color_preview_png_bytes(final_labels, palette_rgb)
        zf.writestr("preview.png", preview_bytes)

        # palette.json
        palette_doc = {
            "background": background_info,
            "shuttles": palette_entries,
        }
        zf.writestr("palette.json", json.dumps(palette_doc, indent=2))

    return buf.getvalue()


def _sanitize_filename(name: str) -> str:
    """
    Clean a user-supplied filename: lowercase, replace whitespace with _,
    strip path separators and quotes. Returns empty string if the result
    would be empty (caller should keep the default in that case).
    """
    if not name:
        return ""
    bad_chars = {"/", "\\", '"', "'", ":", "*", "?", "<", ">", "|"}
    cleaned = "".join("_" if c.isspace() else c for c in name)
    cleaned = "".join(c for c in cleaned if c not in bad_chars)
    cleaned = cleaned.strip("._").lower()
    return cleaned[:64]  # cap length to keep zip entries reasonable
