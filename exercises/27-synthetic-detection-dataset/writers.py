"""Serialise rendered frames + annotations to disk in the formats
listed in ``docs/synthetic-data/features/01-detection-images-and-masks.md``:

- YOLO labels  -> one ``.txt`` per image, normalised xywh, one box per line.
- COCO JSON   -> one big ``annotations.json`` with images, categories,
                 and polygon segmentations. Reads cleanly in Ultralytics,
                 Detectron2, MMDetection.
- PNG masks   -> one binary PNG per object per frame. Used by Mask R-CNN
                 pipelines that want per-instance pixel masks.

Plus a ``dataset.yaml`` so ``yolo train data=dataset.yaml`` works out of
the box.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

import numpy as np
from PIL import Image

from render import CLASS_NAMES, IMG_H, IMG_W, Annotation


def write_image(rgb: np.ndarray, path: Path) -> None:
    """Save the RGB frame as a PNG."""
    Image.fromarray(rgb).save(path)


def write_yolo_labels(annotations: Iterable[Annotation], path: Path) -> None:
    """Write Ultralytics-format labels: ``class cx cy w h`` (all normalised)."""
    lines: List[str] = []
    for ann in annotations:
        x0, y0, x1, y1 = ann.bbox_xyxy
        cx = ((x0 + x1) / 2.0) / IMG_W
        cy = ((y0 + y1) / 2.0) / IMG_H
        w = (x1 - x0) / IMG_W
        h = (y1 - y0) / IMG_H
        lines.append(f"{ann.class_id} {cx:.6f} {cy:.6f} {w:.6f} {h:.6f}")
    path.write_text("\n".join(lines) + ("\n" if lines else ""))


def write_instance_masks(annotations: Iterable[Annotation], frame_name: str, masks_dir: Path) -> None:
    """One PNG per object — ``<frame>_<idx>_<class>.png``, white on black."""
    for idx, ann in enumerate(annotations):
        out = masks_dir / f"{frame_name}_{idx:02d}_{CLASS_NAMES[ann.class_id]}.png"
        Image.fromarray(ann.mask).save(out)


def _polygon_from_disk_mask(mask: np.ndarray, num_pts: int = 16) -> List[float]:
    """Approximate a disk-shaped mask with a regular polygon for COCO.

    We rendered every object as a disk, so we already know it's
    circular — no need to run a contour finder. ``num_pts`` controls
    how round the COCO polygon looks (16 is plenty for a 12 mm vial
    at this resolution).
    """
    x0, x1 = np.where(mask.any(axis=0))[0][[0, -1]]
    y0, y1 = np.where(mask.any(axis=1))[0][[0, -1]]
    cx, cy = (x0 + x1) / 2.0, (y0 + y1) / 2.0
    r = max((x1 - x0), (y1 - y0)) / 2.0
    pts: List[float] = []
    for i in range(num_pts):
        theta = 2.0 * np.pi * i / num_pts
        pts.append(float(cx + r * np.cos(theta)))
        pts.append(float(cy + r * np.sin(theta)))
    return pts


def write_coco(
    frame_names: List[str],
    per_frame_annotations: List[List[Annotation]],
    out_path: Path,
) -> None:
    """One COCO JSON for the whole dataset.

    The structure matches what Ultralytics, MMDetection, and Detectron2
    all read: ``images``, ``annotations``, ``categories``.
    """
    coco = {
        "info": {
            "description": "Synthetic HPLC-autosampler detection dataset",
            "version": "1.0",
            "source": "exercises/24-synthetic-detection-dataset",
        },
        "categories": [
            {"id": i, "name": name, "supercategory": "lab_consumable"}
            for i, name in enumerate(CLASS_NAMES)
        ],
        "images": [],
        "annotations": [],
    }
    ann_id = 1
    for img_id, (name, anns) in enumerate(zip(frame_names, per_frame_annotations), start=1):
        coco["images"].append({
            "id": img_id,
            "file_name": f"images/{name}.png",
            "width": IMG_W,
            "height": IMG_H,
        })
        for ann in anns:
            x0, y0, x1, y1 = ann.bbox_xyxy
            w, h = x1 - x0, y1 - y0
            coco["annotations"].append({
                "id": ann_id,
                "image_id": img_id,
                "category_id": ann.class_id,
                "bbox": [x0, y0, w, h],          # COCO uses xywh (top-left + size)
                "area": int(w * h),
                "iscrowd": 0,
                "segmentation": [_polygon_from_disk_mask(ann.mask)],
                "attributes": ann.attributes,
            })
            ann_id += 1
    out_path.write_text(json.dumps(coco, indent=2))


def write_yolo_dataset_yaml(dataset_root: Path) -> None:
    """Write a tiny ``dataset.yaml`` so ``yolo train`` finds the data."""
    yaml = (
        f"path: {dataset_root.resolve()}\n"
        "train: images\n"
        "val: images\n"
        "names:\n"
    )
    for i, name in enumerate(CLASS_NAMES):
        yaml += f"  {i}: {name}\n"
    (dataset_root / "dataset.yaml").write_text(yaml)
