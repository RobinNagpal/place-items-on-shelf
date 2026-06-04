# 12 — Hand-eye calibration (camera ↔ arm base)

Implements checklist item **12** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Closes the last gap between **perception** (items 4 / 7 / 8) and
**motion** (items 18 - 22).

## The whole new idea, in one paragraph

Exercise 08 produces 3D centroids in the **camera frame** —
`(X_cam, Y_cam, Z_cam)`. MoveIt plans motion in the **robot base
frame** — `(X_base, Y_base, Z_base)`. Those two frames are related
by a single static 4×4 matrix `T_base_cam`. Hand-eye calibration
*measures* that matrix once by watching the arm move an ArUco
marker through ~20 known poses and fitting the only transform that
explains all 20 observations.

```
exercise 8 already gives us:                this exercise adds:

/objects/centroids (camera frame)       arm wiggle + ArUco watching
        │                                            │
        │                                            ▼
        │                                 cv2.calibrateHandEye(20 pairs)
        │                                            │
        │                                            ▼
        │                                     T_base_cam (static)
        │                                            │
        └─────────────► tf2 ─────────────────────────┘
                          │
                          ▼
              /objects/centroids in BASE FRAME → MoveIt target pose
```

One number per camera. Done once at install, re-done after any
bump.

## Eye-in-hand vs eye-to-hand — which one are we doing?

Two physical layouts. They share the math; the *labelling* flips.

```
EYE-IN-HAND (camera bolted to the wrist)        EYE-TO-HAND (overhead, fixed)
                                                 ── this exercise ──

     ┌──┐                                              ┌──📷──┐
     │📷│  ← camera moves with EE                     bench / ceiling
     ├──┤                                              │
     │  │  arm                                          │
     ├──┤                                              ┌──┐
     │  │                                              │  │ arm
     │  │                                              │  │
                                                       │  │
        target sits in the world                      ┌──┐
                                                      📍   ← marker on EE
        we solve: T_ee_cam                            we solve: T_base_cam
        (where is the camera                          (where is the camera
         relative to the gripper?)                     relative to the base?)
```

Our checklist write-up was sketched for eye-in-hand (camera on EE);
**our actual rig is eye-to-hand** (overhead camera from exercise 04).
That changes:

| Step                                | Eye-in-hand                            | Eye-to-hand (this exercise)                 |
|-------------------------------------|----------------------------------------|---------------------------------------------|
| Where the marker lives              | Glued to the bench (world)             | Glued to the **end-effector**               |
| What stays static                   | Marker pose in world                   | Marker pose in EE                           |
| What moves                          | Camera (with the arm)                  | Marker (with the arm)                       |
| What we solve                       | `T_ee_cam`                             | `T_base_cam`                                |
| OpenCV call                         | `cv2.calibrateHandEye(...)`            | Same call with **inverted EE poses**        |

The trick of inverting the EE poses and re-using the same solver is
documented under "Eye-to-Hand variant" in the OpenCV docs. It works
because the AX = XB problem is symmetric — what changes is just
which leg of the chain you treat as "the unknown".

## The maths in one diagram

For every sample `i` the marker can be reached by two paths through
the kinematic chain, and they must agree:

```
                ┌───── T_base_ee_i ─────► EE ─── T_ee_marker ────►┐
       BASE ────┤                                                 ├── MARKER
                └───── T_base_cam ──────► CAM ─── T_cam_marker_i ►┘
```

`T_ee_marker` is constant (the marker is bolted to the EE) and
`T_base_cam` is constant (the camera is bolted to the world). The
two changing things are what the arm reports (`T_base_ee_i`) and
what the camera detects (`T_cam_marker_i`). Re-arranged, every
sample gives one equation of the form **A · X = X · B** where X is
the unknown camera transform. `cv2.calibrateHandEye` solves that
over-determined system for the X that fits all 20 samples best.

## What we feed the solver

| Input list (N=20)        | Where it comes from                                                              |
|--------------------------|----------------------------------------------------------------------------------|
| `R_base_ee_i, t_base_ee_i` | TF lookup `base_link → tool0` at the time the marker frame was captured        |
| `R_cam_marker_i, t_cam_marker_i` | ArUco detector (item 10) — publishes `PoseStamped` in the camera frame |

20 samples is the rule of thumb. More samples reduce noise; what
matters more is **pose variety** — the arm needs to *rotate* the
marker, not just translate it (rotation is what disambiguates the
solver). The collector here drops samples within 5 cm of any
existing sample to enforce some spread.

## What "Done when" means here

The checklist asks: *"re-projecting a fresh marker detection lands
within 5 mm of the marker's true position."*

The node prints two numbers at the end:

1. The solved `(x, y, z, roll, pitch, yaw)` for `T_base_cam`.
2. The residual mean / std after the fit — how consistent the 20
   samples are *with each other*. Sub-millimetre residuals in
   Gazebo. In the real world, expect 1-3 mm with a 30 mm ArUco
   marker and a 1080p camera.

It also prints a ready-to-paste `tf2_ros static_transform_publisher`
command. From then on, **TF carries the camera ↔ base relationship
for free**, and any node that wants to convert
`/objects/centroids` to the base frame does:

```python
self._tf_buf.transform(centroid_in_cam, "base_link")
```

That single line is the entire payoff of this exercise.

## Why we are skipping items 9 and 11

The task list defers two items at this point. Both for use-case
reasons, neither because the topic is unimportant:

- **Item 9 — depth-based grasp-point estimation.** Real HPLC
  autosamplers pick vials from above with a **three-finger cap
  gripper** (Agilent G2258A) or a needle through the septum. There
  is ~2 mm of side clearance between vials at 14 mm centres, so a
  two-finger antipodal grasp (which is what item 9 plans) cannot
  physically enter. The grasp pose collapses to *(centroid XY,
  cap-top Z, gripper pointing straight down)* — five numbers from
  CAD, no planner needed.
- **Item 11 — camera intrinsics calibration.** Gazebo gives us the
  exact intrinsics from the SDF (`fx = 554.26 px`, `cx = 320`,
  …). In the real world you would shoot a checkerboard with
  `camera_calibration` — same recipe everyone uses, well-known. The
  educational delta over what exercise 05 already explains is small.

Both stay on the radar for future projects with different parts or
real hardware. Neither blocks the v1 perception → motion pipeline.

## Run it (concept only — script not exercised here)

This exercise assumes:

1. An ArUco detector is publishing `/aruco/marker_pose`
   (`geometry_msgs/PoseStamped` in the camera frame). That node is
   itself item 10 — we don't ship it here. A bare-bones version is
   ~30 lines of `cv2.aruco.detectMarkers` + `cv2.solvePnP`.
2. The arm is being driven through 20 reasonably varied poses
   (any small loop of exercise 19's `setPoseTarget` works).
3. TF is publishing `base_link → tool0` (free with the MoveIt
   launch from exercise 18).

```bash
python3 hand_eye_calibrate.py --ros-args \
    -p marker_topic:=/aruco/marker_pose \
    -p ee_frame:=tool0 \
    -p base_frame:=base_link \
    -p num_samples:=20
```

Sample output:

```
[hand_eye_calibrate] sample 1/20 captured
...
[hand_eye_calibrate] sample 20/20 captured
[hand_eye_calibrate] === T_base_cam ===
  translation: x=0.0500  y=0.0000  z=1.3000  metres
  rotation:    roll=3.1416  pitch=-0.0000  yaw=-0.0000  rad
[hand_eye_calibrate] static TF command:
  ros2 run tf2_ros static_transform_publisher \
      --x 0.0500 --y 0.0000 --z 1.3000 \
      --roll 3.1416 --pitch 0.0000 --yaw 0.0000 \
      --frame-id base_link --child-frame-id overhead_camera_optical_frame
[hand_eye_calibrate] residual mean=0.84 mm  std=0.31 mm
```

## What this exercise is **not**

- **Not the ArUco detector** — that's item 10. We assume the topic.
- **Not the arm dance** — driving the arm through 20 poses is one
  exercise-19-style loop; not duplicated here.
- **Not a continuous TF publisher** — the output is a static
  transform, and `tf2_ros static_transform_publisher` does that for
  you in one shell line.
- **Not a rotation handler for vials** — the marker's orientation
  helps the solver but the final pick (centroid → grasp pose) uses
  position only because cap orientation does not matter.

## What's next

This effectively closes the v1 perception → motion pipeline:

```
RGB-D camera ─► YOLOv8-seg (item 7) ─► instance_mask + detections
                                              │
                                              ▼
                                      centroid_node (item 8)
                                              │  centroid in camera frame
                                              ▼
                                      tf2 transform (this exercise)
                                              │  centroid in base frame
                                              ▼
                                      pick controller (exercise 21)
                                              │  approach → grasp → lift
                                              ▼
                                            MoveIt
                                              │
                                              ▼
                                             arm
```

The remaining checklist items add **robustness** rather than new
capability: F/T sensing to detect cap contact (item 15), gripper
contact sensors to confirm grasp (item 17), colour segmentation as
a backup vision pipeline (item 13), barcodes for vial IDs
(item 14). Each is useful, none is on the critical path.
