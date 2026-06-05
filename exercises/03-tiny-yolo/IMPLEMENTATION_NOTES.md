# Implementation notes — 03 Tiny YOLO

Engineering decisions that are not obvious from the code.

## Why YOLOv8-nano and not something else

We picked the smallest variant of a modern, well-supported family.

| Option                           | Why we passed |
|----------------------------------|---------------|
| **YOLOv5-nano**                  | Older, but Ultralytics now ships v8 with the same API and slightly better accuracy at the same parameter count. v5 wins only if you must avoid PyTorch ≥ 2.0. |
| **YOLOv8-small / -medium / -large** | More parameters, better mAP. We are accuracy-bound by *data*, not model capacity — a bigger model overfits the small synthetic set without helping. |
| **YOLOv9 / v10 / v11**           | Newer, faster, but the Ultralytics ecosystem and tutorials are still v8-dominant; tooling is more stable. Easy to switch later: change one string in `train.py`. |
| **Faster R-CNN, DETR, RT-DETR**  | Heavier two-stage / transformer detectors. Better mAP, but ~10× slower at inference on a Pi. Wrong fit for "tiny detector next to the arm". |
| **Mask R-CNN, YOLOv8-seg**       | Produce pixel masks instead of boxes. Different exercise (item 7). |

> Rule of thumb: pick the smallest model that clears the mAP bar.
> Scale up later only when a specific failure mode demands it.

## Why we fine-tune from COCO weights instead of training from scratch

`yolov8n.pt` carries 80-class COCO pretraining. Even though "vial"
and "rack" are not COCO classes, the **backbone features** the
network learned on COCO (edges, textures, shapes) transfer to our
synthetic frames. Fine-tuning converges in 50 epochs with ~200
images. Training from scratch on the same data would need 10×–100×
more epochs and would plateau at a worse mAP.

This is the standard recipe on every tiny dataset. The only time
you train from scratch is when your image statistics differ wildly
from natural images (e.g. medical X-rays, thermal cameras).

## Why these hyperparameters

`train.py` overrides only a handful of knobs. Everything else stays
at Ultralytics defaults.

| Knob       | Value | Why |
|------------|-------|-----|
| `epochs`   | 50    | Enough for the model to memorise 200 synthetic frames without obvious overfitting. Watch `results.csv` — if val loss climbs after epoch 40, drop to 30. |
| `imgsz`    | 640   | Default for YOLOv8 and what most tutorials show. Smaller (`512`, `416`) is faster but loses the small `cap_red` and `empty_slot` boxes (~5–10 px wide at 640). |
| `batch`    | 16    | Fits on a 6 GB GPU at `imgsz=640`. Drop to 8 on a Jetson AGX, or pass `--batch 8`. |
| `patience` | 0 (off) | Early stopping is unhelpful at 50 epochs on 200 images — the validation curve is noisy. Re-enable once the dataset grows. |

Defaults we **inherit silently** and rely on:

- `optimizer = SGD`, `lr0 = 0.01`, `momentum = 0.937`,
  `weight_decay = 0.0005`. Stable; matches the YOLOv5/v8 papers.
- Augmentations: **mosaic** (4-image collage), **mixup**,
  HSV jitter, random scale. Crucial for generalising to lighting and
  pose variation we did not bother to render explicitly.
- NMS: `conf=0.001` at val time, `iou=0.6`. These are COCO-standard.
  Do **not** raise `conf` at val — it inflates mAP artificially.

## Why we hold out a `test` split (not just `val`)

Ultralytics runs `val` at the end of every training epoch. That
means the val set sees the model many times across training and
implicitly drives early-stopping / checkpoint selection. mAP on
`val` is **optimistic**.

`test` is touched exactly once, by `validate.py`. That is the number
we trust for the "Done when ≥ 0.7" check.

20% / 80% is overkill for a 200-image set — 10% `val` + 10% `test`
+ 80% `train` is the layout `data/README.md` recommends.

## Why mAP@0.5 and not mAP@0.5:0.95

mAP@0.5 is the **looser, easier** metric: a box counts if its IoU
with ground truth is ≥ 0.5. mAP@0.5:0.95 (COCO-style) averages mAP
across IoU thresholds 0.5, 0.55, …, 0.95.

The checklist's 0.70 bar is mAP@0.5. We compute and print mAP@0.5:0.95
too, because the gap between the two tells you whether the boxes are
*correct but loose* (high mAP@0.5, low mAP@0.5:0.95) or simply
*missed* (both are low). That signal guides what to improve next:

- **Loose boxes, classes correct** → augment with stronger
  random scale / crop; add a few hand-tuned anchor priors.
- **Boxes correct, classes mixed** → look at the confusion matrix
  (Ultralytics writes one in `runs/detect/.../confusion_matrix.png`).
  Probably `vial` vs `cap_red` confusion; add more `cap_red` samples.

## Assumptions baked into the script

1. **The dataset path in `dataset.yaml` is relative to the dataset
   root, not the script.** Ultralytics resolves `path:` against the
   *current working directory* unless absolute. We use a relative
   `./data/synthetic_autosampler`; run the scripts from the exercise
   folder.
2. **Image files are `.jpg`.** Ultralytics accepts most formats, but
   `data/README.md` standardises on `.jpg` to keep the loader fast
   and the file sizes small.
3. **Labels are YOLO format, not COCO JSON.** Conversion is trivial
   but the auto-labeller in exercise 5 outputs YOLO directly, so we
   never store COCO JSON in this repo.
4. **GPU available (default `--device 0`).** CPU training works but
   takes ~20× longer; pass `--device cpu` to run on a laptop.

## Failure modes you will see in practice

- **`dataset not found` from Ultralytics** — `dataset.yaml`'s `path:`
  was resolved relative to the wrong CWD. Run `python train.py` from
  inside `exercises/03-tiny-yolo/`, or pass an absolute path.
- **mAP@0.5 plateaus at ~0.4** — almost always too little data. Go
  back to exercise 5 and render more frames before tuning anything
  in this folder.
- **mAP@0.5 high, mAP@0.5:0.95 very low** — boxes are roughly right
  but loosely fit. Increase `imgsz` to 800 or 960; or include
  `degrees=10` in `train.py` for small rotation augmentation.
- **`cap_red` mAP drops the average** — predictable. `cap_red` and
  `vial` share most pixels (the cap is on top of the vial). Either
  (a) raise the share of `cap_red` examples in the training set or
  (b) merge `cap_red` into `vial` and add a separate colour classifier
  on the cropped vial box — often cleaner.
- **Training loss diverges (`nan` from epoch 1)** — corrupt label
  file (negative width, out-of-range class id). Ultralytics prints
  the offending file path; fix and rerun.

## Why no live ROS code here

This exercise is *training* only. Bringing the model into ROS 2
(stream camera → inference → publish `BoundingBox2DArray`) is item 4
and lives in its own folder. Keeping the two separate means you can:

- Train on a workstation with a GPU.
- Copy a single `best.pt` to the robot Pi.
- Run inference in ROS from that one file.

That same boundary holds in real production setups — training is
offline, inference is online.

## Things to revisit later

- Switch the backbone to `yolov8s` or `yolov9c` once `data/`
  has > 1000 images. Bigger models start to help around that scale.
- Add `cap_blue` and `cap_green` once the LIMS-subset request is
  more than a v1 nice-to-have.
- Quantise `best.pt` to INT8 (item 6). Same `.pt` → `.onnx` → quant
  pipeline; that lands in its own folder.
- Replace the synthetic data with a small *real* set once we have
  hardware in front of a camera. mAP will drop on day one; that is
  the sim-to-real gap you read about — closing it is the entire
  point of items 5 / 11 / 12.
