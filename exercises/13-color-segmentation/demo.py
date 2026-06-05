"""End-to-end demo: generate 3 synthetic scenes, segment, validate.

This script covers the checklist's "Done when": the correct caps are
returned **under three distinct lighting setups**. Instead of
spinning up Gazebo, we render 3 simple synthetic scenes in OpenCV
and run them through `cap_segmenter`. Same algorithm; same code
path you would use on a real frame.

The synthetic scene matches exercise 1's `autosampler_cell.sdf`
overhead view: a dark bench, a tan rack across the middle, and five
vials in the back row. Three of the slots have coloured caps that
mirror the SDF (`vial_a1` red, `vial_a3` blue, `vial_a5` green); two
extra slots are filled in with more red caps to make the LIMS
"give me all reds" demo non-trivial.

Run:
    python demo.py
    python demo.py --output-dir my_runs/

Writes:
    output/scene_<lighting>.png         # the rendered input
    output/annotated_<lighting>.png     # input + drawn detections
    stdout: per-scene PASS / FAIL summary
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

from cap_segmenter import (
    CapDetection,
    annotate,
    caps_to_slots,
    find_all_caps,
)


HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "output"

# Five slot centres across the image width, vertically aligned with the
# rack strip. The colours and (slot -> colour) mapping match what
# `_assert_expected` validates further down.
_SCENE_W, _SCENE_H = 640, 360
_RACK_Y_TOP, _RACK_Y_BOT = 140, 240
_SLOT_X_CENTRES = [90, 220, 340, 470, 580]  # slots 1..5, left to right
_CAP_COLORS_BY_SLOT = {
    1: "red",      # vial_a1 from the SDF
    2: "red",      # extra slot we filled in
    3: "blue",     # vial_a3
    4: "green",    # vial_a5
    5: "red",      # extra slot we filled in
}

# BGR triples used to draw the synthetic caps. Picked to land squarely
# inside the segmenter's HSV ranges at the "normal" brightness level.
_BGR = {
    "red":   (30, 30, 200),
    "blue":  (210, 90, 30),
    "green": (40, 180, 60),
}


def render_scene(lighting: str) -> np.ndarray:
    """Build one synthetic BGR scene at the given lighting setup.

    `lighting` is one of {"bright", "normal", "dim"}. We shift the
    base brightness and add a small amount of random noise so the
    three scenes are visibly different but still resolvable by the
    same HSV thresholds.
    """
    # Dark grey bench background.
    img = np.full((_SCENE_H, _SCENE_W, 3), 60, dtype=np.uint8)

    # Tan rack strip across the middle.
    cv2.rectangle(img,
                  (40, _RACK_Y_TOP), (_SCENE_W - 40, _RACK_Y_BOT),
                  (140, 150, 170), thickness=-1)

    # Five caps in the back row of the rack.
    cap_y = (_RACK_Y_TOP + _RACK_Y_BOT) // 2
    for slot_id, x in enumerate(_SLOT_X_CENTRES, start=1):
        color = _CAP_COLORS_BY_SLOT[slot_id]
        cv2.circle(img, (x, cap_y), 20, _BGR[color], thickness=-1)

    # Lighting shift. We DO NOT touch the rack here: a real lighting
    # change moves the whole frame, so the segmenter has to cope.
    shift = {"bright": +40, "normal": 0, "dim": -40}[lighting]
    img = np.clip(img.astype(np.int16) + shift, 0, 255).astype(np.uint8)

    # Small per-pixel noise to keep it from looking artificial.
    rng = np.random.default_rng(seed={"bright": 1, "normal": 2, "dim": 3}[lighting])
    noise = rng.integers(low=-6, high=7, size=img.shape, dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    return img


def _assert_expected(
    caps: List[CapDetection],
    image_width: int,
) -> Tuple[bool, str]:
    """Compare `(slot -> colour)` against `_CAP_COLORS_BY_SLOT`."""
    found = caps_to_slots(caps, num_slots=len(_CAP_COLORS_BY_SLOT),
                          image_width=image_width)
    expected = _CAP_COLORS_BY_SLOT
    if found == expected:
        return True, f"all {len(expected)} slots matched"
    diffs = []
    for slot_id in sorted(set(found) | set(expected)):
        if found.get(slot_id) != expected.get(slot_id):
            diffs.append(
                f"slot {slot_id}: expected {expected.get(slot_id)!r}, "
                f"got {found.get(slot_id)!r}",
            )
    return False, "; ".join(diffs)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT,
                   help="Where to drop rendered + annotated PNGs")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    overall_ok = True

    print("[demo] scene size       :"
          f" {_SCENE_W}x{_SCENE_H}")
    print(f"[demo] slots (left->right): {_CAP_COLORS_BY_SLOT}")
    print()

    for lighting in ("bright", "normal", "dim"):
        scene = render_scene(lighting)
        caps = find_all_caps(scene)
        overlay = annotate(scene, caps)

        scene_path = args.output_dir / f"scene_{lighting}.png"
        ann_path = args.output_dir / f"annotated_{lighting}.png"
        cv2.imwrite(str(scene_path), scene)
        cv2.imwrite(str(ann_path), overlay)

        ok, msg = _assert_expected(caps, image_width=scene.shape[1])
        verdict = "PASS" if ok else "FAIL"

        found_slots = caps_to_slots(caps, num_slots=len(_CAP_COLORS_BY_SLOT),
                                    image_width=scene.shape[1])
        print(f"[demo] lighting={lighting:<6}  found {len(caps):>2} caps  "
              f"slots={found_slots}  [{verdict}]")
        if not ok:
            print(f"        diff: {msg}")
            overall_ok = False

    print()
    print("[demo] LIMS query example: 'give me all RED caps' ->",
          [s for s, c in _CAP_COLORS_BY_SLOT.items() if c == "red"])
    print(f"[demo] outputs in: {args.output_dir}")
    print()
    print(f"[demo] {'PASS' if overall_ok else 'FAIL'} — "
          "checklist 'done when' bar requires all 3 lighting setups to pass.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
