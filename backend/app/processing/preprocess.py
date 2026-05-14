"""
Pre-processing steps that run before color quantization.

Order matters:
  1. Resize down if the input is much larger than the target output
     (saves significant compute on k-means with no quality loss).
  2. Bilateral filter (smooths gradients, preserves motif edges).
  3. Convert to LAB color space for perceptually accurate clustering.
"""

from __future__ import annotations

from typing import Tuple

import cv2
import numpy as np
from PIL import Image

from app.config import (
    BILATERAL_D,
    BILATERAL_SIGMA_COLOR,
    BILATERAL_SIGMA_SPACE,
    MAX_INPUT_LONG_EDGE,
)


def auto_resize_for_processing(
    img: Image.Image, target_pins: int, target_cards: int
) -> Image.Image:
    """
    Cap the working resolution before quantization.

    We resize the image down to roughly 2x the target output dimensions
    (or MAX_INPUT_LONG_EDGE, whichever is smaller). Reason: we will
    nearest-neighbor resize to exactly pins x cards at the END of the
    pipeline. Running k-means on a 12000px image when the final output
    is 2400px is pure waste.

    Aspect ratio is preserved here - this is just a compute cap. The
    final stretch-to-fit happens after quantization.
    """
    w, h = img.size
    long_edge = max(w, h)

    # Cap 1: never process larger than MAX_INPUT_LONG_EDGE
    target_long = min(long_edge, MAX_INPUT_LONG_EDGE)

    # Cap 2: don't bother processing much larger than 2x the output
    output_long = max(target_pins, target_cards)
    target_long = min(target_long, output_long * 2)

    # Don't upscale - if image is already smaller, leave it alone
    if target_long >= long_edge:
        return img

    scale = target_long / long_edge
    new_w = max(1, int(round(w * scale)))
    new_h = max(1, int(round(h * scale)))
    return img.resize((new_w, new_h), Image.LANCZOS)


def apply_bilateral_filter(rgb: np.ndarray) -> np.ndarray:
    """
    Smooth gradients while keeping motif edges crisp.

    Bilateral filter is slower than Gaussian but it's the right tool here:
    it averages within color similarity windows, so smooth areas (sky-like
    gradients in a saree photo) get smoothed but hard edges between
    motif and background are preserved.

    Input/output: HxWx3 uint8 RGB array.
    """
    # OpenCV uses BGR internally for color ops but bilateralFilter is
    # channel-order-agnostic since it works on numerical similarity, so
    # we can pass RGB directly.
    return cv2.bilateralFilter(
        rgb,
        d=BILATERAL_D,
        sigmaColor=BILATERAL_SIGMA_COLOR,
        sigmaSpace=BILATERAL_SIGMA_SPACE,
    )


def rgb_to_lab_pixels(rgb: np.ndarray) -> np.ndarray:
    """
    Convert an HxWx3 RGB uint8 array to a flat Nx3 LAB float32 array
    suitable for k-means.

    LAB (CIE L*a*b*) is approximately perceptually uniform: equal
    Euclidean distances in LAB correspond to equal perceived color
    differences. Critical for sarees where similar reds (slightly
    different in RGB) should cluster together.
    """
    lab = cv2.cvtColor(rgb, cv2.COLOR_RGB2LAB)
    return lab.reshape(-1, 3).astype(np.float32)


def lab_to_rgb_palette(lab_centers: np.ndarray) -> np.ndarray:
    """
    Convert Nx3 LAB cluster centers back to Nx3 uint8 RGB.

    We round-trip through a 1xNx3 image because cv2.cvtColor operates
    on 2D image arrays, not flat pixel lists.
    """
    lab_img = lab_centers.reshape(1, -1, 3).astype(np.uint8)
    rgb_img = cv2.cvtColor(lab_img, cv2.COLOR_LAB2RGB)
    return rgb_img.reshape(-1, 3)


def pil_to_rgb_array(img: Image.Image) -> Tuple[np.ndarray, Tuple[int, int]]:
    """PIL Image -> HxWx3 uint8 numpy array + (height, width)."""
    arr = np.asarray(img, dtype=np.uint8)
    if arr.ndim != 3 or arr.shape[2] != 3:
        raise ValueError(f"Expected RGB image, got shape {arr.shape}")
    return arr, (arr.shape[0], arr.shape[1])
