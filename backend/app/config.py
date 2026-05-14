"""
Application configuration.

All limits and defaults are defined here so they can be tuned in one place.
"""

# Loom dimension limits (in pixels = pins/cards)
MIN_PINS = 1
MAX_PINS = 10_000
MIN_CARDS = 1
MAX_CARDS = 10_000

# Shuttle count range
MIN_SHUTTLES = 2
MAX_SHUTTLES = 8

# Input image limits
MIN_INPUT_SHORT_EDGE = 500          # px; reject images smaller than this
MAX_INPUT_LONG_EDGE = 8_000         # px; auto-downscale to this before processing
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024  # 50 MB upload cap

# Processing
PROCESSING_TIMEOUT_SECONDS = 120

# Pre-processing
# Aggressive smoothing tuned for textured brocade close-ups, which have
# internal fabric texture (warp/weft visible at high zoom) that k-means
# would otherwise split into multiple "noise" clusters.
#
# The pipeline applies the bilateral filter PASSES times, then one median
# blur, then a light Gaussian. This combination flattens texture inside
# motifs while keeping motif boundaries crisp.
BILATERAL_D = 11
BILATERAL_SIGMA_COLOR = 120
BILATERAL_SIGMA_SPACE = 120
BILATERAL_PASSES = 3

# Median blur kernel size (odd integer). Applied after bilateral filtering
# to smash residual high-frequency texture.
MEDIAN_BLUR_KSIZE = 5

# Final light Gaussian smooth before k-means to tame any leftover noise.
GAUSSIAN_BLUR_KSIZE = 3

# Post-quantization morphology - applied per shuttle.
# Closing (dilate then erode) fills small holes inside motifs.
# Opening (erode then dilate) removes thin outlier strokes.
MORPH_CLOSE_SIZE = 3
MORPH_OPEN_SIZE = 2

# Drop any connected region (per shuttle) smaller than this many pixels.
# 9 = roughly a 3x3 patch. Reassigns it to the background.
MIN_REGION_PIXELS = 9

# K-means
# Cap n_init so it doesn't run a high number of restarts and slow us down.
KMEANS_N_INIT = 5
KMEANS_MAX_ITER = 100
KMEANS_RANDOM_STATE = 42

# Default shuttle filenames (in order of frequency, after the background).
# Used for the first N shuttles; additional shuttles fall back to "shuttle_N".
# These are the conventional Indian brocade weaving thread names.
DEFAULT_SHUTTLE_NAMES = ["resham", "jari", "meena"]


