# 27 — Architecture

## Folder tree

```
27-synthetic-detection-dataset/
├── README.md                # high-level overview for a beginner
├── ARCHITECTURE.md          # this file — per-file responsibility
├── IMPLEMENTATION_NOTES.md  # engineering choices and trade-offs
├── requirements.txt         # numpy, pillow
├── scene.py                 # procedural scene description (no pixels)
├── render.py                # rasterise a scene to RGB + masks
├── writers.py               # serialise to YOLO + COCO + PNG masks
├── generate.py              # main entry — loop, save, write metadata
├── verify.py                # re-read the dataset, check every label
└── .gitignore               # output/ stays untracked
```

`output/` is created at runtime by `generate.py`. It is `.gitignore`'d
so committed checkouts stay light — every contributor can regenerate
it locally.

## Separation of concerns

The four code files split the work along the dimensions a future
contributor will want to change independently:

| You want to … | Edit |
|---|---|
| change rack geometry, slot count, or cap palette | `scene.py` |
| change pixel resolution, colours, randomisation knobs, or noise | `render.py` |
| add a new label format (e.g. TFDS, RLDS) | `writers.py` |
| change the dataset size, seed, or output path | `generate.py` |
| add a stricter validity check | `verify.py` |

## File-by-file

### `scene.py` — procedural scene description

Pure data, no pixels. Owns *what* exists in the world.

- **`RACK_ROWS = 6`, `RACK_COLS = 9`** — 54-slot autosampler variant.
- **`SLOT_SPACING_MM = 14.0`** — centre-to-centre distance (matches
  the HPLC autosampler reference geometry in `docs/hplc-autosamplers/`).
- **`VIAL_DIAM_MM = 12.0`, `CAP_DIAM_MM = 10.0`** — standard 2 mL vial.
- **`WORKSPACE_W_MM`, `WORKSPACE_H_MM`** — the field of view of the
  overhead camera, in mm.
- **`CAP_COLORS`** — five RGB tuples (red / blue / green / yellow /
  white), matching the colour-coded subsets a real LIMS uses.
- **`Vial`, `EmptySlot`, `Distractor`** — three small dataclasses,
  one per object type.
- **`Scene`** — the full description: rack origin, vials, empty
  slots, distractors. Helper methods `slot_center_mm` and
  `rack_bounds_mm` keep the trigonometry out of `render.py`.
- **`random_scene(rng, fill_prob, rack_jitter_mm, max_distractors)`**
  — one scene draw. Procedural-scene method lives here.

Depended on by `render.py`, `generate.py`.

### `render.py` — rasterise a scene

Owns *how* the scene looks.

- **`IMG_W = 640`, `IMG_H = 480`** — camera resolution.
- **`PX_PER_MM = 4.0`** — keeps a 12 mm vial at ~48 px diameter,
  comfortable for a YOLO grid cell at stride 8.
- **`CLASS_NAMES = ["vial", "empty_slot"]`**, **`CLASS_VIAL = 0`**,
  **`CLASS_EMPTY_SLOT = 1`**.
- **`Annotation`** — dataclass: `class_id`, `bbox_xyxy`, `mask`,
  `attributes` (cap colour, slot id). One per detected object.
- **`RenderResult`** — `rgb` array + list of `Annotation`s.
- **`_disk_mask(cx, cy, r_px)`** — builds an `(IMG_H, IMG_W)` binary
  mask in two lines with `np.ogrid`. Reused for every vial and slot.
- **`render(scene, rng)`** — the only public function. Draws the
  background, the rack, the distractors, the empty slots, then the
  vials on top. Applies brightness scaling, an optional Gaussian
  blur, and Gaussian RGB noise. Returns the `RenderResult`.

Depended on by `writers.py` (for `IMG_W` / `IMG_H` / `CLASS_NAMES`),
`generate.py`, `verify.py`.

### `writers.py` — serialise to disk

Owns *how the labels are written*. One function per format.

- **`write_image(rgb, path)`** — RGB PNG.
- **`write_yolo_labels(annotations, path)`** — one `.txt` per image,
  Ultralytics format (`class cx cy w h`, all normalised to `[0, 1]`).
- **`write_instance_masks(annotations, frame_name, masks_dir)`** —
  one binary PNG per object. Filename pattern
  `<frame>_<idx>_<class>.png`, where `<idx>` matches the order in
  the annotations list (so `verify.py` can re-pair them).
- **`_polygon_from_disk_mask(mask)`** — approximates each disk with a
  16-vertex polygon for COCO's `segmentation` field. We rendered
  every object as a disk, so no contour finder is needed.
- **`write_coco(frame_names, per_frame_annotations, out_path)`** —
  one dataset-wide `annotations.json`. Includes `info`, `categories`,
  `images`, `annotations`. Polygon segmentations, COCO `bbox` xywh
  ordering, `iscrowd=0`, custom `attributes` block.
- **`write_yolo_dataset_yaml(dataset_root)`** — Ultralytics-style
  config so `yolo train data=output/dataset.yaml` finds the data.

Depended on by `generate.py`.

### `generate.py` — main entry

Orchestrates everything.

- CLI: `--n` (frame count, default 100), `--seed` (RNG seed),
  `--out` (output folder), `--fill-prob` (per-slot fill probability).
- Creates `output/{images,labels,masks}` once.
- For each frame: `random_scene` -> `render` -> write image + YOLO
  labels + per-instance masks. Accumulates annotations for the COCO
  dump at the end.
- Writes `annotations.json`, `dataset.yaml`, and a small
  `metadata.json` describing which knobs were used. The customer can
  read `metadata.json` to know which randomisation methods produced
  the data.

### `verify.py` — sanity-check the dataset

The "Done when" gate. Re-reads what `generate.py` wrote and:

1. Parses every YOLO `.txt` back into pixel-space boxes.
2. Confirms each box is fully inside the image and has positive area.
3. Matches each YOLO box against its corresponding per-instance mask
   PNG and computes the bbox IoU. Anything below 0.95 fails.
4. Confirms the COCO image / annotation counts match the YOLO files.
5. Draws one overlay (boxes on top of the rendered frame) so a human
   can eyeball one sample.

Prints a single PASS / FAIL line and exits with that status code.

Depended on by nothing — verification is terminal.

## Data flow

```
scene.py  ◄──── generate.py ────►  render.py
                                       │
                                       ▼  RenderResult(rgb, annotations)
                                       │
                                  writers.py
                                       │
                                       ▼
              output/images/{*.png},  output/labels/{*.txt}
              output/masks/{*.png},   output/annotations.json
              output/dataset.yaml,    output/metadata.json
                                       │
                                       ▼
                                  verify.py
                                       │
                                       ▼
                            PASS / FAIL  (exit 0 / 1)
```

No ROS, no Gazebo, no Isaac Sim. The whole pipeline is in-process
Python — by design, so the synthetic-data concepts are not hidden
behind simulator setup. The way you scale this up to a real
production pipeline is to swap `render.py` for an Isaac Sim
Replicator script; the rest of the file structure (procedural scene
description, label writers, verify gate) stays exactly the same.
