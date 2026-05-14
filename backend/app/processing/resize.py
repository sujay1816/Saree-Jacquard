"""
Final resize step: stretch-to-fit the labels array to exactly (cards x pins).

Nearest-neighbor interpolation is mandatory here. Bilinear/bicubic would
introduce intermediate label values that don't correspond to any palette
entry, which would silently corrupt the shuttle masks.

We use Pillow rather than OpenCV because Pillow's nearest-neighbor on an
indexed-palette mode (mode='P') is the safest path: it treats labels as
opaque indices, not pixel values to be interpolated.
"""

from __future__ import annotations

import numpy as np
from PIL import Image


def resize_labels_to_grid(
    labels: np.ndarray, pins: int, cards: int
) -> np.ndarray:
    """
    Stretch-resize a 2D uint8 label array to shape (cards, pins) using
    nearest-neighbor.

    pins  = output width  (number of warp ends, aka image columns)
    cards = output height (number of weft picks, aka image rows)

    The image is stretched independently in each axis. Aspect ratio is
    NOT preserved - this is intentional and matches the spec.
    """
    if labels.dtype != np.uint8:
        labels = labels.astype(np.uint8)

    h, w = labels.shape
    if (w, h) == (pins, cards):
        return labels  # no-op

    # PIL needs an Image. Use mode 'L' (grayscale) because we just need
    # nearest-neighbor on integer pixel values; the actual numeric range
    # of labels (0 to num_shuttles) is well within 0-255.
    img = Image.fromarray(labels, mode="L")
    resized = img.resize((pins, cards), Image.NEAREST)
    return np.asarray(resized, dtype=np.uint8)
