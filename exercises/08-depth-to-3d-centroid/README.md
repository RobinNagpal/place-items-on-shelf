# 08 — Depth-camera point cloud → 3D object centroid

Implements checklist item **8** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Builds on exercise **07** (instance segmentation). Adds the **one
missing dimension** — depth — and turns a 2D pixel mask into a 3D
point the arm can plan to.

## The whole new idea, in one paragraph

Exercise 07 told us *which pixels* belong to each vial. Now we add
a **depth camera**: every pixel also carries a distance in metres.
For each instance we collect the depth values inside its mask, take
the median, and back-project through the same pinhole equations
from exercise 05 — only run in reverse. The output is one
`(X, Y, Z)` per object in the camera frame.

```
exercise 07 already gives us:                this exercise adds:

camera ─► YOLOv8-seg ─► /yolo_seg/instance_mask     depth camera ─► /overhead_camera/depth
                       /yolo_seg/detections                                      │
                                  │                                              │
                                  └───────────────► centroid_node ◄──────────────┘
                                                          │
                                                          ▼
                                              /objects/centroids
                                              (Detection3DArray)
```

Only one new file: `centroid_node.py`.

## Two ways to turn a depth image into a 3D pose

There are two schools of thought for this step. Picking which one
matters more than the code itself.

### A. Pure-geometry on the raw point cloud (no detector)

The depth camera also gives you a full point cloud — a list of 3D
points, no labels attached. If we already know we're looking for a
**12 mm × 32 mm cylinder**, classical algorithms can search for it
directly:

- **Euclidean clustering** — group nearby 3D points into blobs.
- **RANSAC cylinder fit** — for each blob, test "does a 12 mm
  cylinder fit these points?" The math is closed-form.
- **Template matching on point clouds** — slide a known vial shape
  over the cloud and score the overlap.

This *works*. It is also how a lot of older industrial vision
pipelines were built. But two things hurt:

| Problem                                      | Effect                                                                            |
|----------------------------------------------|-----------------------------------------------------------------------------------|
| Multiple identical objects                   | You get N cylinder clusters with no idea which is "slot A3" vs "A4".              |
| Noisy / partial clouds                       | Half a vial behind another vial doesn't fit a cylinder cleanly. The fit drops.    |
| Different shapes share parameters            | A vial cap and a small rack peg both look like short cylinders to RANSAC.         |

So you end up adding a **separate identification step** after the
geometric fit. That's the gap a YOLO detector closes for free —
it already says "this group of pixels is a vial".

### B. Detector + depth lookup (what this exercise does)

The detector from exercise 07 already labelled every pixel: pixel
value `3` in `/yolo_seg/instance_mask` means "vial #3". For each
instance we just:

1. Pull the depth values **inside that mask**.
2. Take their median (robust to mask edge noise).
3. Back-project the mask centroid `(u, v)` plus that depth through
   the inverse pinhole.

Result: one `(X, Y, Z)` per object, identity already attached. No
clustering, no RANSAC, no second pass to relabel.

This is also why the v1 sequence is **item 4/7 (where, in 2D) →
item 8 (how far) → item 9 (how to grasp)**. Each step adds one
axis of information without trying to redo the previous one.

## Multiple identical vials — does it confuse the node?

No. The mask carries identity:

```
/yolo_seg/instance_mask:        /yolo_seg/detections:
 0 0 0 0 0 0 0 0 0              detections[0] = {class: vial, score: 0.91}
 0 1 1 0 2 2 0 3 3              detections[1] = {class: vial, score: 0.89}
 0 1 1 0 2 2 0 3 3              detections[2] = {class: vial, score: 0.88}
 0 0 0 0 0 0 0 0 0
   ^^^   ^^^   ^^^
  vial   vial  vial
  #1     #2    #3
```

Three vials that look identical to a geometric pipeline already
have three distinct ids here. The centroid node loops over the ids,
not over a pool of "vial blobs". Two vials side-by-side stay
separated even when their bounding boxes overlap, because pixel
masks (item 7) carved them apart upstream.

## The inverse pinhole, in three lines

Exercise 05 projected world → pixel. We need the reverse:

```python
Z = depth_metres                          # straight from the depth image
X = (u - cx) * Z / fx                     # cx, fx from the camera intrinsics
Y = (v - cy) * Z / fy
```

`(X, Y, Z)` is in the **camera frame**. To hand it to MoveIt as a
target in the **robot base frame**, you run it through TF once —
that's exercise 12 (hand-eye calibration). We don't do TF here so
the output stays close to the depth image it came from.

## What "Done when" means here

The checklist asks for *"a 3D centroid per object, accurate to
within 1 cm of the Gazebo ground truth."*

Two sources of error matter:

| Source              | Typical size at 0.5 m camera distance                                       |
|---------------------|-----------------------------------------------------------------------------|
| Depth noise         | ~2 mm RMS on the Gazebo plugin; smaller after the median across many pixels |
| Mask edge wobble    | 1-2 px; the median depth absorbs almost all of it                           |
| Intrinsic mismatch  | 0 — same constants as the SDF; check exercise 05 if you tweak the camera    |

We do **not** ship an automated scorer for this exercise. The
pattern is identical to exercise 05's scorer — substitute
`compare_3d_distance(gt_pose, predicted_xyz)` for the IoU step. If
you want a number, copy that node and change one function.

## Run it

You need exercise 07 running plus a depth-image topic. The Gazebo
depth-camera sensor is a one-block addition to the SDF (see
`IMPLEMENTATION_NOTES.md` for the SDF snippet and the matching
`ros_gz_image` bridge command). Once those are up:

```bash
# Assumes exercise 07's seg node + bridge are publishing.
python3 centroid_node.py --ros-args \
    -p depth_topic:=/overhead_camera/depth
```

Sanity checks:

```bash
ros2 topic hz /objects/centroids
ros2 topic echo /objects/centroids --once
# Expect Z ≈ 0.475 m for a vial sitting on the bench at ~0.825 m
# below the camera (CAM_Z=1.30 in the SDF, bench top ≈ 0.825 m).
```

## What this exercise is **not**

- **Not a TF transform** — the output is in the camera frame.
  Converting to the robot base frame is item 12 (hand-eye).
- **Not a grasp pose** — only the centre point. Item 9 adds
  orientation via PCA on the mask pixels.
- **Not a full point-cloud pipeline** — we sample depth at the
  mask, not the entire cloud. That's deliberate (see "two ways"
  above).

## What's next

- **Item 9** — grasp-point estimation. PCA on the *mask pixels*
  gives a principal axis; this exercise's `(X, Y, Z)` becomes the
  centre of the grasp.
- **Item 12** — hand-eye calibration. Once you know the camera ↔
  end-effector transform, the centroid here turns into a MoveIt
  target without any extra math.
