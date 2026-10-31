"""
ocr.py
-------
Runs pytesseract OCR on a preprocessed OpenCV image and returns the
raw extracted text. This raw text is later parsed by
utils/regex_extractor.py into structured medical fields.
"""

import pytesseract
import numpy as np
from PIL import Image

# ---------------------------------------------------------------------------
# Windows-specific configuration:
# pytesseract is only a Python wrapper around the Tesseract OCR *engine*.
# On Windows, the engine is not automatically found on PATH after installing
# it, so we point pytesseract directly at the installed executable.
#
# If Tesseract was installed to a different location on your machine, update
# the path below to match (check with, e.g.,
#   Test-Path "C:\Program Files\Tesseract-OCR\tesseract.exe"
# in PowerShell).
#
# On macOS/Linux this line is not needed (tesseract is normally on PATH after
# `brew install tesseract` or `apt-get install tesseract-ocr`), so it is safe
# to comment out or remove there.
# ---------------------------------------------------------------------------
import os as _os
_WIN_TESSERACT = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
if _os.path.exists(_WIN_TESSERACT):  # only on Windows installs; elsewhere tesseract is found on PATH
    pytesseract.pytesseract.tesseract_cmd = _WIN_TESSERACT


def extract_text_from_image(cv_image: np.ndarray, lang: str = "eng") -> str:
    """
    Runs pytesseract OCR on an OpenCV (numpy array) image.

    Args:
        cv_image: A preprocessed grayscale/binarized OpenCV image.
        lang: Tesseract language pack to use (default English).

    Returns:
        The raw text string extracted from the image. Returns an
        empty string if OCR fails or finds no text, rather than
        raising, so the calling UI can show a friendly message.
    """
    try:
        # pytesseract can operate directly on numpy arrays via PIL conversion
        pil_image = Image.fromarray(cv_image)

        # --psm 6 assumes a uniform block of text, which works well for
        # structured lab reports with a table-like layout.
        custom_config = r"--oem 3 --psm 6"
        raw_text = pytesseract.image_to_string(pil_image, lang=lang, config=custom_config)
        return raw_text.strip()
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError(
            "Tesseract OCR engine was not found on this system. "
            "Please install it (see README.md) and ensure it is on your PATH."
        )
    except Exception as e:
        raise RuntimeError(f"Error extracting text via OCR: {e}")