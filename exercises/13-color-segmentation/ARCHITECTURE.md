# Architecture — 13 Colour segmentation (no ML)

## Folder tree

```
13-color-segmentation/
├── README.md              # concept + workflow + autosampler tie-in
├── ARCHITECTURE.md        # this file
├── IMPLEMENTATION_NOTES.md# why HSV, why CLOSE, picking thresholds, failure modes
├── requirements.txt       # opencv-python + numpy
├── cap_segmenter.py       # core library: find_caps, find_all_caps, caps_to_slots, annotate
├── demo.py                # synthesize 3 lit scenes, run, validate, write PNGs
├── .gitignore             # ignore output/ and __pycache__/
└── output/                # demo writes scene_<lighting>.png + annotated_<lighting>.png
    (created at runtime; not in git)
```

The whole exercise is **two Python files** — one library and one
runnable demo. No ROS, no Gazebo, no model weights, no dataset.

## Per-file responsibility

| File | Owns |
|---|---|
| [`cap_segmenter.py`](cap_segmenter.py) | The HSV thresholds (`CAP_HSV_RANGES`), the area bounds (`MIN_AREA_PX`, `MAX_AREA_PX`), the morphological kernel, the `CapDetection` dataclass, and four public functions: `find_caps`, `find_all_caps`, `caps_to_slots`, `annotate`. Everything an outside caller (e.g. a ROS node) needs to import. |
| [`demo.py`](demo.py) | Renders three synthetic BGR scenes at three brightness levels, runs the segmenter on each, asserts the resulting `{slot: color}` matches `_CAP_COLORS_BY_SLOT`, and writes PNGs to `output/`. This is the "Done when 3 lighting setups pass" check. |
| [`requirements.txt`](requirements.txt) | Pins `opencv-python>=4.8` and `numpy>=1.24`. No other deps. |
| `.gitignore` | Keeps `output/` and `__pycache__/` out of git. |

## How the files interact at runtime

```
                cap_segmenter.py
                ────────────────
                CAP_HSV_RANGES, MIN_AREA_PX, MAX_AREA_PX
                @dataclass CapDetection
                def find_caps(bgr, color)
                def find_all_caps(bgr)
                def caps_to_slots(caps, num_slots, image_width)
                def annotate(bgr, caps)
                        ▲             ▲
                        │             │ imports
                        │             │
                        │       demo.py
                        │       ──────
                        │       render_scene(lighting)  -> synthetic BGR
                        │       main():
                        │         for lighting in {bright, normal, dim}:
                        │            bgr = render_scene(lighting)
                        ├──────────  caps = find_all_caps(bgr)
                        │            overlay = annotate(bgr, caps)
                        │            slots = caps_to_slots(caps, 5, bgr.shape[1])
                        │            check slots == ground truth -> PASS / FAIL
                        │
                  (no other consumers — by design)
                        ▼
                  output/scene_*.png
                  output/annotated_*.png
                  exit 0 / 1
```

The handoff between the two files is **the public functions of
`cap_segmenter`**. `demo.py` calls them; nothing else in the
project does yet. When exercise 14 / 36+ wire this into ROS, they
will import the same functions — the algorithm stays in
`cap_segmenter.py` so the ROS node is just plumbing.

## Data flow inside one frame

```
input BGR uint8 (H, W, 3)
      │   cv2.cvtColor(BGR -> HSV)
      ▼
HSV uint8 (H, W, 3)
      │   for each colour: cv2.inRange(hsv, lo, hi)  -> uint8 (H, W) binary
      │   OR the per-colour masks where the colour wraps (red has 2)
      ▼
binary mask (H, W) uint8 {0, 255}
      │   cv2.morphologyEx(mask, MORPH_CLOSE, 5x5 kernel)
      ▼
cleaned mask (H, W)
      │   cv2.connectedComponentsWithStats(mask, connectivity=8)
      ▼
(num_labels, label_image, stats[N,5], centroids[N,2])
      │   filter:  MIN_AREA_PX <= stats[i, CC_STAT_AREA] <= MAX_AREA_PX
      ▼
list[CapDetection]
```

The slot dictionary is then a one-line bucket-by-x-band over that
list — see `caps_to_slots` in `cap_segmenter.py`.

## Dependencies (external to this folder)

- **`opencv-python` (or `opencv-python-headless`)** — provides
  `cvtColor`, `inRange`, `morphologyEx`,
  `connectedComponentsWithStats`, `rectangle`, `circle`, `putText`.
- **`numpy`** — array container under every OpenCV call.

No torch, no ultralytics, no ROS, no `cv_bridge`. The whole library
is portable Python that runs anywhere OpenCV does.

## What this exercise does NOT touch

| Subsystem | Where it lives |
|-----------|-----------------|
| Gazebo world / cap colours in SDF | exercise 1 |
| YOLO detector training | exercise 3 |
| Live ROS camera subscription pattern | exercise 4 |
| Instance segmentation (pixel masks) | exercise 7 |
| 3D centroid (depth) | exercise 8 |
| Barcode reading | exercise 14 |
| Hand-eye calibration (pixels -> robot frame) | exercises 11 + 12 |

This exercise is **pure perception, single frame, no learning**.
It was kept narrow on purpose: the next exercise that needs a live
camera feed (any of items 14, 36-40) will subscribe to the same
ROS topic exercise 4 uses, call `find_all_caps`, and publish the
result. Nothing inside `cap_segmenter.py` will need to change.
