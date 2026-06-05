# Implementation notes — 05 Score detections vs Gazebo ground truth

Just the choices that are not obvious from the code.

## Why we score every 1 s, not every frame

YOLO runs at the camera frame rate (~30 Hz on a GPU, single digits
on a CPU). Scoring at that same rate is wasteful — and the running
tally only needs to be human-readable. A 1 Hz timer is cheap,
prints cleanly, and gives the user a slow-enough number stream to
read while dragging a vial in Gazebo.

The scorer uses the **latest** detection seen since the previous
tick. That means short detection drops do not bias the score: they
just contribute one extra FN to the running tally and move on.

## Why we hardcode `CAM_X / CAM_Y / CAM_Z / HFOV / IMG_W / IMG_H`

The clean alternative is to subscribe to `/camera_info` and pull the
intrinsics from there. We do not for two reasons:

1. **Gazebo Sim does not always publish `CameraInfo`** for a bare
   `<sensor type="camera">` block — you usually have to add an
   extra plugin or hand-write a CameraInfo publisher. That is a
   side quest.
2. **The whole exercise is "one step ahead of exercise 4"** — moving
   the camera in the SDF then re-deriving the intrinsics is the
   same change in both places. Reading from two sources just hides
   the dependency without removing it.

The price: if you ever change the camera in the SDF, you must edit
the constants at the top of `detection_scorer.py`. A single comment
points that out.

## Why `project_to_pixel` is the short form, not a full extrinsic matrix

For a camera pose with only a `pitch=+pi/2` rotation, the world
axes line up with the image axes in a trivial way:

```
right in image  (+u)  ↔  +Y in world
down in image   (+v)  ↔  +X in world
depth axis      (+z)  ↔  -Z in world  (camera looks down)
```

So the full `K @ [R|t] @ world_point` reduces to one division per
axis. Doing it long-form would add ~15 lines of numpy + a rotation
constant — for **this specific camera** the closed form is clearer
*and* equivalent.

If the camera ever gains a non-trivial yaw / roll / non-straight-
down pose, replace the function body with a proper
`cv2.projectPoints` call and pass the rotation as `rvec`.

## Why GT bbox size is a constant 14x14 px

At true top-down view of an upright cylinder you see a disc, not a
rectangle. The disc's diameter projects to:

```
pixel_diameter = (real_diameter * fx) / depth
              = (0.012 * 554) / 0.475
              ≈ 14 px
```

That is independent of where the vial sits in the rack, because the
camera-to-vial depth is roughly constant (rack-top vs tray-top
differ by ~25 mm out of 475 mm, ~5% error). Pretending the GT box
is the same size everywhere keeps the scorer code two lines instead
of twenty.

For mAP@0.5 this is plenty accurate — a 5% box-size mismatch only
moves the IoU threshold slightly.

If you start scoring **rack edges** or **tray edges** (4 corners
each), drop the constant and project both corners of each side
properly.

## Why we use `Detection2DArray.results[0]`

`Detection2D` allows multiple **class hypotheses** per box (the
ImageNet "top-5" pattern). YOLOv8 publishes one class per box, so
`results[0]` is always the only entry. We assume that and don't
iterate.

If a future detector publishes a true top-K list, swap the indexed
access for a "pick the highest score" loop.

## Why we treat extra YOLO boxes as FPs without checking class

Inside `_score_tick` we already filter `latest_dets` for class
`"vial"`, so any unmatched detection in that filtered list was a
YOLO vial prediction that did not overlap a real vial. That is
exactly a false positive of class `vial`.

Other YOLO classes (`cap_red`, `rack_edge`, …) are simply ignored —
they neither help nor hurt the score. Once we add a Gazebo GT for
them too, the same logic generalises: one tracker per class.

## Failure modes you will see in practice

- **`/gazebo/pose_info` not publishing** — the `ros_gz_bridge` line
  in the README has a long flag; one wrong character breaks the
  bridge silently. `ros2 topic hz /gazebo/pose_info` should show
  ~30 Hz.
- **Everything is FN** — IoU is 0 every time. Either the projection
  signs are wrong (your camera pose differs from the SDF) or the
  YOLO model never learned `vial` (wrong `best.pt`). Print one
  `gt_box` and one `yolo_vials[0]` side-by-side; if they are far
  apart in u-v, the projection is the bug.
- **All TP, all IoU = 1.0** — you forgot to set
  `CAM_Z`/`CAM_Y`/`CAM_X` to the actual camera pose, so the GT box
  and the predicted box both default to image-centre. Confirm the
  constants match the SDF.
- **Stats look right but precision dips during motion** — that is
  the YOLO node falling behind the camera. The 1 Hz scorer reads
  the most recent detection; if that detection is from 200 ms ago,
  it lags the (moved) GT pose. Lower YOLO confidence threshold or
  run inference on a GPU.
