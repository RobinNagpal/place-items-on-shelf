# 27 — Synthetic detection dataset

A small, self-contained generator that produces a labelled detection
dataset for the HPLC autosampler scene — RGB images, per-instance
masks, YOLO labels, and a COCO JSON — entirely in Python. No Gazebo,
no Isaac Sim, no human labeler.

This is the **simplest possible implementation of Feature 1** from the
synthetic-data offering described in
[`../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../docs/synthetic-data/features/01-detection-images-and-masks.md).
It demonstrates three of the four methods listed in
[`../../docs/synthetic-data/how-we-generate-it.md`](../../docs/synthetic-data/how-we-generate-it.md):

- **Domain randomisation** — per-scene brightness, background tint,
  rack colour, slight blur, cap colours.
- **Procedural scenes** — every frame has a randomly jittered rack,
  randomly filled slots, and 0–3 distractor objects.
- **Sensor noise modelling** — Gaussian RGB noise on every frame.

Photo-real rendering needs a ray tracer (Isaac Sim, Blender Cycles,
Unreal). It is out of scope for a tiny self-contained exercise.

## What this exercise does, in plain English

A real ML team spends most of its time **labelling photos by hand**.
Synthetic data flips that around: the program **draws the scene
itself**, so it already knows the truth for every pixel. We dump that
truth in the same format the team's training code already reads.

For each scene the generator:

1. Picks a random rack position and a random subset of slots to fill.
2. Picks a random cap colour for each filled slot.
3. Sprinkles 0–3 distractor objects around the bench.
4. Renders the scene to one RGB image (640×480).
5. Writes the corresponding labels: one YOLO `.txt`, one PNG mask per
   object, and one COCO row per object.

After ``N`` scenes you have a dataset that drops straight into
Ultralytics YOLO, Detectron2, MMDetection, or any Mask R-CNN
pipeline.

```
   procedural scene             rasterised frame                labels
   (rack + vials + clutter)     (RGB, with DR + noise)          (YOLO + COCO + masks)
            │                           │                              │
            │  scene.py                 │  render.py                   │  writers.py
            ▼                           ▼                              ▼
   Scene(vials, empties,      RenderResult(rgb,            output/images/scene_XXXX.png
         distractors)               annotations)                  output/labels/scene_XXXX.txt
                                                                  output/masks/scene_XXXX_NN_*.png
                                                                  output/annotations.json (COCO)
                                                                  output/dataset.yaml     (Ultralytics)
```

## Quick answers (read this first)

**Why a top-down 2D render and not a 3D simulator?**
The HPLC autosampler camera is mounted overhead. A top-down render is
not a shortcut here — it is what the production camera actually
sees. Skipping a 3D sim keeps the exercise small (numpy + Pillow only)
without dropping any of the synthetic-data concepts. Going 3D is the
next step (Isaac Sim Replicator); the file structure stays the same.

**Where do the bounding boxes come from?**
They come from the geometry we drew. ``render.py`` builds a binary
mask for each vial / empty slot as a filled disk, then derives the
tight bbox from the mask. No image-processing step. That's the
"ground truth from the simulator" rule from
[`how-we-generate-it.md`](../../docs/synthetic-data/how-we-generate-it.md).

**Why two classes (``vial`` and ``empty_slot``) and not five?**
Two classes is enough to demonstrate the format and to drive
exercises 3 (tiny YOLO) and 4 (live YOLO on Gazebo). If you need
``cap_red`` as its own class, split ``vial`` by cap colour in
``render.py``'s ``Annotation.class_id`` assignment — one line.

**How does this tie into the rest of the curriculum?**
- **Exercise 3 (tiny YOLO)** — would normally need ~200 hand-labelled
  images. Point it at this dataset instead and you get 100× more
  data for free.
- **Exercise 5 (score detections)** — uses Gazebo model-state as
  ground truth. This exercise is the *other* half of that story:
  produce labels from the simulator instead of scoring detections
  against them.
- **Feature 1 in the sales pitch** — the actual product we ship to
  customers. This is the simplest end-to-end version.

## What is the workflow

```
generate.py            scene.py -> render.py -> writers.py
                       per scene, N times
                                ────────────────────────────►   output/
                                                                ├── images/         scene_XXXX.png
                                                                ├── labels/         scene_XXXX.txt (YOLO)
                                                                ├── masks/          scene_XXXX_NN_*.png
                                                                ├── annotations.json (COCO)
                                                                ├── dataset.yaml
                                                                └── metadata.json
                                                                         │
verify.py              re-read labels + masks                            ▼
                       check every box is inside the image,        PASS / FAIL
                       every (bbox, mask) pair has IoU >= 0.95,
                       and the COCO counts match
```

Each script is also runnable on its own — see
[`ARCHITECTURE.md`](ARCHITECTURE.md).

## What the libraries are doing

- **`numpy`** — random generators (`np.random.default_rng` gives
  reproducible streams), mask arithmetic (`np.ogrid` builds the disk
  masks in two lines), and the Gaussian noise sample.
- **`Pillow` (`PIL`)** — the rasteriser. We use `ImageDraw` to render
  the rack body, slots, vials, caps, and distractors, then
  `ImageFilter.GaussianBlur` for the optional slight blur.

No machine-learning libraries are pulled in for the dataset itself.
The customer trains on the output with whatever their pipeline uses
(Ultralytics, Detectron2, …).

## Inputs and outputs

| | Format | Example |
|---|---|---|
| **Input** — generator seed and frame count | CLI args | `python generate.py --n 100 --seed 0` |
| **Output** — one RGB frame per scene | PNG, 640×480 | `output/images/scene_0001.png` |
| **Output** — YOLO labels | `class cx cy w h` (normalised) | `0 0.500000 0.250000 0.075000 0.100000` |
| **Output** — COCO JSON | bbox + polygon segmentation + per-cap attributes | `output/annotations.json` |
| **Output** — instance masks | one PNG per object | `output/masks/scene_0001_03_vial.png` |
| **Output** — Ultralytics config | `dataset.yaml` | drops into `yolo train data=…` |
| **Output** — metadata | which knobs were used | `output/metadata.json` |

## Example run

```bash
# 1. install deps
pip install -r requirements.txt

# 2. generate 100 frames (~35 s on a laptop CPU)
python generate.py --n 100 --seed 0

# 3. verify the labels (re-reads everything, checks IoU vs masks)
python verify.py

# expected:
# [generate] wrote 100 frames, 5400 objects in 35.2 s
# [generate] output -> .../27-synthetic-detection-dataset/output
# [verify] frames: 100  objects: 5400
# [verify] COCO  : 100 images, 5400 annotations
# [verify] worst bbox-vs-mask IoU: 1.000
# [verify] out-of-image boxes  : 0
# [verify] low-IoU boxes (<.95): 0
# [verify] overlay written to .../output/verify_overlay.png
# [verify] PASS
```

Open `output/verify_overlay.png` to see the YOLO boxes drawn back on
top of the rendered scene — every vial should have a red outline,
every empty slot a blue outline, and nothing else.

## Done when

The checklist gate for this exercise is:

> Generate ≥ 100 frames with valid COCO + YOLO + per-instance masks,
> and every YOLO bounding box has IoU ≥ 0.95 against its corresponding
> mask (i.e. the labels actually match the pixels).

`verify.py` enforces all of that and prints `PASS` / `FAIL`.

## How this ties into other exercises

- **Exercise 3 (tiny YOLO)** — point `yolo train data=output/dataset.yaml`
  at this folder and skip the hand-labelling step entirely.
- **Exercise 5 (score detections vs Gazebo)** — the opposite end of
  the same pipeline: scoring instead of producing.
- **Exercise 7 (instance segmentation)** — the per-instance PNG masks
  in `output/masks/` feed YOLOv8-seg or Mask R-CNN training directly.
- **Exercise 14 (barcode reader)** — extend `render.py` to draw a QR
  code on each cap, then feed those images to the barcode reader.

## What this exercise is **not**

| Need | Where it is solved |
|------|--------------------|
| Photo-real ray-traced frames | Isaac Sim Replicator (out of scope) |
| Real depth / point-cloud labels | Feature 2 (separate exercise) |
| Sensor noise for non-camera sensors | Feature 5 (separate exercise) |
| Training a detector on the data | exercise 3 (tiny YOLO) |
| Closed-loop perception in Gazebo | exercise 4 |
