"""End-to-end synthetic-dataset generation.

Run with ``python generate.py`` (or ``python generate.py --n 50`` for
a quicker smoke test). Produces ``output/`` containing:

    output/
    ├── images/         scene_0001.png ...
    ├── labels/         scene_0001.txt   (YOLO)
    ├── masks/          scene_0001_00_vial.png ...
    ├── annotations.json (COCO)
    ├── dataset.yaml     (Ultralytics)
    └── metadata.json    (which knobs were used, for the customer)

The whole 100-frame default run takes ~5 seconds on a laptop CPU.
"""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

import numpy as np

from render import render
from scene import random_scene
from writers import (
    write_coco,
    write_image,
    write_instance_masks,
    write_yolo_dataset_yaml,
    write_yolo_labels,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=100, help="number of frames to generate")
    parser.add_argument("--seed", type=int, default=0, help="RNG seed (reproducible runs)")
    parser.add_argument("--out", type=Path, default=Path(__file__).parent / "output")
    parser.add_argument("--fill-prob", type=float, default=0.7,
                        help="per-slot probability of containing a vial")
    args = parser.parse_args()

    out: Path = args.out
    (out / "images").mkdir(parents=True, exist_ok=True)
    (out / "labels").mkdir(parents=True, exist_ok=True)
    (out / "masks").mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(args.seed)
    frame_names = []
    per_frame_annotations = []
    n_objects = 0
    t0 = time.time()

    for i in range(args.n):
        name = f"scene_{i:04d}"
        scene = random_scene(rng, fill_prob=args.fill_prob)
        result = render(scene, rng)
        write_image(result.rgb, out / "images" / f"{name}.png")
        write_yolo_labels(result.annotations, out / "labels" / f"{name}.txt")
        write_instance_masks(result.annotations, name, out / "masks")
        frame_names.append(name)
        per_frame_annotations.append(result.annotations)
        n_objects += len(result.annotations)

    write_coco(frame_names, per_frame_annotations, out / "annotations.json")
    write_yolo_dataset_yaml(out)

    metadata = {
        "frames": args.n,
        "seed": args.seed,
        "fill_prob": args.fill_prob,
        "total_objects": n_objects,
        "methods_used": ["domain_randomisation", "procedural_scenes", "sensor_noise_modelling"],
        "image_size_px": [640, 480],
        "px_per_mm": 4.0,
        "classes": ["vial", "empty_slot"],
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2))

    dt = time.time() - t0
    print(f"[generate] wrote {args.n} frames, {n_objects} objects in {dt:.1f} s")
    print(f"[generate] output -> {out.resolve()}")


if __name__ == "__main__":
    main()
