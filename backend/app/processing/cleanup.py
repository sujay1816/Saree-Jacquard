"""
Post-quantization cleanup of the labels array.

Two operations:

  1. `remove_speckle` - always-on. Kills isolated single pixels whose color
     differs from all 8 neighbors. These are almost always quantization noise
     or JPEG artifacts that would create single-pixel shuttle changes on the loom.

  2. `enforce_minimum_motif_size` - opt-in. Finds connected regions smaller
     than the user's threshold and reassigns them to their largest neighbor.
     Useful when the user wants to guarantee no thread floats below a certain
     size. Disabled by default because some designs (zari hairlines) need
     fine detail preserved.
"""

from __future__ import annotations

import numpy as np
from scipy import ndimage


def remove_speckle(labels: np.ndarray) -> np.ndarray:
    """
    Replace each pixel whose 8 neighbors all share a label different from
    itself with that neighbor label. Single-pass; not iterated.

    Quietly catches typical quantization noise without disturbing real
    motif edges (real edges have at least one same-label neighbor).

    `labels` is a 2D uint8 array. Returns a new array; input unchanged.
    """
    if labels.size == 0:
        return labels.copy()

    h, w = labels.shape
    out = labels.copy()

    # For each unique label, build a binary mask of its neighborhood
    # using a 3x3 box filter. If a pixel of label L has zero same-label
    # neighbors, it's isolated.
    unique_labels = np.unique(labels)
    if len(unique_labels) < 2:
        return out  # nothing to do on a single-color image

    # For speed, compute "is this pixel an isolated speckle of label L"
    # via a single pass: a pixel is speckle iff sum of same-label neighbors
    # (excluding self) is 0.
    for lbl in unique_labels:
        mask = (labels == lbl).astype(np.uint8)
        # Count of same-label pixels in 3x3 neighborhood (including self)
        neighbor_count = ndimage.uniform_filter(
            mask.astype(np.float32), size=3, mode="constant", cval=0.0
        ) * 9.0  # uniform_filter returns mean; multiply to get count
        # Exclude self from count
        neighbors_only = neighbor_count - mask
        isolated_positions = (mask == 1) & (neighbors_only < 0.5)
        if not np.any(isolated_positions):
            continue

        # Replace each isolated pixel with the most common neighbor label.
        # Use the global mode of the immediate neighbors via a small loop;
        # number of speckle pixels is typically small.
        ys, xs = np.where(isolated_positions)
        for y, x in zip(ys, xs):
            y0, y1 = max(0, y - 1), min(h, y + 2)
            x0, x1 = max(0, x - 1), min(w, x + 2)
            neighborhood = labels[y0:y1, x0:x1].ravel()
            # Exclude the center pixel itself
            others = neighborhood[neighborhood != lbl]
            if others.size > 0:
                vals, counts = np.unique(others, return_counts=True)
                out[y, x] = vals[np.argmax(counts)]

    return out


def enforce_minimum_motif_size(labels: np.ndarray, min_size: int) -> np.ndarray:
    """
    Reassign any connected region (4-connectivity) smaller than `min_size x min_size`
    pixels to its largest neighboring label.

    Uses pixel area (min_size**2) as the threshold rather than literal block size,
    which is the standard interpretation of "minimum motif size N" in weaving.

    Iterates until no small regions remain (or a safety cap is reached) so that
    merging doesn't itself create new small regions.

    min_size=1 is a no-op. min_size=2 means "no region smaller than 4 pixels".
    """
    if min_size <= 1:
        return labels.copy()

    threshold = min_size * min_size
    out = labels.copy()

    # Safety cap on iteration; in practice 2-3 passes is enough.
    for _iteration in range(5):
        changed = _merge_small_regions_once(out, threshold)
        if not changed:
            break

    return out


def _merge_small_regions_once(labels: np.ndarray, threshold: int) -> bool:
    """
    Single pass: find each connected region under `threshold` pixels and
    reassign it to the label of its largest neighboring region.

    Mutates `labels` in place. Returns True if any change was made.
    """
    changed = False
    unique_labels = np.unique(labels)

    for lbl in unique_labels:
        mask = labels == lbl
        # 4-connected labeling of regions of this color
        component_ids, num_components = ndimage.label(mask)
        if num_components == 0:
            continue

        # Region sizes (component_ids 1..num_components; 0 is "not this label")
        sizes = ndimage.sum(mask, component_ids, index=range(1, num_components + 1))

        for comp_id, size in enumerate(sizes, start=1):
            if size >= threshold:
                continue
            # Find neighboring labels via dilation of this component
            comp_mask = component_ids == comp_id
            dilated = ndimage.binary_dilation(comp_mask)
            border = dilated & ~comp_mask
            border_labels = labels[border]
            border_labels = border_labels[border_labels != lbl]
            if border_labels.size == 0:
                # No different-label neighbors (component touches only itself
                # or image edge). Leave alone.
                continue
            vals, counts = np.unique(border_labels, return_counts=True)
            new_label = vals[np.argmax(counts)]
            labels[comp_mask] = new_label
            changed = True

    return changed
