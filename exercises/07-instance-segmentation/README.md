# 07 — Instance segmentation (pixel masks, not just boxes)

Implements checklist item **7** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Builds on exercise 04 — same Gazebo world, same camera, same image
topic. The **only** thing that changes is the model.

> Item 6 ("tiny classifier quantised for an edge CPU") is skipped
> deliberately. It would deliver roughly what exercise 03's YOLO
> already gives us; pixel masks add a new capability.

## The one-paragraph "what's different from exercise 04"

YOLOv8 (detection) draws a **rectangle** around each object.
YOLOv8-seg (segmentation) labels **every pixel** that belongs to
each object. The rectangles overlap when vials sit close together;
the pixel masks do not — that's the whole point.

```
YOLOv8 (detection)              YOLOv8-seg (segmentation)
-------------------             -------------------------
  ┌───────────┐                   ░░░██░░░░░██░░░
  │           │                   ░██████░░██████░░
  │   vial    │                   ██████████████████
  │           │                   ░██████░░██████░░
  └───────────┘                   ░░░██░░░░░██░░░

one box per object              one binary mask per object
(4 numbers)                     (one bit per pixel inside the object)
```

## Why pixel masks matter for the autosampler

Vials sit ~14 mm centre-to-centre in the rack. The 12 mm cylinders'
**bounding boxes overlap by roughly 50%** with their neighbours — a
detector trying to say "this is vial B3, that is vial B4" using
boxes alone is guessing. **Pixel masks separate them cleanly**
because the gaps between vials are still background pixels.

Two concrete autosampler payoffs:

| Question the arm asks                   | What pixel masks add                                                 |
|-----------------------------------------|----------------------------------------------------------------------|
| "Is the *next* slot empty before I lower?" | Masks let you check the exact 14 mm-wide column without an overlap-induced false positive on the neighbour. |
| "Where is the vial's centre, exactly?"  | Mask centroid is more precise than a bbox centre — useful as a seed for the depth-based centroid in item 8. |

## What changes in the code

The detection node from exercise 04 and the segmentation node here
are 90% the same — load the model, subscribe to the camera, run
`model.predict()`, publish. Only the model file changes and one
extra output appears:

| Step                | Exercise 04 (YOLOv8)              | Exercise 07 (YOLOv8-seg)                                  |
|---------------------|-----------------------------------|-----------------------------------------------------------|
| Model file          | `yolov8n.pt`                      | `yolov8n-seg.pt`                                          |
| Per-result fields   | `.boxes`                          | `.boxes` **and** `.masks`                                 |
| Mask data           | —                                 | `result.masks.data` — `(N, H, W)` float tensor in [0, 1]  |
| Output topics       | `/yolo/detections`, `/yolo/image_annotated` | `/yolo_seg/detections`, `/yolo_seg/instance_mask`, `/yolo_seg/image_annotated` |
| Annotation drawing  | rectangles                        | translucent coloured masks (still bbox-aware)             |
| Cost on CPU         | ~30 ms / frame (nano)             | ~60–100 ms / frame (nano-seg)                             |

That's the entire diff at the code level. Everything else — the
ROS plumbing, the SDF world, the bridge — is reused unchanged.

## How we ship the mask through ROS

ROS does not have a "per-detection mask" message type out of the
box. The standard trick is to publish an **instance map**: a
single-channel image the same size as the input frame, where the
pixel value is the **instance id**:

```
0   = background
1   = first detection
2   = second detection
...
N   = N-th detection
```

That fits naturally in `sensor_msgs/Image` with `encoding="mono8"`.
A subscriber decodes one instance with one numpy comparison:

```python
vial_mask = instance_map == 3        # boolean H x W array
```

And the matching class / confidence for instance `i` is in
`/yolo_seg/detections.detections[i-1]` — same `Detection2DArray`
shape exercise 04 already publishes.

The `/yolo_seg/image_annotated` topic is unchanged in role: it's
the same frame with the masks drawn translucently on top, for
human eyes in RViz.

## What "Done when" means here

The checklist asks: *"Mask IoU vs Gazebo ground truth is above 0.7
per object across 10 random scenes."*

We do **not** ship a scorer for this exercise — exercise 05's
scoring pattern transfers almost directly. Swap `iou_xywh` for a
mask-IoU on the boolean arrays from `instance_map == i`, and use
exercise 05's `/gazebo/pose_info` to project each true vial to a
ground-truth disc mask the same way it projected to a bbox.

## Run it (alongside exercise 04's launch)

```bash
# 1. Make sure exercise 04 is up (Gazebo + image bridge + ... but skip the
#    YOLO detector — we don't need it for this exercise):
ros2 launch yolo_live_demo yolo_live.launch.py weights:=/abs/path/to/yolov8n.pt
# (you can stop the live_detector node if you want; it does not conflict.)

# 2. Download or train a YOLOv8-seg checkpoint:
#    Ultralytics ships pretrained COCO seg weights at yolov8n-seg.pt -
#    fine-tune on the same data set used in exercise 03 once we have it.
pip install ultralytics

# 3. Run this node:
python3 seg_node.py --ros-args -p weights:=/abs/path/to/yolov8n-seg.pt
```

Sanity checks:

```bash
ros2 topic hz /yolo_seg/detections
ros2 topic hz /yolo_seg/instance_mask
# Inspect a single instance mask:
ros2 run rqt_image_view rqt_image_view /yolo_seg/image_annotated
```

## Still 2D — and that's why camera placement matters

A mask is just a `H × W` array of booleans over the **image plane**.
No depth is attached to any pixel. To turn it into a 3D pose the
arm can plan to, you need the same four bridges as plain YOLO
(see exercise 04's question 8): **RGB-D depth (item 8)**, a
**fixed-z plane** assumption, a **slot-index lookup**, or
**ArUco markers (item 10)**. Segmentation does not replace those —
it just hands the bridge a cleaner 2D input.

Where masks win once depth lands: `mask + depth_map` gives a clean
cluster of 3D points for that one object, while `bbox + depth_map`
also drags in surrounding table. That's why the v1 sequence is
**item 7 (mask) → item 8 (depth) → item 9 (PCA grasp)**.

Because we are still 2D today, **camera placement is load-bearing**:

- **Top-down (what the SDF uses):** almost no occlusion, the
  fixed-z trick works because every vial top is at the same known
  height. Cheapest recipe for v1.
- **Side view:** vials at the back hide behind the front row —
  masks cannot fix that.
- **Eye-in-hand (gripper-mounted):** great for final approach,
  needs hand-eye calibration (item 12) to be useful.

The more constraints baked into the camera placement, the less
calibration math you need later. Move the camera and you re-open
exercises 11 and 12.

## What this exercise is **not**

- **Not a full mask scorer** — the IoU comparison logic from
  exercise 05 generalises; we don't repeat it here.
- **Not panoptic segmentation** — panoptic also classifies every
  background pixel (table, rack body). Useful, heavier, not needed
  for picks.
- **Not depth-aware** — masks are still 2D. Item 8 (RGB-D centroid)
  is the first 3D answer.

## What's next

- **Item 8** — RGB-D point cloud → 3D centroid. The mask centroid
  becomes a great seed for the depth lookup.
- **Item 9** — grasp-point estimation. PCA on the *mask pixels*
  gives a much cleaner principal-axis estimate than PCA on bbox
  pixels would.
