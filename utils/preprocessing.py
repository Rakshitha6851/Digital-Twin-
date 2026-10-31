"""
preprocessing.py
------------------
OpenCV-based image preprocessing pipeline used to clean up scanned /
photographed medical reports before they are sent to pytesseract for
Optical Character Recognition (OCR).

Pipeline steps:
    1. Grayscale conversion
    2. Contrast enhancement (CLAHE)
    3. Noise removal (denoising)
    4. Thresholding (binarization)
    5. Sharpening
    6. Resizing (upscaling small images improves OCR accuracy)
"""

import cv2
import numpy as np
from PIL import Image


def compute_blur_score(pil_image: Image.Image) -> float:
    """
    Measures image sharpness using the variance of the Laplacian — a
    standard, widely-used OpenCV technique for blur detection.

    How it works: the Laplacian operator highlights edges (rapid
    intensity changes). A sharp, in-focus image has many strong edges,
    so the *variance* of the Laplacian response is high. A blurry image
    has soft, smeared edges, so the variance is low.

    Returns:
        A float score. Higher = sharper. Typically:
            < 50   : very blurry / unusable for OCR
            50-100 : borderline / may OCR poorly
            > 100  : reasonably sharp
        (These are rule-of-thumb thresholds commonly used for this
        technique; see is_image_too_blurry() for how it's applied here.)
    """
    try:
        cv_image = pil_to_cv2(pil_image)
        gray = convert_to_grayscale(cv_image)

        # Normalize scale so the score isn't skewed by image resolution:
        # resize to a consistent width before measuring.
        target_width = 800
        if gray.shape[1] != target_width:
            scale = target_width / gray.shape[1]
            gray = cv2.resize(gray, (target_width, int(gray.shape[0] * scale)))

        laplacian_variance = cv2.Laplacian(gray, cv2.CV_64F).var()
        return float(laplacian_variance)
    except Exception as e:
        raise RuntimeError(f"Error computing image blur score: {e}")


def is_image_too_blurry(pil_image: Image.Image, threshold: float = 60.0) -> bool:
    """
    Returns True if the image is likely too blurry for reliable OCR,
    based on the Laplacian-variance blur score.

    Args:
        pil_image: The uploaded image.
        threshold: Minimum acceptable sharpness score. Images scoring
                   below this are flagged as too blurry. 60.0 is a
                   reasonable general-purpose default for document/text
                   photos; lower it if legitimate reports are being
                   rejected, raise it to be stricter.
    """
    try:
        score = compute_blur_score(pil_image)
        return score < threshold
    except Exception:
        # If blur detection itself fails for some reason, don't block the
        # user's upload on that basis — let OCR proceed and fail its own
        # way if the image is truly unusable.
        return False


def pil_to_cv2(pil_image: Image.Image) -> np.ndarray:
    """Convert a PIL Image to an OpenCV (numpy array, BGR) image."""
    try:
        rgb_image = np.array(pil_image.convert("RGB"))
        bgr_image = cv2.cvtColor(rgb_image, cv2.COLOR_RGB2BGR)
        return bgr_image
    except Exception as e:
        raise RuntimeError(f"Error converting PIL image to OpenCV format: {e}")


def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
    """Step 1: Convert a BGR image to single-channel grayscale."""
    try:
        return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    except Exception as e:
        raise RuntimeError(f"Error converting image to grayscale: {e}")


def enhance_contrast(gray_image: np.ndarray) -> np.ndarray:
    """Step 2: Enhance contrast using CLAHE (Contrast Limited Adaptive
    Histogram Equalization) so faint printed/handwritten text becomes
    more legible."""
    try:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        return clahe.apply(gray_image)
    except Exception as e:
        raise RuntimeError(f"Error enhancing contrast: {e}")


def remove_noise(image: np.ndarray) -> np.ndarray:
    """Step 3: Remove noise using Non-local Means Denoising, which
    helps eliminate JPEG artifacts and camera-sensor noise."""
    try:
        return cv2.fastNlMeansDenoising(image, None, h=10, templateWindowSize=7, searchWindowSize=21)
    except Exception as e:
        raise RuntimeError(f"Error removing noise: {e}")


def apply_thresholding(image: np.ndarray) -> np.ndarray:
    """Step 4: Binarize the image using Otsu's thresholding so text is
    pure black on a pure white background (best for OCR)."""
    try:
        _, thresholded = cv2.threshold(image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        return thresholded
    except Exception as e:
        raise RuntimeError(f"Error applying thresholding: {e}")


def sharpen_image(image: np.ndarray) -> np.ndarray:
    """Step 5: Sharpen the image using a convolution kernel to make
    character edges crisper."""
    try:
        sharpen_kernel = np.array([[0, -1, 0],
                                    [-1, 5, -1],
                                    [0, -1, 0]])
        return cv2.filter2D(image, -1, sharpen_kernel)
    except Exception as e:
        raise RuntimeError(f"Error sharpening image: {e}")


def resize_image(image: np.ndarray, scale_factor: float = 2.0) -> np.ndarray:
    """Step 6: Upscale the image. Small/low-res medical report photos
    often OCR poorly; upscaling with cubic interpolation improves
    character recognition."""
    try:
        width = int(image.shape[1] * scale_factor)
        height = int(image.shape[0] * scale_factor)
        return cv2.resize(image, (width, height), interpolation=cv2.INTER_CUBIC)
    except Exception as e:
        raise RuntimeError(f"Error resizing image: {e}")


def preprocess_pipeline(pil_image: Image.Image) -> np.ndarray:
    """
    Runs the full OpenCV preprocessing pipeline on a PIL image and
    returns a cleaned-up OpenCV image ready for pytesseract.

    Order: grayscale -> resize -> contrast enhance -> denoise ->
           threshold -> sharpen
    (Resizing early makes downstream filters operate on more pixels,
    which tends to give the OCR engine more detail to work with.)
    """
    try:
        cv_image = pil_to_cv2(pil_image)
        gray = convert_to_grayscale(cv_image)
        resized = resize_image(gray, scale_factor=2.0)
        contrasted = enhance_contrast(resized)
        denoised = remove_noise(contrasted)
        thresholded = apply_thresholding(denoised)
        sharpened = sharpen_image(thresholded)
        return sharpened
    except Exception as e:
        raise RuntimeError(f"Error in preprocessing pipeline: {e}")