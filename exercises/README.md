# Exercises

Small, self-contained implementations of the items in
[`../docs/learning-checklist.md`](../docs/learning-checklist.md). One
subfolder per item. Each folder is independent — you do not have to
work through them in order.

## How each exercise folder is laid out

Every folder follows the same shape:

```
NN-short-slug/
├── README.md              # what it does, in plain English
├── ARCHITECTURE.md        # folder tree and what each file owns
├── IMPLEMENTATION_NOTES.md# engineering decisions and trade-offs
└── <code / annotation files for this exercise>
```

The three doc files exist for different readers:

- **`README.md`** — for someone meeting the exercise for the first time.
  Concept-level: what it does, the workflow, the data flow, an example run.
- **`ARCHITECTURE.md`** — for someone editing the code. Lists every file
  in the folder and what it is responsible for.
- **`IMPLEMENTATION_NOTES.md`** — for someone debugging it. Why each
  library, what the algorithm does, the assumptions, the failure modes.

If an exercise has no code (e.g. a "read and annotate" task), the
annotation file replaces the code, but the three docs still apply.

See [`../CLAUDE.md`](../CLAUDE.md#when-implementing-a-learning-checklist-item)
for the full convention.

## Implemented so far

Each implementation targets the **HPLC autosampler tie-in** noted on
that checklist item — dimensions, layout, and the reference products
come from
[`../docs/hplc-autosamplers/requirements/`](../docs/hplc-autosamplers/requirements/).

| # | Folder | Checklist item | Status |
|---|---|---|---|
| 1 | [`01-custom-gazebo-world/`](01-custom-gazebo-world/) | A.1 — Gazebo world of the autosampler cell | done |
| 2 | [`02-read-and-annotate-urdf/`](02-read-and-annotate-urdf/) | A.2 — URDF + reach check against the cell | done |
| 3 | [`03-tiny-yolo/`](03-tiny-yolo/) | B.3 — Tiny YOLO fine-tuned on a 5-class autosampler dataset | done |
| 4 | [`04-yolo-live-on-gazebo-camera/`](04-yolo-live-on-gazebo-camera/) | B.4 — YOLO live on a Gazebo overhead camera, publishing `vision_msgs/Detection2DArray` | done |
| 5 | [`05-score-detections-vs-gazebo/`](05-score-detections-vs-gazebo/) | B.5 — Auto-score `/yolo/detections` against Gazebo model-state ground truth (IoU, running TP/FP/FN) | done |
| 7 | [`07-instance-segmentation/`](07-instance-segmentation/) | B.7 — YOLOv8-seg live on the Gazebo camera; publishes detections + instance mask + overlay | done |
| 8 | [`08-depth-to-3d-centroid/`](08-depth-to-3d-centroid/) | B.8 — Depth camera + instance mask → 3D centroid per object on `/objects/centroids` | done |
| 10 | [`10-aruco-pose/`](10-aruco-pose/) | B.10 — ArUco 6-DoF pose from a single RGB frame; one Detection3D per marker | done |
| 12 | [`12-hand-eye-calibration/`](12-hand-eye-calibration/) | B.12 — Eye-to-hand calibration via `cv2.calibrateHandEye`; closes the camera-frame ↔ base-frame gap | done |
| 13 | [`13-color-segmentation/`](13-color-segmentation/) | B.13 — HSV-threshold cap segmenter; maps detections to rack-slot ids for LIMS colour subsets | done |
| 18 | [`18-joint-space-hello-moveit/`](18-joint-space-hello-moveit/) | D.18 — MoveIt hello world: home → park → home | done |
| 19 | [`19-cartesian-pose-goal/`](19-cartesian-pose-goal/) | D.19 — Cartesian pose goal: MoveIt as the IK solver | done |
| 20 | [`20-collision-objects/`](20-collision-objects/) | D.20 — Collision objects in the planning scene | done |
| 21 | [`21-hardcoded-pick-and-place/`](21-hardcoded-pick-and-place/) | D.21 — Hardcoded pick-and-place: 18 + 19 + 20 stitched together | done |
| 22 | [`22-cartesian-path-following/`](22-cartesian-path-following/) | D.22 — Straight-line Cartesian path (`computeCartesianPath`) | done |

The numbers match the item numbers in
[`../docs/learning-checklist.md`](../docs/learning-checklist.md). When you
implement a new item, add a row here and a `[x]` tick in the checklist.
