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
# OpenCV bilateral filter parameters - moderate strength.
# d=neighborhood diameter, sigmaColor=color similarity, sigmaSpace=spatial similarity.
BILATERAL_D = 9
BILATERAL_SIGMA_COLOR = 75
BILATERAL_SIGMA_SPACE = 75

# K-means
# Cap n_init so it doesn't run a high number of restarts and slow us down.
KMEANS_N_INIT = 5
KMEANS_MAX_ITER = 100
KMEANS_RANDOM_STATE = 42

# Default shuttle filenames (in order of frequency, after the background).
# Used for the first N shuttles; additional shuttles fall back to "shuttle_N".
# These are the conventional Indian brocade weaving thread names.
DEFAULT_SHUTTLE_NAMES = ["resham", "jari", "meena"]

# Minimum motif size cleanup
MOTIF_MIN_SIZE_DEFAULT = 2
MOTIF_MIN_SIZE_MAX = 5
