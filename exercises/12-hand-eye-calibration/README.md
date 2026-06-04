# 12 — Hand-eye calibration (camera ↔ arm base)

Implements checklist item **12** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Closes the last gap between **perception** (items 4 / 7 / 8 / 10)
and **motion** (items 18 – 22).

## What this exercise is actually solving

Imagine two different people describing where a vial is:

- **The camera** says: *"vial is 8 cm right of my lens, 4 cm down,
  47 cm in front of me."*
- **The arm** thinks in its **own** coordinates: base at the
  origin, X forward along the bench, Y left, Z up. It does not
  know what "right of the lens" means.

Both are right. They describe the **same vial**, but in two
different **coordinate languages**. Without a translator, the arm
cannot plan motion using camera-words — it would go somewhere
completely wrong.

The translator is a single 4×4 matrix called `T_base_cam`. It
encodes 6 numbers:

- The camera's position in arm-coordinates (x, y, z).
- The camera's orientation in arm-coordinates (roll, pitch, yaw).

**The entire purpose of this exercise is finding those 6 numbers.**
Once we have them, every pixel the camera sees can be turned into a
point the arm can move to. Skip this step and MoveIt is planning to
the wrong place by exactly the camera's unknown offset — usually
several cm.

## A short glossary

| Term         | What it actually means                                                       |
|--------------|------------------------------------------------------------------------------|
| **EE**        | End-Effector — the very last link of the arm where the gripper bolts on. For our myCobot 280 Pi it is the URDF link `tool0`. |
| **ArUco marker** | A printable black-and-white square that OpenCV can detect and locate in 6-DoF. We use it as a calibration landmark. Built in exercise [`10-aruco-pose/`](../10-aruco-pose/). |
| **TF**        | ROS 2's "frame tree" — keeps track of where every link is relative to every other link. The arm's controller publishes `base_link → tool0` for free. |

## What is moving during calibration

**Not the camera.** Our overhead camera is bolted to the ceiling
and never moves. The marker is glued to the **end-effector**, and
the **arm** moves through 20 different poses.

```
   ┌────────📷────────┐    overhead camera, BOLTED to the ceiling
   │                  │    (never moves during calibration)
   │      ┌──┐        │
   │      │  │        │
   │   ┌──┤  ├──┐     │
   │   │  └──┘  │     │      arm  (this DOES move)
   │   │   📍   │     │      📍 the ArUco marker is on the EE,
   │   │        │     │         so it moves WITH the arm
   │   ●────────●     │
   └──────────────────┘    bench
```

Per pose we save two things:

- Where the **arm** thinks its EE is (from TF — the arm always
  knows this from its joint encoders).
- Where the **camera** sees the marker (from the ArUco detector in
  exercise 10).

After 20 such "double views" of the same physical point, we have
enough constraints to pin down `T_base_cam` uniquely.

## Eye-in-hand vs eye-to-hand

Two physical layouts. Same math; the labels flip.

```
EYE-IN-HAND (camera on the wrist)        EYE-TO-HAND (overhead, fixed)
                                          ── this exercise ──

     ┌──┐                                       ┌──📷──┐
     │📷│  ← camera moves with EE              bench / ceiling
     ├──┤                                       │
     │  │  arm                                  │
     ├──┤                                       ┌──┐
     │  │                                       │  │ arm
                                                ┌──┐
        marker sits on the bench               📍   ← marker on EE
        we solve:  T_ee_cam                     we solve:  T_base_cam
```

Even with the camera bolted to the wrist (eye-in-hand), you still
need calibration: bracket slop, lens recess, and sensor offset add
up to an unknown few-cm transform between the camera lens and
`tool0`. The procedure is identical; only the labels change.

## The math, in one sentence

For every sample, the marker can be reached two ways through the
kinematic chain — through the arm, and through the camera. Those
two paths must agree. With 20 pose pairs, OpenCV solves the only
camera transform that makes all 20 agreements consistent.

```
                  ┌── T_base_ee_i ──► EE ── T_ee_marker ──►┐
        BASE ─────┤                                        ├── MARKER
                  └── T_base_cam ───► CAM ── T_cam_marker_i►┘
```

That is the **AX = XB** problem; `cv2.calibrateHandEye` solves it.

## What we feed the solver

| Input list (N=20)        | Where it comes from                                                           |
|--------------------------|-------------------------------------------------------------------------------|
| `R_base_ee_i, t_base_ee_i` | TF lookup `base_link → tool0` at the time the marker frame was captured     |
| `R_cam_marker_i, t_cam_marker_i` | ArUco detector — `/aruco/markers` from exercise 10                    |

20 samples is a rule of thumb. More matters less than **pose
variety** — the arm must *rotate* the marker, not just translate
it. The collector drops samples within 5 cm of any existing sample
to enforce some spread.

## What "Done when" means here

The checklist asks: *"re-projecting a fresh marker detection lands
within 5 mm of the marker's true position."*

The script prints:

1. The solved `(x, y, z, roll, pitch, yaw)` for `T_base_cam`.
2. A ready-to-paste `static_transform_publisher` command — pop it
   into a launch file and TF carries the camera ↔ base relationship
   for free from then on.
3. The residual mean / std after the fit — sub-millimetre in
   Gazebo, 1–3 mm with a real 30 mm marker and a 1080p camera.

Once the static TF is published, **any downstream node** does:

```python
self._tf_buf.transform(centroid_in_cam, "base_link")
```

…and the camera ↔ arm dictionary is applied automatically. That
single line is the entire payoff of this exercise.

## Run it (concept only — script not exercised here)

Assumes exercise 10's ArUco detector is publishing, and the arm is
being walked through 20 varied poses.

```bash
python3 hand_eye_calibrate.py --ros-args \
    -p marker_topic:=/aruco/marker_pose \
    -p ee_frame:=tool0 \
    -p base_frame:=base_link \
    -p num_samples:=20
```

Sample output:

```
sample 1/20 captured
...
sample 20/20 captured
=== T_base_cam ===
  translation: x=0.0500  y=0.0000  z=1.3000  metres
  rotation:    roll=3.1416  pitch=-0.0000  yaw=-0.0000  rad
static TF command:
  ros2 run tf2_ros static_transform_publisher \
      --x 0.0500 --y 0.0000 --z 1.3000 \
      --roll 3.1416 --pitch 0.0000 --yaw 0.0000 \
      --frame-id base_link --child-frame-id overhead_camera_optical_frame
residual mean=0.84 mm  std=0.31 mm
```

## What this exercise is **not**

- **Not the ArUco detector** — that lives in exercise 10. This node
  *consumes* its output topic.
- **Not the 20-pose arm dance** — one for-loop over exercise 19's
  `setPoseTarget`; not duplicated here.
- **Not a continuous TF publisher** — output is a *static*
  transform; `static_transform_publisher` does the publishing.

## What's next

With this exercise done, the full v1 perception → motion pipeline
is conceptually complete:

```
RGB-D camera ─► YOLOv8-seg (item 7) ─► instance_mask + detections
                                              │
                                              ▼
                                      centroid_node (item 8)
                                              │  centroid in camera frame
                                              ▼
                                      tf2 transform (this exercise)
                                              │  centroid in BASE frame
                                              ▼
                                      pick controller (item 21)
                                              │  approach → grasp → lift
                                              ▼
                                            MoveIt
                                              │
                                              ▼
                                             arm
```

Remaining checklist items add **robustness**, not new capability:
F/T sensing (15), gripper contact (17), colour segmentation (13),
barcodes (14). Each is useful, none is on the critical path.
