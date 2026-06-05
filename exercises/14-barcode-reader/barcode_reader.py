"""Decode a vial's barcode by spinning it in front of a side camera.

Two public functions:

    decode_barcode(bgr)            -> str | None
    spin_and_decode(frame_provider, max_steps) -> (code, step_found)

`decode_barcode` is the single-frame decoder. `spin_and_decode` is the
search loop that the arm controller calls at the scan station: ask
for one camera frame, try to decode, rotate the wrist a bit, repeat.

Why two decoders? The checklist names `pyzbar` (handles both QR codes
and 1D barcodes — Code 128, UPC, ...). pyzbar needs the libzbar0
system library; if that's not installed we fall back to
`cv2.QRCodeDetector` (QR-only, but pure-OpenCV with no extra deps).
The arm code calls `decode_barcode` and does not care which decoder
ran.
"""

from __future__ import annotations

from typing import Callable, Optional, Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# Decoder selection — pyzbar if available, cv2.QRCodeDetector otherwise.
# ---------------------------------------------------------------------------

def _try_load_pyzbar() -> Optional[Callable[[np.ndarray], Optional[str]]]:
    """Return a callable(bgr) -> str|None backed by pyzbar, or None."""
    try:
        from pyzbar.pyzbar import decode as _pyzbar_decode  # type: ignore
    except (ImportError, OSError):
        # ImportError if the python package is missing.
        # OSError if libzbar0 is missing on the system.
        return None

    def _decode(bgr: np.ndarray) -> Optional[str]:
        # pyzbar wants grayscale. Converting once is faster than letting
        # libzbar do it internally.
        gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)
        found = _pyzbar_decode(gray)
        if not found:
            return None
        # If multiple codes are visible we pick the first — the spin loop
        # holds one vial at a time, so this is the only one we care
        # about.
        return found[0].data.decode("utf-8", errors="replace")

    return _decode


def _cv2_decoder() -> Callable[[np.ndarray], Optional[str]]:
    """Return a callable(bgr) -> str|None backed by cv2.QRCodeDetector."""
    detector = cv2.QRCodeDetector()

    def _decode(bgr: np.ndarray) -> Optional[str]:
        # `detectAndDecode` returns (text, bbox, straight_qrcode).
        # An empty string means "no code found".
        text, _bbox, _ = detector.detectAndDecode(bgr)
        return text if text else None

    return _decode


# Pick a decoder once at import time. Re-checking on every call would
# be wasteful — the libraries don't appear and disappear at runtime.
_PRIMARY = _try_load_pyzbar()
_FALLBACK = _cv2_decoder()

if _PRIMARY is None:
    DECODER_NAME = "cv2.QRCodeDetector (fallback)"
    _DECODE = _FALLBACK
else:
    DECODER_NAME = "pyzbar"
    _DECODE = _PRIMARY


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def decode_barcode(bgr_image: np.ndarray) -> Optional[str]:
    """Try to read a barcode / QR code from one frame.

    Returns the decoded text (e.g. "B-2024-0117") if a code was
    found, otherwise None. Never raises.
    """
    if bgr_image is None or bgr_image.size == 0:
        return None
    try:
        return _DECODE(bgr_image)
    except Exception:
        # Decoder libraries occasionally raise on degenerate inputs
        # (all-black frame, weird shape). Treat any failure as "no
        # code this frame" — the spin loop just tries the next angle.
        return None


def spin_and_decode(
    frame_provider: Callable[[int], np.ndarray],
    max_steps: int = 12,
) -> Tuple[Optional[str], int]:
    """Drive the spin-in-place search at the scan station.

    `frame_provider(step)` is a callable the arm controller supplies.
    It should:
      1. Rotate the wrist by one step (e.g. 360 / max_steps degrees).
      2. Capture one camera frame.
      3. Return it as a BGR numpy array.

    The loop calls `frame_provider` up to `max_steps` times and stops
    the moment a decode succeeds. Returns:
      (decoded text, step at which it was found)   on success
      (None,         max_steps)                    on time-out

    A real arm controller wires `frame_provider` to one wrist nudge
    + a `cv_bridge` read from the scan-camera topic. The demo wires
    it to a precomputed list of rendered angles.
    """
    if max_steps <= 0:
        raise ValueError(f"max_steps must be > 0, got {max_steps}")

    for step in range(max_steps):
        frame = frame_provider(step)
        code = decode_barcode(frame)
        if code is not None:
            return code, step
    return None, max_steps
