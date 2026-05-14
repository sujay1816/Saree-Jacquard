"""
Color quantization via k-means in LAB color space.

The key design decision: we quantize to N+1 colors when the user asks for
N shuttles. The largest cluster (by pixel count) is treated as the
background ("no thread fires" state) and is NOT exported as a shuttle BMP.
The remaining N clusters become the N shuttle masks.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np
from sklearn.cluster import KMeans

from app.config import KMEANS_MAX_ITER, KMEANS_N_INIT, KMEANS_RANDOM_STATE
from app.processing.preprocess import lab_to_rgb_palette


@dataclass
class QuantizationResult:
    """
    Output of the quantization step.

    Attributes:
        labels: HxW uint8 array. Each pixel holds an index into `palette_rgb`.
                Index 0 is always the background. Indices 1..N are the shuttles
                in descending order of pixel frequency.
        palette_rgb: (N+1)x3 uint8 array of RGB colors, ordered such that
                     [0] = background, [1..N] = shuttles by frequency.
        pixel_counts: (N+1,) int array; pixel_counts[i] = number of pixels
                      assigned to palette[i].
        shape: (height, width) of the labels array.
    """

    labels: np.ndarray
    palette_rgb: np.ndarray
    pixel_counts: np.ndarray
    shape: Tuple[int, int]

    @property
    def num_shuttles(self) -> int:
        """Number of shuttles (excludes the background at index 0)."""
        return self.palette_rgb.shape[0] - 1

    @property
    def background_rgb(self) -> Tuple[int, int, int]:
        return tuple(int(x) for x in self.palette_rgb[0])

    def shuttle_rgb(self, shuttle_idx: int) -> Tuple[int, int, int]:
        """RGB color of shuttle (1-based)."""
        if shuttle_idx < 1 or shuttle_idx > self.num_shuttles:
            raise IndexError(f"Shuttle index {shuttle_idx} out of range")
        return tuple(int(x) for x in self.palette_rgb[shuttle_idx])


def quantize_image(
    lab_pixels: np.ndarray,
    image_shape: Tuple[int, int],
    num_shuttles: int,
) -> QuantizationResult:
    """
    Run k-means on LAB pixels with K = num_shuttles + 1, then reorder
    clusters so the background (most frequent) is at index 0 and the
    rest are sorted by descending frequency.

    Args:
        lab_pixels: Nx3 float32 LAB pixel array (from preprocess.rgb_to_lab_pixels).
        image_shape: (height, width) of the original 2D image.
        num_shuttles: how many shuttle BMPs the user wants (2-8).

    Returns:
        QuantizationResult with labels reshaped to image_shape.
    """
    k = num_shuttles + 1  # +1 for background

    # Sanity: if image has fewer unique pixels than K, k-means will still
    # work but some clusters may be empty. That's fine - empty clusters
    # just contribute zero-count entries to the palette.
    kmeans = KMeans(
        n_clusters=k,
        n_init=KMEANS_N_INIT,
        max_iter=KMEANS_MAX_ITER,
        random_state=KMEANS_RANDOM_STATE,
    )
    raw_labels = kmeans.fit_predict(lab_pixels)
    raw_centers_lab = kmeans.cluster_centers_  # shape (k, 3)

    # Count how many pixels landed in each cluster
    raw_counts = np.bincount(raw_labels, minlength=k)

    # Sort cluster indices by descending pixel count.
    # The most frequent cluster becomes our background (index 0 in output).
    sort_order = np.argsort(-raw_counts)  # descending

    # Build a remap table: old_cluster_id -> new_cluster_id
    remap = np.zeros(k, dtype=np.int32)
    for new_id, old_id in enumerate(sort_order):
        remap[old_id] = new_id

    new_labels_flat = remap[raw_labels].astype(np.uint8)
    new_labels = new_labels_flat.reshape(image_shape)

    # Reorder palette and counts to match
    sorted_centers_lab = raw_centers_lab[sort_order]
    sorted_counts = raw_counts[sort_order]
    palette_rgb = lab_to_rgb_palette(sorted_centers_lab)

    return QuantizationResult(
        labels=new_labels,
        palette_rgb=palette_rgb,
        pixel_counts=sorted_counts,
        shape=image_shape,
    )


def build_palette_metadata(
    qr: QuantizationResult,
    default_names: List[str],
) -> Tuple[List[dict], dict]:
    """
    Produce the per-shuttle metadata that goes into palette.json and the API
    response, plus the background info.

    Default naming:
      - shuttle 1 -> default_names[0] (e.g. "resham")
      - shuttle 2 -> default_names[1] (e.g. "jari")
      - ...
      - shuttle k -> "shuttle_k" if k > len(default_names)
    """
    total_pixels = int(qr.labels.size)
    bg_count = int(qr.pixel_counts[0])

    bg_rgb = qr.background_rgb
    background_info = {
        "rgb": list(bg_rgb),
        "hex": _rgb_to_hex(bg_rgb),
        "pixel_count": bg_count,
        "pixel_fraction": bg_count / total_pixels if total_pixels else 0.0,
    }

    palette_entries: List[dict] = []
    for i in range(1, qr.palette_rgb.shape[0]):
        rgb = qr.shuttle_rgb(i)
        count = int(qr.pixel_counts[i])
        if i - 1 < len(default_names):
            default_name = default_names[i - 1]
        else:
            default_name = f"shuttle_{i}"
        palette_entries.append(
            {
                "shuttle_number": i,
                "name": default_name,
                "rgb": list(rgb),
                "hex": _rgb_to_hex(rgb),
                "pixel_count": count,
                "pixel_fraction": count / total_pixels if total_pixels else 0.0,
            }
        )

    return palette_entries, background_info


def _rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    return "#{:02x}{:02x}{:02x}".format(*rgb)
