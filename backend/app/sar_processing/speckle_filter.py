"""
SAR Processing — Speckle Filtering.

Implements Lee filter and Refined Lee filter for reducing
multiplicative speckle noise in SAR imagery while preserving
edges and spatial detail.
"""

import numpy as np
from scipy import ndimage

from app.core.logging_config import get_logger
from app.config.constants import SPECKLE_FILTER_WINDOW

logger = get_logger(__name__)


def lee_filter(
    image: np.ndarray,
    window_size: int = SPECKLE_FILTER_WINDOW,
) -> np.ndarray:
    """
    Apply Lee speckle filter to a SAR image.

    The Lee filter is an adaptive filter that reduces speckle noise
    while preserving the mean backscatter. It works by computing
    local statistics (mean and variance) within a sliding window.

    The filtered pixel value is:
        I_filtered = I_mean + W * (I - I_mean)

    Where W is the adaptive weight:
        W = 1 - (Cu² / Ci²)

    Cu = coefficient of variation of noise (assumed ~0.2 for multi-look)
    Ci = coefficient of variation of the local window

    Args:
        image: 2D numpy array of SAR backscatter values (linear or dB).
        window_size: Size of the filtering window (must be odd).

    Returns:
        Filtered image as a 2D numpy array.
    """
    if window_size % 2 == 0:
        window_size += 1
        logger.warning("Window size adjusted to odd number: %d", window_size)

    logger.info("Applying Lee filter — window_size=%d, shape=%s", window_size, image.shape)

    img = image.astype(np.float64)

    # Compute local mean using uniform filter
    local_mean = ndimage.uniform_filter(img, size=window_size)

    # Compute local variance
    local_sq_mean = ndimage.uniform_filter(img ** 2, size=window_size)
    local_variance = local_sq_mean - local_mean ** 2
    local_variance = np.maximum(local_variance, 0)  # Avoid negative variance

    # Coefficient of variation of noise (for ~4-look Sentinel-1 GRD)
    cu_squared = 0.05  # Cu ≈ 0.22 for 4-look data → Cu² ≈ 0.05

    # Coefficient of variation of image
    ci_squared = local_variance / (local_mean ** 2 + 1e-10)

    # Adaptive weight
    weight = 1.0 - (cu_squared / (ci_squared + 1e-10))
    weight = np.clip(weight, 0.0, 1.0)

    # Apply filter
    filtered = local_mean + weight * (img - local_mean)

    logger.info("Lee filter applied successfully")
    return filtered


def refined_lee_filter(
    image: np.ndarray,
    window_size: int = SPECKLE_FILTER_WINDOW,
    num_looks: int = 4,
) -> np.ndarray:
    """
    Apply Refined Lee speckle filter.

    The Refined Lee filter improves upon the standard Lee filter by
    using directional windows to better preserve edges. It selects
    the most homogeneous directional window for each pixel.

    This implementation uses 8 directional sub-windows (horizontal,
    vertical, and two diagonals, plus their complements).

    Args:
        image: 2D numpy array of SAR backscatter values.
        window_size: Size of the filtering window (must be odd, >= 7).
        num_looks: Number of looks in the SAR image (affects noise model).

    Returns:
        Filtered image preserving edges better than standard Lee.
    """
    if window_size < 7:
        window_size = 7
    if window_size % 2 == 0:
        window_size += 1

    logger.info(
        "Applying Refined Lee filter — window=%d, looks=%d",
        window_size, num_looks,
    )

    img = image.astype(np.float64)
    half = window_size // 2
    rows, cols = img.shape
    filtered = np.copy(img)

    # Define 4 directional kernels (horizontal, vertical, 2 diagonals)
    directions = _create_directional_kernels(window_size)

    cu_squared = 1.0 / num_looks  # Noise coefficient of variation squared

    for i in range(half, rows - half):
        for j in range(half, cols - half):
            window = img[i - half:i + half + 1, j - half:j + half + 1]

            # Find the most homogeneous direction
            min_variance = float("inf")
            best_mean = img[i, j]

            for direction_mask in directions:
                pixels = window[direction_mask]
                if len(pixels) == 0:
                    continue
                d_var = np.var(pixels)
                if d_var < min_variance:
                    min_variance = d_var
                    best_mean = np.mean(pixels)

            # Apply Lee formula with best directional statistics
            ci_squared = min_variance / (best_mean ** 2 + 1e-10)
            weight = max(0.0, 1.0 - cu_squared / (ci_squared + 1e-10))
            weight = min(weight, 1.0)

            filtered[i, j] = best_mean + weight * (img[i, j] - best_mean)

    logger.info("Refined Lee filter applied successfully")
    return filtered


def _create_directional_kernels(window_size: int) -> list:
    """
    Create boolean masks for 4 directional sub-windows.

    Returns masks for horizontal, vertical, and two diagonal
    directions within a square window.

    Args:
        window_size: The window dimension.

    Returns:
        List of 2D boolean numpy arrays (masks).
    """
    half = window_size // 2
    masks = []

    # Horizontal direction
    h_mask = np.zeros((window_size, window_size), dtype=bool)
    h_mask[half, :] = True
    h_mask[half - 1, :] = True
    h_mask[half + 1, :] = True
    masks.append(h_mask)

    # Vertical direction
    v_mask = np.zeros((window_size, window_size), dtype=bool)
    v_mask[:, half] = True
    v_mask[:, half - 1] = True
    v_mask[:, half + 1] = True
    masks.append(v_mask)

    # Diagonal (top-left to bottom-right)
    d1_mask = np.zeros((window_size, window_size), dtype=bool)
    for k in range(-1, 2):
        np.fill_diagonal(d1_mask[max(0, k):, max(0, -k):], True)
    masks.append(d1_mask)

    # Anti-diagonal (top-right to bottom-left)
    d2_mask = np.zeros((window_size, window_size), dtype=bool)
    flipped = np.fliplr(d1_mask)
    d2_mask[:] = flipped
    masks.append(d2_mask)

    return masks


def apply_speckle_filter(
    image: np.ndarray,
    method: str = "lee",
    window_size: int = SPECKLE_FILTER_WINDOW,
) -> np.ndarray:
    """
    Apply speckle filter using the specified method.

    This is the main entry point for speckle filtering. It selects
    the appropriate filter implementation based on the method parameter.

    Args:
        image: Input SAR image array.
        method: Filter method — "lee" or "refined_lee".
        window_size: Filter window size.

    Returns:
        Speckle-filtered image array.

    Raises:
        ValueError: If an unsupported filter method is specified.
    """
    methods = {
        "lee": lee_filter,
        "refined_lee": refined_lee_filter,
    }

    if method not in methods:
        raise ValueError(
            f"Unknown speckle filter method: '{method}'. "
            f"Supported methods: {list(methods.keys())}"
        )

    return methods[method](image, window_size=window_size)
