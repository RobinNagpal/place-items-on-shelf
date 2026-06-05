"""Fine-tune YOLOv8-nano on the synthetic autosampler dataset.

The dataset itself does not exist yet — exercise 5 (auto-label from
Gazebo ground truth) is the planned source. This script assumes the
images and labels are already laid out in YOLO format under the path
declared in `dataset.yaml`.

Run:
    python train.py
or with overrides:
    python train.py --epochs 30 --imgsz 512 --batch 8

Outputs land in `runs/detect/<run_name>/`. The best checkpoint is
`runs/detect/<run_name>/weights/best.pt` — that file is what
validate.py loads next.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from ultralytics import YOLO


# Resolve dataset.yaml next to this script — keeps the command short
# and lets you run train.py from any working directory.
HERE = Path(__file__).resolve().parent
DATA_YAML = HERE / "dataset.yaml"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    # YOLOv8-nano weights, pre-trained on COCO. Ultralytics downloads
    # them on first use. Swap to "yolov8s.pt" / "yolov8m.pt" for a
    # bigger model — same script works.
    p.add_argument("--weights", default="yolov8n.pt",
                   help="Starting checkpoint (default: COCO-pretrained nano)")
    p.add_argument("--epochs", type=int, default=50,
                   help="Number of training epochs")
    p.add_argument("--imgsz", type=int, default=640,
                   help="Image size in pixels (square)")
    p.add_argument("--batch", type=int, default=16,
                   help="Mini-batch size — drop to 8 on a small GPU")
    p.add_argument("--device", default="0",
                   help='Device: "0" for first GPU, "cpu" to force CPU')
    p.add_argument("--name", default="autosampler_yolov8n",
                   help="Sub-folder name under runs/detect/")
    return p.parse_args()


def main() -> None:
    args = parse_args()

    # Load the pretrained model. YOLO() handles both .pt files and
    # model names (e.g. "yolov8n") — same call.
    model = YOLO(args.weights)

    # train() runs the full loop: dataloader, optimiser, scheduler,
    # validation at the end of each epoch, and saves best.pt /
    # last.pt. Hyperparameters we do NOT pass keep their ultralytics
    # defaults (SGD, lr0=0.01, momentum=0.937, weight_decay=0.0005,
    # warmup 3 epochs, mosaic + mixup augmentation).
    model.train(
        data=str(DATA_YAML),
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=args.device,
        name=args.name,
        # Save best checkpoint every epoch, keep just the top one.
        save=True,
        save_period=-1,
        # No early stopping yet — the synthetic set is small, every
        # epoch helps. Turn this back on once we hit overfitting.
        patience=0,
    )


if __name__ == "__main__":
    main()
