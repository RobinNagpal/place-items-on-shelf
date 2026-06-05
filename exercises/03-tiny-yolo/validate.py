"""Evaluate a fine-tuned YOLOv8 checkpoint on the held-out test split.

Reads `best.pt` produced by train.py, runs Ultralytics' built-in val
loop on the `test:` split declared in `dataset.yaml`, and prints
mAP@0.5 (overall and per class). Exits non-zero if mAP@0.5 is below
the checklist's "Done when" bar of 0.70.

Run:
    python validate.py
    python validate.py --weights runs/detect/autosampler_yolov8n/weights/best.pt
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from ultralytics import YOLO


HERE = Path(__file__).resolve().parent
DATA_YAML = HERE / "dataset.yaml"

# Checklist item 3, "Done when": mAP@0.5 above 0.7 on a held-out set.
MIN_MAP50 = 0.70


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--weights",
        default="runs/detect/autosampler_yolov8n/weights/best.pt",
        help="Path to the trained checkpoint",
    )
    p.add_argument("--imgsz", type=int, default=640,
                   help="Image size used for inference (match training)")
    p.add_argument("--device", default="0",
                   help='Device: "0" for first GPU, "cpu" for CPU')
    p.add_argument("--split", default="test",
                   choices=["val", "test"],
                   help="Which dataset split to score against")
    return p.parse_args()


def main() -> int:
    args = parse_args()

    weights_path = Path(args.weights)
    if not weights_path.exists():
        # Friendly hint instead of a torch traceback when the path is
        # wrong (commonest beginner mistake on this exercise).
        print(f"[validate] checkpoint not found: {weights_path}", file=sys.stderr)
        print("[validate] run train.py first, or pass --weights <path>",
              file=sys.stderr)
        return 2

    model = YOLO(str(weights_path))

    # `val()` returns a `Results` object holding per-class and
    # aggregate metrics. We do NOT pass conf= / iou= — the defaults
    # (0.001 conf, 0.6 NMS IoU) are the standard COCO-style settings
    # used to compare against published numbers.
    metrics = model.val(
        data=str(DATA_YAML),
        split=args.split,
        imgsz=args.imgsz,
        device=args.device,
    )

    # `metrics.box.map50` is the headline number — mean Average
    # Precision at IoU=0.5, averaged over all classes.
    overall_map50 = float(metrics.box.map50)
    overall_map = float(metrics.box.map)   # mAP@0.5:0.95 — stricter

    print()
    print(f"[validate] split           = {args.split}")
    print(f"[validate] mAP@0.5         = {overall_map50:.3f}")
    print(f"[validate] mAP@0.5:0.95    = {overall_map:.3f}")
    print(f"[validate] bar (mAP@0.5)   = {MIN_MAP50:.2f}")
    print()

    # Per-class breakdown — useful to see WHICH class is dragging
    # the average down (cap_red is the usual suspect since it shares
    # all features with `vial`).
    names = model.names  # dict {0: "vial", 1: "empty_slot", ...}
    per_class = metrics.box.maps  # numpy array of mAP@0.5:0.95 per class
    print("[validate] per-class mAP@0.5:0.95")
    for class_id, score in enumerate(per_class):
        print(f"           {class_id:>2}  {names[class_id]:<12}  {float(score):.3f}")

    if overall_map50 < MIN_MAP50:
        print()
        print(f"[validate] FAIL — mAP@0.5 {overall_map50:.3f} < {MIN_MAP50:.2f}")
        return 1

    print()
    print(f"[validate] PASS — mAP@0.5 {overall_map50:.3f} >= {MIN_MAP50:.2f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
