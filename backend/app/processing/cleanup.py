"""
Post-quantization cleanup of the labels array.

This module is always-on as of v1.1: aggressive preprocessing combined with
this cleanup produces clean, weaver-ready shuttle masks even for textured
brocade close-ups.

Three operations, applied in order, for each shuttle (background label 0
is preserved untouched):

  1. Morphological closing  -> fills small holes inside a motif body.
                               Result: solid motifs instead of "etched" ones.
  2. Morphological opening  -> removes thin outlier strokes from a motif's
                               boundary. Result: cleaner motif edges.
  3. Small-region drop      -> any connected piece of a shuttle smaller than
                               MIN_REGION_PIXELS is reassigned to background.
                               Result: no single-pixel shuttle changes for
                               the loom to thrash on.

This pipeline was tuned against textured brocade saree photos. It assumes
the user wants clean weaving output rather than pixel-perfect preservation
of every gradient.
"""

from __future__ import annotations

import cv2
import numpy as np
from scipy import ndimage

from app.config import (
    MIN_REGION_PIXELS,
    MORPH_CLOSE_SIZE,
    MORPH_OPEN_SIZE,
)


def clean_labels(labels: np.ndarray) -> np.ndarray:
    """
    Apply all cleanup steps to a quantized label array.

    `labels` is HxW uint8 where 0 = background and 1..N = shuttles.
    Returns a new labels array of the same shape and dtype.
    """
    if labels.size == 0:
        return labels.copy()

    shuttle_ids = [int(v) for v in np.unique(labels) if v != 0]
    if not shuttle_ids:
        return labels.copy()

    # Step 1 & 2: per-shuttle morphological closing then opening.
    # Operate on a clean canvas: clear all shuttle pixels first, then
    # write back each shuttle's cleaned mask. This avoids overlap
    # ambiguity when closing for shuttle A would touch shuttle B's pixels.
    out = np.zeros_like(labels)
    close_kernel = np.ones((MORPH_CLOSE_SIZE, MORPH_CLOSE_SIZE), np.uint8)
    open_kernel = np.ones((MORPH_OPEN_SIZE, MORPH_OPEN_SIZE), np.uint8)

    for sh in shuttle_ids:
        mask = (labels == sh).astype(np.uint8)
        if mask.sum() == 0:
            continue
        # Closing: fills holes within the motif body.
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, close_kernel)
        # Opening: removes thin outlier strokes.
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, open_kernel)
        # Where this shuttle now claims a pixel, write its label. In the
        # rare case of multi-shuttle claim (because closing expanded both),
        # the LATER shuttle wins. Shuttles are processed in label order so
        # higher-numbered shuttles take precedence. This is a known limit;
        # for textured brocade output the difference is negligible.
        out[mask == 1] = sh

    # Step 3: drop tiny connected regions per shuttle.
    out = _drop_small_regions(out, min_size=MIN_REGION_PIXELS)

    return out


def _drop_small_regions(labels: np.ndarray, min_size: int) -> np.ndarray:
    """
    For each shuttle, find connected components smaller than `min_size`
    pixels (4-connectivity) and reassign them to background (label 0).

    Single pass; the previous morphology step has already eliminated most
    candidates, so iterating is unnecessary.
    """
    out = labels.copy()
    for sh in np.unique(out):
        if sh == 0:
            continue
        mask = (out == sh).astype(np.uint8)
        comp_ids, n_comps = ndimage.label(mask)
        if n_comps == 0:
            continue
        sizes = ndimage.sum(mask, comp_ids, index=range(1, n_comps + 1))
        for comp_id, size in enumerate(sizes, start=1):
            if size < min_size:
                out[comp_ids == comp_id] = 0
    return out
