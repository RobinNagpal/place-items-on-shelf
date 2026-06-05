# 03 — Tiny YOLO on a custom 5-class dataset

Implements checklist item **3** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Mapped onto the HPLC autosampler v1 cell defined in
[`../../docs/hplc-autosamplers/requirements/`](../../docs/hplc-autosamplers/requirements/).

This is the **first perception exercise** in the project. Until now
the arm has been moving with no idea what is on the bench. After this,
the arm knows: *"there is a vial in slot B3, the rack is roughly
here, the tray is roughly there."*

## What is YOLO (plain English)

**YOLO** stands for *"You Only Look Once"*. It is a family of neural
networks for **object detection** — pass it an RGB image, get back a
list of boxes, each labelled with a class name (`vial`, `cap_red`, …)
and a confidence number.

The "only look once" refers to the speed trick: traditional
detectors (R-CNN, etc.) ran one slow pass to *propose* regions and a
second pass to *classify* them. YOLO does it in **one** forward pass
through one network. That makes it fast enough to run on every
camera frame, even on a small Pi / Jetson next to the robot.

We use **YOLOv8-nano** (`yolov8n.pt`) from
[Ultralytics](https://docs.ultralytics.com/) — the smallest variant
in the v8 family, ~3 M parameters, ~6 MB on disk. Bigger variants
(`s`, `m`, `l`, `x`) exist; we pick `nano` because the autosampler
controller is a Pi 4 / Jetson Nano, not a workstation.

### How YOLOv8 sees an image, in one paragraph

The network slides over the image at three resolutions at once
(stride 8, 16, 32). At every grid cell at every resolution it
predicts a few candidate boxes (`x, y, w, h`), one objectness score,
and one class probability per class in our `names:` list. A
post-processing step called **NMS** (non-max suppression) collapses
overlapping boxes into the single best one. The output is the
`[x, y, w, h, conf, class_id]` rows you see in the validation report.

The five class IDs we train on are listed in [`dataset.yaml`](dataset.yaml).

## How the model knows what to detect

Only because **the labels tell it**. There is no magic. Each training
image has a `.txt` next to it listing every box and its class id:

```
0 0.21 0.18 0.04 0.10        # class 0 (vial)
4 0.21 0.13 0.03 0.03        # class 4 (cap_red)
```

The trainer learns "pixels that look like this go with class N". If
you never label a class, the trained model has no idea it exists.

### Single-class vs multi-class detection

| Mode               | When to use                                 | How to set up                                     |
|--------------------|---------------------------------------------|---------------------------------------------------|
| **Single-class**   | You only need *"is `X` here?"*               | One line under `names:` in `dataset.yaml`, label only that class in the `.txt` files. |
| **Multi-class**    | You need to tell several object types apart | Multiple lines under `names:`, label every class you care about. |

The same `train.py` and `validate.py` handle both — only the data
and `dataset.yaml` change. We picked **multi-class with 5 labels**
because one detector then answers three different questions per
frame (where is the rack, where is the tray, which slots are full),
which is cheaper than running three models.

> **Important:** if you cut the dataset down to one class but forget
> to update `dataset.yaml`, training crashes with a class-id
> mismatch. The two must stay in sync.

## Why YOLO is the right first perception step

Three reasons:

1. **Every later perception exercise needs "where are the things?"**
   - Item 4 streams YOLO live on the Gazebo camera feed.
   - Item 5 scores those detections against Gazebo ground truth.
   - Items 7–10 sharpen the answer (masks, depth, 6-DoF).
   - Item 14 reads the barcode of the vial YOLO found.
2. **It is the cheapest baseline.** A fine-tuned YOLOv8-nano on a
   small synthetic set is one `model.train()` call. Every fancier
   method later has to beat its mAP@0.5 to be worth the complexity.
3. **It runs on the same hardware as the arm.** Pixel masks (item 7)
   and large transformers (item 25 VLA) are heavier — we want the
   workhorse detector to leave headroom for the rest.

## The five classes (autosampler-specific)

| id | class        | what it is in the cell                                            | why we want it |
|----|--------------|-------------------------------------------------------------------|----------------|
| 0  | `vial`       | any capped 12 × 32 mm vial standing in a rack or tray slot         | "is the source slot full?" / "is the destination slot already loaded?" |
| 1  | `empty_slot` | an empty hole in either the 5×10 rack or the 10×10 tray            | tells the pick logic which source slots to skip and which target slots are free |
| 2  | `rack_edge`  | corners / outer edge of the **MicroSolv 50-position rack**        | coarse rack pose without ArUco — see item 10 for the precise version |
| 3  | `tray_edge`  | corners / outer edge of the **Agilent 100-position tray**          | coarse tray pose — same idea, destination side |
| 4  | `cap_red`    | red PP cap (and we can add `cap_blue`, `cap_green` later)         | colour-coded subsets ("load only the red caps next") — common LIMS request |

Class IDs come from
[`dataset.yaml`](dataset.yaml). One detector, one pass — enough to
drive the v1 pick-and-place script.

## Workflow

```
        Gazebo world (from exercise 1)
                 │
                 │  exercise 5 (auto-label from /gazebo/model_states)
                 ▼
        data/synthetic_autosampler/
          images/{train,val,test}/*.jpg
          labels/{train,val,test}/*.txt   (YOLO format)
                 │
                 │  train.py
                 ▼
        YOLOv8-nano  ──── fine-tune from COCO weights ────►  best.pt
                 │
                 │  validate.py  on the held-out `test` split
                 ▼
        mAP@0.5  ─── PASS (>= 0.70) ───►  exercise 4 (live on Gazebo camera)
                 │
                 └─── FAIL (< 0.70) ───►  more data / longer training / look at per-class breakdown
```

Inputs and outputs at a glance:

| Step | Reads                                                            | Writes                                                        |
|------|------------------------------------------------------------------|---------------------------------------------------------------|
| Train | `dataset.yaml`, `data/.../images/train`, `data/.../labels/train` | `runs/detect/<run_name>/weights/best.pt` and training plots   |
| Validate | `best.pt`, `dataset.yaml`, `data/.../{images,labels}/test`       | prints mAP@0.5, mAP@0.5:0.95, per-class breakdown; exit code  |

## How we measure it — what is mAP?

Built up in five steps:

1. **TP / FP / FN.** For one box, the model is right (**TP**) if it
   says "object here" *and* the real object is there *and* the
   boxes overlap enough. A false alarm is an **FP**. A missed
   object is an **FN**.
2. **Overlap = IoU.** Intersection-over-Union — overlapping area
   divided by combined area. `1.0` = same box, `0.0` = no overlap.
   The standard "match" cutoff is **IoU ≥ 0.5**.
3. **Precision** = correct boxes / boxes drawn. **Recall** = real
   objects found / real objects present.
4. Every box has a 0–1 **confidence**. Sweeping the confidence
   threshold from 0 to 1 produces a **precision-recall curve**.
   **AP** (Average Precision) for one class is the area under that
   curve.
5. **mAP** = mean AP across classes. **mAP@0.5** uses the 0.5 IoU
   cutoff; **mAP@0.5:0.95** averages mAP at IoU 0.5, 0.55, …, 0.95
   (stricter — punishes loose boxes).

Cheat sheet for reading a score:

| Score      | What it means                                       |
|------------|-----------------------------------------------------|
| 0.9 – 1.0  | Excellent.                                          |
| 0.7 – 0.9  | Good. Checklist "Done when" bar is here.            |
| 0.5 – 0.7  | Working, but expect mistakes.                       |
| < 0.5      | Unreliable — usually means too little training data.|

## What "Done when" means here

The checklist asks for **mAP@0.5 above 0.7 on a held-out test set**.

- `validate.py` prints `metrics.box.map50` (the headline number),
  `metrics.box.map` (the stricter mAP@0.5:0.95), and a **per-class**
  breakdown so we can see *which* class is dragging the average.
- The script exits non-zero if mAP@0.5 < 0.70, so it drops into CI
  later without extra wiring.

## Example run

```bash
# 1. install deps (one time)
pip install -r requirements.txt

# 2. make sure data/synthetic_autosampler/ exists in YOLO layout
#    (currently empty — exercise 5 fills it)

# 3. fine-tune
python train.py
# → runs/detect/autosampler_yolov8n/weights/best.pt

# 4. score on the held-out test split
python validate.py
# [validate] split           = test
# [validate] mAP@0.5         = 0.781
# [validate] mAP@0.5:0.95    = 0.532
# [validate] bar (mAP@0.5)   = 0.70
# [validate] per-class mAP@0.5:0.95
#             0  vial          0.611
#             1  empty_slot    0.498
#             2  rack_edge     0.522
#             3  tray_edge     0.515
#             4  cap_red       0.515
# [validate] PASS — mAP@0.5 0.781 >= 0.70
```

(Numbers above are illustrative — the dataset is not generated yet.)

## Using `best.pt` to predict on a new image

Training writes the network to a single `.pt` file (~6 MB for
YOLOv8-nano) under `runs/detect/<name>/weights/`. Inference is then
three lines:

```python
from ultralytics import YOLO

model = YOLO("runs/detect/autosampler_yolov8n/weights/best.pt")
results = model("scene.jpg")        # path, numpy image, or list

for box in results[0].boxes:
    cls  = int(box.cls[0])                # 0 = vial, 1 = empty_slot, ...
    conf = float(box.conf[0])             # 0.0 – 1.0 confidence
    xyxy = box.xyxy[0].tolist()           # [x1, y1, x2, y2] in pixels
    print(results[0].names[cls], conf, xyxy)
```

Sample output for one frame:

```
vial    0.93  [184, 322, 226, 414]
vial    0.88  [241, 320, 282, 413]
cap_red 0.81  [186, 324, 222, 358]
```

`conf` is the **0–1 confidence** for that specific box —
1.0 = "completely sure", 0.0 = "almost certainly not". Ultralytics
keeps boxes with `conf >= 0.25` by default at predict time. Save an
annotated image with `results[0].save("out.jpg")`.

That same `best.pt` is what exercise 4 will load inside a ROS 2
node to run on every Gazebo camera frame.

## What this exercise is **not**

YOLO answers "where roughly" — not "exactly where in 3D" and not
"what does the label say". Each of those is a later checklist item:

| Need                     | Where it is solved             |
|--------------------------|--------------------------------|
| Pixel-accurate masks     | item 7 (instance segmentation) |
| 3D centroid              | item 8 (depth point cloud)     |
| Grasp pose               | item 9 (PCA antipodal)         |
| Precise 6-DoF object pose | item 10 (ArUco)               |
| Calibrated 3D coordinates | items 11 + 12 (intrinsics + hand-eye) |
| Reading the barcode      | item 14 (`pyzbar`)             |

This exercise is the foundation those build on.

## What's next

- **Item 4** — run this model on the live Gazebo camera feed and
  publish detections on a ROS 2 topic.
- **Item 5** — auto-score those detections against Gazebo's
  ground-truth model state (closing the data loop the empty
  [`data/`](data/) folder hints at).
