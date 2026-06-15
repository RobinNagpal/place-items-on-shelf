"""Sanity-check the generated dataset.

This is the "Done when" gate. We re-read what ``generate.py`` wrote
and confirm three things:

1. Every YOLO label parses cleanly into a box that lies inside the image.
2. Each YOLO box agrees with the corresponding per-instance mask
   (IoU >= 0.95). If the bbox and the mask disagree, one of them is
   wrong and the dataset is silently broken.
3. The COCO JSON has the same image / annotation count as we wrote.

Run with ``python verify.py [--out path/to/output]``. Prints a single
PASS/FAIL line.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from render import CLASS_NAMES, IMG_H, IMG_W


def _read_yolo_labels(path: Path):
    """Parse a YOLO label file into pixel-space (cls, x0, y0, x1, y1)."""
    boxes = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        cls, cx, cy, w, h = line.split()
        cls, cx, cy, w, h = int(cls), float(cx), float(cy), float(w), float(h)
        x0 = int(round((cx - w / 2) * IMG_W))
        y0 = int(round((cy - h / 2) * IMG_H))
        x1 = int(round((cx + w / 2) * IMG_W))
        y1 = int(round((cy + h / 2) * IMG_H))
        boxes.append((cls, x0, y0, x1, y1))
    return boxes


def _bbox_iou(a, b) -> float:
    """Standard pairwise IoU on two (x0, y0, x1, y1) boxes."""
    ax0, ay0, ax1, ay1 = a
    bx0, by0, bx1, by1 = b
    ix0, iy0 = max(ax0, bx0), max(ay0, by0)
    ix1, iy1 = min(ax1, bx1), min(ay1, by1)
    iw, ih = max(0, ix1 - ix0), max(0, iy1 - iy0)
    inter = iw * ih
    union = (ax1 - ax0) * (ay1 - ay0) + (bx1 - bx0) * (by1 - by0) - inter
    return inter / union if union > 0 else 0.0


def _mask_bbox(mask: np.ndarray):
    """Tight (x0, y0, x1, y1) of the non-zero pixels in a mask."""
    ys, xs = np.where(mask > 0)
    return (int(xs.min()), int(ys.min()), int(xs.max()), int(ys.max()))


def _draw_overlay(image_path: Path, boxes, out_path: Path) -> None:
    """Draw each YOLO box on top of the image and save to ``out_path``."""
    img = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(img)
    palette = {0: (255, 80, 80), 1: (80, 200, 255)}
    for cls, x0, y0, x1, y1 in boxes:
        draw.rectangle([(x0, y0), (x1, y1)], outline=palette.get(cls, (255, 255, 0)), width=2)
        draw.text((x0 + 2, y0 + 2), CLASS_NAMES[cls], fill=(0, 0, 0))
    img.save(out_path)


def verify(out_dir: Path) -> bool:
    images_dir = out_dir / "images"
    labels_dir = out_dir / "labels"
    masks_dir = out_dir / "masks"
    coco_path = out_dir / "annotations.json"

    frame_paths = sorted(images_dir.glob("*.png"))
    if not frame_paths:
        print(f"[verify] FAIL — no images found in {images_dir}")
        return False

    coco = json.loads(coco_path.read_text())
    n_coco_images = len(coco["images"])
    n_coco_anns = len(coco["annotations"])

    bad_boxes = 0
    bad_iou = 0
    total_objects = 0
    worst_iou = 1.0

    for frame_path in frame_paths:
        name = frame_path.stem
        boxes = _read_yolo_labels(labels_dir / f"{name}.txt")
        for cls, x0, y0, x1, y1 in boxes:
            # Box must be inside the image and have positive area.
            if not (0 <= x0 < x1 <= IMG_W and 0 <= y0 < y1 <= IMG_H):
                bad_boxes += 1
                continue
            total_objects += 1

        # Match each YOLO box against the matching instance mask file.
        # Filenames look like ``scene_0001_03_vial.png`` — index order
        # matches the order written by ``writers.write_instance_masks``.
        mask_paths = sorted(masks_dir.glob(f"{name}_*.png"))
        for box, mask_path in zip(boxes, mask_paths):
            cls, x0, y0, x1, y1 = box
            mask = np.asarray(Image.open(mask_path).convert("L"))
            mask_box = _mask_bbox(mask)
            iou = _bbox_iou((x0, y0, x1, y1), mask_box)
            if iou < worst_iou:
                worst_iou = iou
            if iou < 0.95:
                bad_iou += 1

    # Sample overlay so the user can eyeball one frame.
    overlay_path = out_dir / "verify_overlay.png"
    sample = frame_paths[0]
    _draw_overlay(sample, _read_yolo_labels(labels_dir / f"{sample.stem}.txt"), overlay_path)

    ok = (
        bad_boxes == 0
        and bad_iou == 0
        and n_coco_images == len(frame_paths)
        and n_coco_anns == total_objects
    )

    print(f"[verify] frames: {len(frame_paths)}  objects: {total_objects}")
    print(f"[verify] COCO  : {n_coco_images} images, {n_coco_anns} annotations")
    print(f"[verify] worst bbox-vs-mask IoU: {worst_iou:.3f}")
    print(f"[verify] out-of-image boxes  : {bad_boxes}")
    print(f"[verify] low-IoU boxes (<.95): {bad_iou}")
    print(f"[verify] overlay written to {overlay_path}")
    print(f"[verify] {'PASS' if ok else 'FAIL'}")
    return ok


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "output")
    args = parser.parse_args()
    ok = verify(args.out)
    raise SystemExit(0 if ok else 1)


if __name__ == "__main__":
    main()
