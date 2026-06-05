"""Find vials by cap colour. Pure OpenCV, no machine learning.

This is the whole exercise in one file. Given an image of the
autosampler bench (overhead view of the rack with capped vials in
it), return one `CapDetection` per visible cap and its colour.

How it works, in five steps:

    1. Convert BGR -> HSV. In HSV, "red" / "blue" / "green" are
       small bands of the H (hue) channel — much easier to threshold
       than RGB where lighting changes pull every channel at once.
    2. For each target colour, build a binary mask of pixels inside
       its HSV range (cv2.inRange).
    3. Morphological closing to fill small dropouts caused by cap
       glare or shadows (cv2.morphologyEx).
    4. Connected-component labelling — every separate blob in the
       mask becomes one detection (cv2.connectedComponentsWithStats).
    5. Reject blobs that are too small (noise) or too large (the
       rack body itself or a wall).

The autosampler tie-in is in `caps_to_slots` at the bottom of the
file: it takes the pixel centroids and assigns each detection to a
slot id in the rack's left-to-right ordering, so a LIMS query of
"give me all red caps" maps directly to slot indices.

Example:

    >>> import cv2
    >>> from cap_segmenter import find_all_caps, caps_to_slots
    >>> bgr = cv2.imread("scene.png")
    >>> caps = find_all_caps(bgr)
    >>> for c in caps:
    ...     print(c.color, c.centroid_xy)
    >>> print(caps_to_slots(caps, num_slots=5, image_width=bgr.shape[1]))
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# HSV thresholds — H in [0, 179], S in [0, 255], V in [0, 255]
# ---------------------------------------------------------------------------
#
# Red wraps around H=0 (it sits at both ends of the hue circle), so it
# needs TWO ranges that get OR'd together. Blue and green each fit in
# one range. These values match the cap colours rendered by exercise
# 1's `worlds/autosampler_cell.sdf` and tolerate the brightness shifts
# used in `demo.py` to fake three lighting conditions.
#
# Re-tune these for real-world lighting with the recipe in
# IMPLEMENTATION_NOTES.md ("Picking HSV ranges in the real world").
HsvRange = Tuple[Tuple[int, int, int], Tuple[int, int, int]]

CAP_HSV_RANGES: Dict[str, List[HsvRange]] = {
    "red": [
        ((0,   70, 50), (10,  255, 255)),    # hue near 0
        ((170, 70, 50), (179, 255, 255)),    # hue near 180 (red wraps)
    ],
    "blue": [
        ((95,  70, 50), (130, 255, 255)),
    ],
    "green": [
        ((40,  60, 40), (85,  255, 255)),
    ],
}

# At the overhead-camera distance in exercise 1, a 9 mm screw cap
# projects to roughly a 20-50 px disc (~300-2500 px area). Anything
# below the floor is per-pixel sensor noise; anything above the
# ceiling is the rack body or a wall.
MIN_AREA_PX = 300
MAX_AREA_PX = 8000

# Morphological kernel — closes 5-pixel gaps from glare on the cap.
_CLOSE_KERNEL = np.ones((5, 5), dtype=np.uint8)


@dataclass(frozen=True)
class CapDetection:
    """One cap found in one image.

    `centroid_xy` is in (x, y) pixel coordinates with the origin at
    the top-left of the image (OpenCV's convention).
    `bbox_xywh` is (x, y, width, height) of the cap's bounding box.
    """
    color: str
    centroid_xy: Tuple[int, int]
    area_px: int
    bbox_xywh: Tuple[int, int, int, int]


def find_caps(bgr_image: np.ndarray, target_color: str) -> List[CapDetection]:
    """Return every cap of one colour in one image."""
    if target_color not in CAP_HSV_RANGES:
        raise ValueError(
            f"unknown colour: {target_color!r}; "
            f"known = {list(CAP_HSV_RANGES)!r}",
        )

    # Step 1 — work in HSV so a single channel encodes "redness" etc.
    hsv = cv2.cvtColor(bgr_image, cv2.COLOR_BGR2HSV)

    # Step 2 — build the binary mask. OR'd ranges handle hue wrap-around.
    mask = np.zeros(hsv.shape[:2], dtype=np.uint8)
    for lo, hi in CAP_HSV_RANGES[target_color]:
        mask = cv2.bitwise_or(mask, cv2.inRange(hsv, np.array(lo), np.array(hi)))

    # Step 3 — close small holes. A glossy cap often has a glare spot
    # in the middle that the threshold rejects; CLOSE fills it in.
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, _CLOSE_KERNEL)

    # Step 4 — every connected blob becomes one candidate detection.
    # `connectedComponentsWithStats` hands back the bbox and centroid
    # for each label in a single call — exactly what we need.
    num_labels, _labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask, connectivity=8,
    )

    detections: List[CapDetection] = []
    # Label 0 is the background; skip it.
    for label_id in range(1, num_labels):
        area = int(stats[label_id, cv2.CC_STAT_AREA])

        # Step 5 — drop noise and the rack/wall.
        if area < MIN_AREA_PX or area > MAX_AREA_PX:
            continue

        x = int(stats[label_id, cv2.CC_STAT_LEFT])
        y = int(stats[label_id, cv2.CC_STAT_TOP])
        w = int(stats[label_id, cv2.CC_STAT_WIDTH])
        h = int(stats[label_id, cv2.CC_STAT_HEIGHT])
        cx, cy = centroids[label_id]
        detections.append(CapDetection(
            color=target_color,
            centroid_xy=(int(round(cx)), int(round(cy))),
            area_px=area,
            bbox_xywh=(x, y, w, h),
        ))
    return detections


def find_all_caps(bgr_image: np.ndarray) -> List[CapDetection]:
    """Run every configured colour and return one combined list."""
    out: List[CapDetection] = []
    for color in CAP_HSV_RANGES:
        out.extend(find_caps(bgr_image, color))
    return out


# ---------------------------------------------------------------------------
# Autosampler tie-in — pixel centroids -> rack slot indices
# ---------------------------------------------------------------------------

def caps_to_slots(
    caps: List[CapDetection],
    num_slots: int,
    image_width: int,
) -> Dict[int, str]:
    """Assign each detection to a left-to-right slot id (1-based).

    The autosampler tie-in works because the overhead camera sees the
    rack as a horizontal row of slots. Slot 1 is the leftmost cap,
    slot N is the rightmost. We split the image width into `num_slots`
    equal vertical bands and assign each detection to the band that
    contains its centroid.

    Returns `{slot_id: color}` for every detected slot. Empty slots
    are simply absent from the dict.

    In a real cell you would use a ROI rectangle for the rack instead
    of the whole image width — same idea, smaller domain.
    """
    if num_slots <= 0:
        raise ValueError(f"num_slots must be > 0, got {num_slots}")

    slot_width = image_width / num_slots
    slot_to_color: Dict[int, str] = {}
    for cap in caps:
        cx, _ = cap.centroid_xy
        # Slots are 1-indexed to match how a lab tech reads them.
        slot_id = int(cx // slot_width) + 1
        slot_id = max(1, min(num_slots, slot_id))
        slot_to_color[slot_id] = cap.color
    return slot_to_color


def annotate(bgr_image: np.ndarray, caps: List[CapDetection]) -> np.ndarray:
    """Draw each detection on a copy of the image. Handy for the demo.

    We draw the bounding box, the centroid as a small filled circle,
    and the colour name as text just above the bbox. Box + text are
    drawn in the cap's own colour so it is obvious which is which.
    """
    overlay = bgr_image.copy()
    bgr_for = {
        "red":   (40, 40, 220),
        "blue":  (220, 100, 30),
        "green": (60, 200, 80),
    }
    for cap in caps:
        x, y, w, h = cap.bbox_xywh
        colour = bgr_for.get(cap.color, (255, 255, 255))
        cv2.rectangle(overlay, (x, y), (x + w, y + h), colour, 2)
        cv2.circle(overlay, cap.centroid_xy, 3, colour, -1)
        cv2.putText(
            overlay, cap.color, (x, max(y - 6, 12)),
            cv2.FONT_HERSHEY_SIMPLEX, 0.5, colour, 1, cv2.LINE_AA,
        )
    return overlay
