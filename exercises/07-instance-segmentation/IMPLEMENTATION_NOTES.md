# Implementation notes — 07 Instance segmentation

The non-obvious choices behind `seg_node.py`.

## Why YOLOv8-seg and not Mask R-CNN or SAM

| Option            | Why we passed                                          |
|-------------------|--------------------------------------------------------|
| **YOLOv8-seg**    | Same Ultralytics API as exercise 03 / 04. One line difference: load `yolov8n-seg.pt` instead of `yolov8n.pt`. ~6 MB on disk. Runs on the same Pi-class hardware. |
| **Mask R-CNN**    | The classic. Far heavier (~170 MB ResNet-50 backbone), 2–4 FPS on a CPU. Beats YOLOv8-seg by a few mAP points; not worth it for the vial task. |
| **SAM / SAM 2**   | Foundation segmentation model — runs zero-shot, no fine-tuning needed. Excellent boundaries. Slow (~1–2 s per frame on CPU). Useful for one-off **auto-labelling** later (a stronger replacement for exercise 05's projected ground truth), not for live inference. |
| **YOLOv9-seg / v10-seg / v11-seg** | Newer and slightly faster. Same API path. Easy drop-in swap once the project commits to a specific Ultralytics version. |

## Why the instance map is `mono8`, not a stack of binary masks

A stack of `N` binary masks would mean publishing `N`
`sensor_msgs/Image`s per frame — variable count, per-mask
synchronisation headache for subscribers. The instance-map
representation collapses them into **one** image of the same
dimensions, and a subscriber gets any individual mask in one line:

```python
vial_mask = instance_map == 3   # boolean (H, W)
```

The cost is a 254-instance cap. For the autosampler (max 100 vials
in a tray) this is comfortably high.

## Why we threshold the soft mask at 0.5

`result.masks.data` is a float tensor in `[0, 1]` — the network's
per-pixel "soft" probability that this pixel belongs to the
instance. Thresholding turns it into a binary mask. `0.5` is the
standard cutoff and matches Ultralytics' own visualisation
(`.plot()`).

For tightly packed objects you may want a stricter threshold (0.6,
0.7) to avoid two instances claiming the same pixel — but that
shows up as a *bias* in the scorer, so do not tune this without
re-running exercise 05.

## Why we keep publishing the bbox `Detection2DArray` alongside the mask

Two reasons:

1. **The classifier / confidence lives there.** The instance map
   alone says "instance 3 occupies these pixels" but does NOT say
   "instance 3 is a `vial` at confidence 0.92". The detections
   message carries that, indexed by instance order.
2. **Downstream subscribers can pick.** Code that only needs "where
   are the vials roughly" stays on the bbox topic and avoids the
   mask cost. Code that needs the exact silhouette subscribes to
   `instance_mask`. The arm controller may only ever need the
   former; the grasp-planner needs the latter.

## Why we copy the camera image header onto every output message

Same reason as exercise 04 — without the header, TF lookups
("where is instance 3 in the arm frame?") have nothing to anchor
on. The instance map, the bbox array, and the overlay all share
the **same** `frame_id` and `stamp` so a subscriber knows they came
from the same physical frame.

## Why we do not pull intrinsics into this node

Exercise 05's scorer hardcodes the camera intrinsics. This node
does not need them — it stays entirely in pixel space. The
projection of "instance 3's mask centroid" into a 3D world point
is the next exercise's job (item 8, RGB-D centroid).

That separation keeps each node simple and prevents intrinsics
from being defined in two places.

## Performance — when CPU is not enough

| Resolution × FPS    | Hardware    | Expected throughput |
|---------------------|-------------|---------------------|
| 640×480 @ 30 Hz     | i5 laptop CPU | 6–10 FPS — drops half the frames |
| 640×480 @ 30 Hz     | RTX 4060 GPU | 30+ FPS — easy        |
| 640×480 @ 30 Hz     | Jetson Orin Nano | 15–25 FPS — usable |

If you must run on CPU and the throughput is too low:

- Pass `imgsz=512` to `predict()`. ~30% faster, small mask quality
  hit.
- Quantise to INT8 (planned for item 6). Roughly 2× CPU speed up.
- Subscribe at 5 Hz instead of 30 Hz with a `ros2 topic throttle`
  node — for an event-driven pick (the autosampler pattern), 1
  frame is enough.

## Failure modes you will see in practice

- **`result.masks` is `None`** — you loaded a *detection* `.pt` by
  mistake. YOLOv8-seg weights have `-seg` in the filename.
- **Instance map is all zeros but the overlay shows masks** — the
  soft mask threshold (`> 0.5`) excluded everything. Confidence
  threshold was too high; lower `conf_threshold`.
- **Annotation looks right; subscribers crash on mask shape** — a
  YOLO frame skipped publishing (no detections) so subscribers
  see a `None` instance map. The node still publishes a zero map
  in that case, so this should be impossible — if it happens, the
  subscriber forgot to declare a QoS depth and dropped the first
  message.
- **Masks "shimmer" at instance boundaries between frames** — the
  per-pixel probability is just-above-0.5 in that ring. Common,
  cosmetic. Smooth in post if it matters; do not raise the
  threshold globally.

## What to revisit later

- Once exercise 05's scorer is in place, copy it into a
  `mask_scorer.py` that uses **mask IoU** (intersection-over-union
  of the boolean masks) instead of bbox IoU. The rest of the
  logic — match GT to prediction, TP/FP/FN — is identical.
- Investigate publishing per-instance masks as a
  `vision_msgs/Detection2DArray` extension once we accept a custom
  message dependency.
