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

## What "Done when" means here

The checklist asks for **mAP@0.5 above 0.7 on a held-out test set**.

- mAP@0.5 = mean Average Precision when a predicted box is counted
  as "correct" if its IoU with the ground-truth box is ≥ 0.5.
- A score of 1.0 = perfect; 0.7 is a strong baseline on a clean
  synthetic dataset.
- `validate.py` prints this number and exits non-zero if it is below
  0.70, so it is easy to drop into CI later.

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
