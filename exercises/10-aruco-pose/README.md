# 10 — ArUco marker 6-DoF pose estimation

Implements checklist item **10** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Adds an **object-locator channel** alongside the YOLO pipeline from
items 4 / 7 / 8. Used at **runtime** to find the source rack and
destination tray every cycle; also used **once at install** by
exercise 12 for hand-eye calibration.

## What this exercise is actually for

> Glue a small printed square — an **ArUco marker** — on any
> object you control, and the camera tells you that object's full
> **6-DoF pose** (position + orientation) every frame, in real time.

That is the entire capability. The marker only detects *itself* in
the image, but because:

- You stuck it at a **known place** on the object, AND
- You already know the **object's geometry** from CAD / spec sheet,

…the marker's pose gives you every other point on the object too.
For our autosampler that means **the source rack and destination
tray report their exact position every frame**, and we can hand
any slot's pose to MoveIt for an arm pick.

```
overhead camera ──► aruco_detector_node ──► /aruco/markers
                                                 │
                                                 ▼
                                       slot-pose helper
                              (marker pose · CAD offset = slot pose)
                                                 │
                                                 ▼
                                          tf2 transform
                                                 │
                                                 ▼
                                            MoveIt ──► arm picks
```

Calibration is another use of the same node (exercise 12), but
runtime tray-location is the bigger use.

## What an ArUco marker is

A small black-and-white square pattern, kind of like a tiny QR
code. Anyone can print one on a sheet of paper.

```
       30 mm × 30 mm
   ┌────────────────┐
   │ ████████ ██████│
   │ ██    ██ ██  ██│      <- internal 4×4 black/white grid
   │ ██ ██ ██ ██████│         encodes a numeric ID (0..49 for
   │ ██    ██ ██  ██│         DICT_4X4_50)
   │ ████████ ██  ██│
   │ ██████████████ │      <- the thick black border is what makes
   └────────────────┘         the detector locate the 4 corners
                              cheaply and unambiguously
```

It gives us three things for free:

1. A robust visual signal — the high-contrast border is found
   reliably even at oblique angles.
2. A unique ID per marker — `DICT_4X4_50` has 50 distinct IDs; we
   use a different one per tray so the camera can tell them apart.
3. A known size — we print it at 30 mm; that known physical size
   is what unlocks the 6-DoF pose recovery.

## The autosampler use case (primary)

Glue one ArUco marker per tray, at a known corner of each tray.

```
                          camera
                            📷
                            │
                            ▼
   ┌───────────────────┐         ┌───────────────────┐
   │ ░░░░░░░░░░░░░░░░░ │         │ ░░░░░░░░░░░░░░░░░ │
   │ ░░  vials in 5×10 │         │ ░░ empty 10×10    │
   │ ░░  slots         │         │ ░░ slots          │
   │ ░░░░░░░░░░░░░░░░░ │         │ ░░░░░░░░░░░░░░░░░ │
   │ ┌──┐              │         │ ┌──┐              │
   │ │📍│  aruco_0     │         │ │📍│  aruco_1     │
   │ └──┘              │         │ └──┘              │
   └───────────────────┘         └───────────────────┘
       SOURCE RACK                  DESTINATION TRAY
       (MicroSolv 50)               (Agilent 100)
```

From a single image the node publishes:

```
/aruco/markers
   detections:
     - class_id: "aruco_0",  pose: (x, y, z, rx, ry, rz)   ← source rack corner
     - class_id: "aruco_1",  pose: (x, y, z, rx, ry, rz)   ← destination tray corner
```

That's the **complete output** for the autosampler. Two markers,
two poses, every frame. The arm now knows where both trays sit
relative to the camera, even if a lab tech bumped one of them.

## Where the object geometry comes from (your question)

You asked whether we get the object's geometry from Gazebo. The
clean answer is **the geometry is a fixed constant, not a runtime
measurement.** The source depends on whether you're in sim or in a
real lab:

| Environment           | Where the geometry comes from                                              |
|-----------------------|----------------------------------------------------------------------------|
| **Our Gazebo sim**     | The **SDF file we wrote**. We placed the rack at a known size and slot layout, so we know every dimension by construction. |
| **A real lab**         | The **manufacturer's spec sheet**. MicroSolv publishes the dimensions of the 50-slot rack; Agilent publishes the 100-slot tray. These live in [`docs/hplc-autosamplers/requirements/`](../../docs/hplc-autosamplers/requirements/). |
| **A custom fixture**   | **CAD** — whoever designed the fixture has a `.STEP` file with every dimension. |
| **A part you measured** | **Calipers, once.** Write the dimensions into a YAML.                      |

In every case the dimensions are **typed into code as constants**
before the system runs. The camera does not need to measure them
and could not even if we wanted it to — the ArUco detector only
sees the marker square, not the tray it's glued to.

This is also why ArUco is so reliable: there is no "measurement
error on the object's size" at runtime, because the size was never
measured at runtime in the first place.

## From marker pose to slot pose (the recipe)

We know two things ahead of time:

```python
# From the MicroSolv spec sheet (or our SDF):
RACK_LAYOUT = {
    "rows": 5, "cols": 10,
    "slot_spacing_x_m": 0.014,        # 14 mm centre-to-centre
    "slot_spacing_y_m": 0.014,
    "marker_offset_x_m": -0.007,      # marker corner sits 7 mm short of slot A1
    "marker_offset_y_m": -0.007,
    "vial_top_z_m": 0.032,            # cap top 32 mm above the rack base
}
```

The slot-pose helper is then one tiny function:

```python
def slot_pose_in_camera_frame(marker_pose, slot_col, slot_row):
    """Apply a fixed offset from the marker to a specific slot."""
    dx = RACK_LAYOUT["marker_offset_x_m"] + slot_col * RACK_LAYOUT["slot_spacing_x_m"]
    dy = RACK_LAYOUT["marker_offset_y_m"] + slot_row * RACK_LAYOUT["slot_spacing_y_m"]
    dz = RACK_LAYOUT["vial_top_z_m"]
    return marker_pose @ translation_matrix(dx, dy, dz)
```

50 slots → 50 fixed offsets → 50 poses, all derived from one
marker observation. If the tray gets bumped 2 cm, the marker pose
shifts 2 cm and every slot pose shifts with it. No retraining, no
manual reset.

## End-to-end pick using ArUco (no calibration loop running)

This is the runtime flow the autosampler will use every cycle.
Calibration is done once at install (exercise 12) and `T_base_cam`
is in TF; from then on the loop is:

```
1.  Camera takes a frame.
2.  aruco_detector_node publishes:
        /aruco/markers:
          aruco_0  → marker_pose_in_cam_0 (source rack)
          aruco_1  → marker_pose_in_cam_1 (destination tray)
3.  Slot-pose helper applies CAD offsets:
        slot_B3_pose_in_cam = marker_pose_in_cam_0 · offset_B3
4.  TF turns it into base frame using T_base_cam (item 12):
        slot_B3_pose_in_base = T_base_cam · slot_B3_pose_in_cam
5.  Pick controller hands slot_B3_pose_in_base to MoveIt.
6.  MoveIt plans + executes. Arm picks the vial.
```

That is a complete perception-driven pick that uses **ArUco alone
plus known geometry**. No YOLO, no depth, no machine learning, no
re-calibration. This is the most common production pattern for any
robot cell whose layout you control.

## How the camera detects the marker (step by step)

The detector pipeline runs entirely on a **single 2D RGB image**:

```
       1. take one frame (640 × 480 BGR)
              │
              ▼
       2. convert to grayscale
              │
              ▼
       3. adaptive threshold (separate black vs white)
              │
              ▼
       4. find contours; keep those that look like a 4-corner polygon
              │
              ▼
       5. for each candidate quad:
              warp it to a flat top-down view
              read the internal grid bits
              look the bit pattern up in the dictionary
              accept if the bit pattern matches a known ID
              │
              ▼
       6. return for each accepted marker:
              - the 4 corner pixel coordinates ((u, v) each)
              - the integer ID
```

That is what `cv2.aruco.detectMarkers(gray)` does in ~3–5 ms per
frame. It does **not** yet know where the marker is in 3D — only
where it is in the image.

## From 2D corners to 3D pose — and why 2D RGB is enough

You asked whether we need a depth (RGB-D) camera. **We don't.**

We know:

- The marker is a flat 30 mm × 30 mm square. Its 4 corners sit at
  fixed positions in the marker's own frame:
  `(-15, +15, 0)`, `(+15, +15, 0)`, `(+15, -15, 0)`, `(-15, -15, 0)`
  in millimetres.
- After detection we know the **pixel coordinates** of those same
  4 corners in the image.
- We know the camera's **intrinsics** (focal length, optical
  centre) from the SDF.

That gives us **4 known 3D-to-2D correspondences**. This is exactly
the input to a classical problem called **Perspective-n-Point
(PnP)** — *"given N known 3D points and their projections in an
image, find the camera pose."* For 4 coplanar points, there is a
unique solution and `cv2.solvePnP` returns it.

```
  marker frame                     camera frame
  ────────────                     ────────────

   (-15, +15)  ────► (u_TL, v_TL)
   (+15, +15)  ────► (u_TR, v_TR)         cv2.solvePnP   ┌─ tvec (X, Y, Z) in metres
   (+15, -15)  ────► (u_BR, v_BR)   ───────────────────► │
   (-15, -15)  ────► (u_BL, v_BL)                        └─ rvec (rotation)
   millimetres        pixels
```

The **known marker size** is what removes the distance ambiguity.
A 30 mm square that covers 36 pixels says "camera is X away"; the
same 30 mm at 18 pixels says "camera is 2X away". Depth would be
redundant.

If you swapped our overhead camera for a $20 webcam with no depth
sensor, this exercise would work identically.

## What information arrives in ROS

The node publishes one topic, `vision_msgs/Detection3DArray`:

```
/aruco/markers
   header.frame_id  = camera optical frame

   detections[i].bbox.center
       position.x, .y, .z      = marker centre in metres (camera frame)
       orientation.x..w        = marker orientation as a quaternion

   detections[i].bbox.size
       x = y = marker_size, z ≈ 0

   detections[i].results[0].hypothesis.class_id = "aruco_3"     (marker ID)
   detections[i].results[0].hypothesis.score    = 1.0           (PnP solved or didn't)
```

So per marker: **one 6-DoF pose + one integer ID**. That's the
whole channel. Everything else (tray dimensions, slot layout, vial
diameter) is constants in your code.

## What ArUco does NOT pass back

Worth being explicit, since the README before mis-emphasised this:

- **Not the tray's dimensions.** Those are typed-in constants from
  the spec sheet / SDF. The camera doesn't measure them.
- **Not the slot positions.** Computed from marker pose +
  CAD offsets.
- **Not vial positions.** Vials don't have markers; that's YOLO
  (items 7 / 8).
- **Not depth.** No depth camera involved.
- **Not the tray's outline / shape.** Just one 6-DoF pose per
  marker.

## ArUco vs YOLO — different tools for different objects

| Object kind                               | Best tool                      |
|-------------------------------------------|--------------------------------|
| Things you control (trays, fixtures, jigs)| **ArUco** (this exercise)      |
| Things you can mark once                  | **ArUco**                      |
| Things you can't mark (vials, parts)      | **YOLO / segmentation** (items 7 / 8) |
| Things whose shape you don't know         | **Point-cloud clustering**     |

ArUco is fast (~5 ms), zero-training, sub-mm-precise. YOLO handles
variety, occlusion, and things you can't physically mark. Real
cells use both: ArUco for the structure, YOLO for what's inside.

## Sidebar — using ArUco for hand-eye calibration

The same node is used **once at install** by exercise 12. We
temporarily glue a marker to the end-effector, move the arm
through 20 poses, and run `cv2.calibrateHandEye` against the
poses this node reports. The marker is removed afterwards. See
[`../12-hand-eye-calibration/`](../12-hand-eye-calibration/) for
the math. Calibration is a *one-time* use; the tray-locator use
above runs every cycle, forever.

## What "Done when" means here

The checklist asks: *"6-DoF pose of the marker is published every
frame, with sub-degree orientation error in Gazebo."*

We don't ship a scorer. The Gazebo model state for the marker
plate (if you SDF-mount it) is the ground truth — compare against
the published `/aruco/markers` entry. Exercise 05's
`/gazebo/pose_info` bridge already gives you the plumbing.

## Run it

```bash
# 1. Exercise 04's launch must already be up (overhead camera + bridge).
ros2 launch yolo_live_demo yolo_live.launch.py

# 2. Run this node:
python3 aruco_detector_node.py --ros-args \
    -p image_topic:=/overhead_camera/image_raw \
    -p marker_size_m:=0.030 \
    -p dictionary:=DICT_4X4_50

# 3. Sanity check:
ros2 topic hz /aruco/markers
ros2 topic echo /aruco/markers --once
```

To see markers in Gazebo you need a textured marker plate in the
SDF. The PNG comes from `cv2.aruco.generateImageMarker(...)`; see
`IMPLEMENTATION_NOTES.md` for the SDF model block.

## What this exercise is **not**

- **Not a vial detector** — that's YOLO.
- **Not a 3D / depth pipeline** — operates on a flat RGB image.
- **Not the slot-pose helper** — that's domain code that belongs
  next to the pick controller, not the perception node.
- **Not tied to one use case** — same node works for tray
  locators, fixture locators, and the calibration marker on the EE.

## What's next

- **Slot-pose helper** (small follow-on) — a library that maps
  `aruco_<id>` + slot index → `geometry_msgs/Pose` for the pick
  controller. ~30 lines of CAD-offset math.
- **Item 12** — hand-eye calibration. Consumes this topic *once*.
- **Item 14** — QR codes on vial caps for per-vial identity (we
  identify *trays* with ArUco; *vials* would use QR / barcode).
