"""End-to-end demo: five vials with five barcodes, each scanned by spinning.

Simulates one full pick-and-place cycle's worth of barcode reads:

  for vial in range(5):
      pick from source slot
      move to scan station
      spin_and_decode(...)                  <-- this exercise
      move to tray slot
      log (tray_slot -> barcode) to LIMS

We do not run MoveIt here; the focus is the scan step. For each of
the five vials we generate a QR code, paste it on a fake "vial" image
at one specific rotation angle, then ask `spin_and_decode` to find
that angle by trying every angle in turn. The test passes if all
five codes are read and the LIMS dict matches ground truth.

Run:
    python demo.py
    python demo.py --output-dir runs/

Writes:
    output/vial_<slot>_visible.png      # the angle where the QR was readable
    output/lims.csv                     # tray_slot,barcode  (one row per vial)
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path
from typing import Dict, List

import cv2
import numpy as np
import qrcode

from barcode_reader import DECODER_NAME, spin_and_decode


HERE = Path(__file__).resolve().parent
DEFAULT_OUT = HERE / "output"

# Five vials, five barcodes — mimics the "5 cubes with 5 different
# codes" "Done when" bar from checklist item 14.
VIAL_BARCODES: List[str] = [
    "B-2024-0117",
    "B-2024-0118",
    "B-2024-0119",
    "B-2024-0120",
    "B-2024-0121",
]

# The scan station sees a 320x320 frame. The vial is held vertically
# in the gripper, centred. Background is dark (camera baffles).
_FRAME_W, _FRAME_H = 320, 320

# spin_and_decode tries this many angles per vial. 12 steps = every
# 30 degrees; one full rotation covers the barcode no matter where
# it sits.
SPIN_STEPS = 12


def make_qr_image(text: str, side_px: int = 120) -> np.ndarray:
    """Render a QR code as a BGR numpy array."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(text)
    qr.make()
    pil = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    # qrcode -> PIL -> numpy: PIL is RGB, OpenCV is BGR.
    arr = np.array(pil)
    bgr = cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    return cv2.resize(bgr, (side_px, side_px), interpolation=cv2.INTER_AREA)


def _draw_vial(frame: np.ndarray) -> None:
    """Draw the static vial body + cap onto `frame`."""
    # Dark scan-station background.
    frame[:] = 30
    # Vial body — vertical rectangle, wide enough that the QR fits
    # fully on the (near-white) body with its quiet zone preserved.
    body_top, body_bot = 40, 280
    body_l,  body_r = _FRAME_W // 2 - 80, _FRAME_W // 2 + 80
    cv2.rectangle(frame, (body_l, body_top), (body_r, body_bot),
                  (220, 220, 225), thickness=-1)
    # Cap on top.
    cap_top = body_top - 18
    cv2.rectangle(frame, (body_l + 6, cap_top), (body_r - 6, body_top),
                  (40, 40, 200), thickness=-1)


def vial_frame_at(
    qr_bgr: np.ndarray,
    step: int,
    barcode_visible_at_step: int,
    num_steps: int = SPIN_STEPS,
) -> np.ndarray:
    """Render one scan-station view: BGR frame at rotation `step`.

    The barcode is only visible when the spin angle matches
    `barcode_visible_at_step` (and at the immediately-adjacent angle,
    to fake the "barcode is partially visible at +/- 30 degrees too"
    behaviour you would see in real life). At every other angle the
    vial body shows but no QR — the decoder fails.
    """
    frame = np.zeros((_FRAME_H, _FRAME_W, 3), dtype=np.uint8)
    _draw_vial(frame)

    # Map angle -> visibility. Treat the wrap-around (step 0 vs step
    # max_steps - 1) correctly.
    delta = abs(step - barcode_visible_at_step)
    delta = min(delta, num_steps - delta)
    if delta <= 1:
        # Paste the QR onto the vial body. Centred horizontally,
        # mid-height on the vial.
        qh, qw = qr_bgr.shape[:2]
        y0 = 80
        x0 = (_FRAME_W - qw) // 2
        frame[y0:y0 + qh, x0:x0 + qw] = qr_bgr

    return frame


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--output-dir", type=Path, default=DEFAULT_OUT,
                   help="Where to drop the per-vial visible-angle PNGs + LIMS CSV")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    print(f"[demo] decoder         : {DECODER_NAME}")
    print(f"[demo] spin steps      : {SPIN_STEPS} (every {360 // SPIN_STEPS} deg)")
    print(f"[demo] vials to scan   : {len(VIAL_BARCODES)}")
    print()

    # Choose which angle the barcode shows up at, per vial. We pick a
    # different angle for each one to prove the spin loop finds it
    # regardless of where it started.
    visible_angles = [0, 3, 6, 9, 11]  # spread across the 12 steps

    lims_log: Dict[int, str] = {}
    overall_ok = True

    for tray_slot, (truth_code, visible_step) in enumerate(
            zip(VIAL_BARCODES, visible_angles), start=1):
        qr = make_qr_image(truth_code)

        # The arm asks for one frame per wrist nudge.
        def provider(step: int, qr=qr, vis=visible_step) -> np.ndarray:
            return vial_frame_at(qr, step, vis)

        decoded, step_found = spin_and_decode(provider, max_steps=SPIN_STEPS)

        ok = decoded == truth_code
        verdict = "PASS" if ok else "FAIL"
        if decoded is None:
            print(f"[demo] tray slot {tray_slot}: TIMEOUT after {step_found} spins "
                  f"(expected {truth_code!r})  [{verdict}]")
        else:
            print(f"[demo] tray slot {tray_slot}: decoded {decoded!r} on spin "
                  f"step {step_found} (visibility was at {visible_step})  [{verdict}]")
            lims_log[tray_slot] = decoded
            # Save the frame that the arm actually saw when it decoded.
            cv2.imwrite(
                str(args.output_dir / f"vial_{tray_slot}_visible.png"),
                provider(step_found),
            )
        overall_ok = overall_ok and ok

    # Write the LIMS log — this is the artefact the autosampler controller
    # really produces. One row per vial, "(tray_slot, barcode)".
    lims_csv = args.output_dir / "lims.csv"
    with lims_csv.open("w", newline="") as fp:
        w = csv.writer(fp)
        w.writerow(["tray_slot", "barcode"])
        for slot in sorted(lims_log):
            w.writerow([slot, lims_log[slot]])

    print()
    print(f"[demo] LIMS log written to {lims_csv}")
    print(f"[demo] {len(lims_log)}/{len(VIAL_BARCODES)} vials successfully scanned")
    print()
    print(f"[demo] {'PASS' if overall_ok else 'FAIL'} — "
          "checklist 'done when' bar requires 5 codes -> 5 mappings.")
    return 0 if overall_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
