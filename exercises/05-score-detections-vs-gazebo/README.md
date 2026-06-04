# 05 — Score detections automatically against Gazebo ground truth

Implements checklist item **5** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Builds **directly on exercise 4** — the Gazebo world, the camera,
the bridge, and the live YOLO node are reused unchanged.

## The whole new idea, in one paragraph

Gazebo already knows the **true 3D pose** of every object in the
scene. It publishes those poses on a topic. So instead of paying a
human to label "vial here, vial there" in every frame, we let
Gazebo's own pose stream play the role of the labeller. We project
each true pose onto the image, compare it to YOLO's predicted box,
and keep a running tally — **no manual labelling at all**.

```
exercise 4:                          exercise 5 adds:

camera ─► ros_gz_image ─► YOLO       Gazebo model poses ─► ros_gz_bridge
                          ▼                                       ▼
                  /yolo/detections                       /gazebo/pose_info
                          │                                       │
                          └─────────────────► detection_scorer ◄──┘
                                                      │
                                                      ▼
                                        running TP / FP / FN / mean-IoU
```

The only new code is `detection_scorer.py`. Nothing in the YOLO
pipeline changes — we just **read** its output topic and compare.

## What exact values are we cross-verifying?

| From                        | What it gives                                                        |
|-----------------------------|----------------------------------------------------------------------|
| **Gazebo `/pose/info`**      | For every model in the world: `(X, Y, Z)` and orientation in metres / radians, in the world frame. The **ground truth**. |
| **`/yolo/detections`**       | For every box YOLO drew: `(cx, cy, w, h)` in **pixels** plus class and confidence. The **prediction**. |

These two live in different units (metres vs pixels) and different
frames (world vs image). To compare them we have to put them on the
same page. We do that by projecting the ground truth into pixels —
exactly the math a real camera does — so the comparison is
apples-to-apples in pixel space.

## The actual comparison — is it just "the difference between two values"?

Yes, in spirit. Once both boxes are in pixels, the comparison is
one number per pair:

- **IoU (Intersection over Union)** of the predicted box and the
  ground-truth box. `1.0` = exactly the same box, `0.0` = no
  overlap. We treat `IoU >= 0.5` as "the model got this vial".

That single number rolls up into the standard counts:

- **TP (true positive)** — a YOLO box matched a real vial with
  IoU ≥ 0.5.
- **FP (false positive)** — a YOLO box that did not match any real
  vial (the model "hallucinated" one).
- **FN (false negative)** — a real vial that YOLO did not find.

And from those, the usual ratios:

- **Precision** = `TP / (TP + FP)` — of the boxes the model drew,
  how many were right?
- **Recall** = `TP / (TP + FN)` — of the real vials, how many did
  the model find?

The scorer prints these every second and a final summary on Ctrl-C.

## How we get the "exact position" from Gazebo

Two short hops, almost the same shape as exercise 4's image
pipeline:

1. **Gazebo publishes** every model's world pose on its own
   transport topic `/world/autosampler_cell/pose/info`.
2. **`ros_gz_bridge`** maps that to a `tf2_msgs/TFMessage` on the
   ROS 2 topic `/gazebo/pose_info`. Each `TransformStamped` inside
   that message has `child_frame_id` = the model's name and the
   `translation` is the world position.

So `vial_a3`'s true position is just:

```python
for t in msg.transforms:
    if t.child_frame_id == "vial_a3":
        x, y, z = t.transform.translation.x, ...    # metres, world frame
```

Bridge command (single line — add it to exercise 4's launch or run
in its own terminal):

```bash
ros2 run ros_gz_bridge parameter_bridge \
    /world/autosampler_cell/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V \
    --ros-args -r /world/autosampler_cell/pose/info:=/gazebo/pose_info
```

## From a 3D pose to a pixel box (one function)

Camera is mounted straight down, so the projection collapses to a
short closed form:

```python
depth = CAM_Z - z_world                    # how far below the camera
u_px  = cx_px + fx * (y_world - CAM_Y) / depth
v_px  = cy_px + fy * (x_world - CAM_X) / depth
```

`fx = (image_width/2) / tan(hfov/2)` — derived once from the SDF.

Width / height of the projected vial are constant because the
camera distance is fixed: roughly 14 px on each side for a 12 mm
vial seen from ~0.475 m. That number lives at the top of
`detection_scorer.py` and is the only thing to update if you move
the camera.

## What "Done when" means here

The checklist asks for *"a single script that prints IoU per frame
and an mAP summary at exit."*

- `detection_scorer.py` prints **TP / FP / FN / precision / recall /
  mean IoU** every second.
- On `Ctrl-C` it prints the final summary so it does not scroll past.

(mAP@0.5 specifically would need to sweep confidence thresholds and
compute the precision-recall curve, like exercise 3's `validate.py`.
The single-IoU summary here is enough for the checklist bar and is
much easier to read live.)

## Run it (after exercise 4 is already running)

Three steps. Two of them are one-liners; the third is the script.

```bash
# 1. Make sure exercise 4 is already running (Gazebo + bridge + YOLO).
ros2 launch yolo_live_demo yolo_live.launch.py weights:=/abs/path/to/best.pt

# 2. In a second terminal: bridge Gazebo's pose topic to ROS 2.
ros2 run ros_gz_bridge parameter_bridge \
    /world/autosampler_cell/pose/info@tf2_msgs/msg/TFMessage[gz.msgs.Pose_V \
    --ros-args -r /world/autosampler_cell/pose/info:=/gazebo/pose_info

# 3. In a third terminal: the scorer.
python3 detection_scorer.py
```

Sample output:

```
[t=   1s] TP=2 FP=0 FN=1  P=1.00 R=0.67  meanIoU=0.43
[t=   2s] TP=5 FP=0 FN=1  P=1.00 R=0.83  meanIoU=0.48
[t=   3s] TP=8 FP=0 FN=1  P=1.00 R=0.89  meanIoU=0.51
...
=== final score ===
frames scored: 30
TP=84  FP=3  FN=6
precision=0.966  recall=0.933
mean IoU on matched pairs=0.520
```

Drag a vial around in the Gazebo GUI — the precision should stay
high while you do it, because the GT pose moves with the vial and
the projection follows.

## What this exercise is **not**

- **Not a full mAP curve** — we hold IoU=0.5 fixed and report a
  scalar. Sweeping thresholds is exercise 3's job, offline.
- **Not a generic projection** — the helper assumes our specific
  straight-down camera. Move the camera and rewrite the four-line
  `project_to_pixel` function.
- **Not for the rack/tray edge classes** — we score `vial` only.
  Edges would mean four corner points each; the same idea, just
  more bookkeeping.

## What's next

- **Item 6** — quantise the same `.pt` to INT8 for the on-arm Pi.
- **Item 7** — pixel masks (instance segmentation) for tightly
  packed vials. The scorer here is the natural mask-IoU target too.
- **Item 8** — the first 3D answer: depth-camera point cloud →
  object centroid in metres.
