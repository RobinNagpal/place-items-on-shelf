# 10 — ArUco marker 6-DoF pose estimation

Implements checklist item **10** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Adds a second, complementary perception channel to the YOLO
pipeline from items 4 / 7 / 8. Used by exercise **12** (hand-eye
calibration) and by the source/destination tray locator that the
autosampler needs.

## What this exercise actually does, in one paragraph

Stick a small printed square (an **ArUco marker**) on something
physical — for us, on the **source tray** and the **destination
tray**. OpenCV's `cv2.aruco` reads a plain RGB image from the
overhead camera, finds every marker square in the frame, and
returns each one's full **6-DoF pose** — *(x, y, z, roll, pitch,
yaw)* — in the camera frame. We then know exactly where every tray
is, and because each tray has its own marker ID, we also know
*which* tray is *which*.

No depth camera needed. No machine learning needed. One image,
some geometry, and a known marker size are enough.

## What an ArUco marker actually is

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

Three things this gives us for free:

1. **A robust visual signal.** The border is high-contrast; the
   detector finds the 4 corners even at oblique angles or in
   imperfect lighting.
2. **A unique ID per marker.** The internal pattern encodes a
   number. `DICT_4X4_50` has 50 unique IDs; bigger dictionaries
   (`DICT_6X6_250`, `DICT_ARUCO_ORIGINAL`) have more.
3. **A known size.** *We* printed it at 30 mm. That known physical
   size is what unlocks the 6-DoF pose recovery.

## How the camera detects it (step by step)

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
              accept the candidate if the pattern matches an ID
              │
              ▼
       6. return for each accepted marker:
              - the 4 corner pixel coordinates (the (u, v) of each corner)
              - the integer ID
```

That is what `cv2.aruco.detectMarkers(gray)` does in ~3–5 ms per
frame at 640 × 480 on a modern CPU. It does **not** yet know where
the marker is in 3D — only where it is in the image.

## From 2D corners to 3D pose — and why a plain 2D camera is enough

This is the question you asked: do we need an RGB-D camera, or is
2D enough? **2D is enough.** Here is why.

We know:

- The marker is a flat 30 mm × 30 mm square. So its 4 corners are
  at fixed positions in the **marker's own frame**:
  `(-15, +15, 0)`, `(+15, +15, 0)`, `(+15, -15, 0)`, `(-15, -15, 0)`
  in millimetres.
- After detection we know the **pixel coordinates** of those same
  4 corners in the image.
- We know the camera's **intrinsics** — focal length and the
  optical centre, from the SDF.

That gives us **4 known 3D-to-2D correspondences**. This is exactly
the input to a classical computer-vision problem called
**Perspective-n-Point (PnP)** — *"given N known 3D points and their
projections in an image, find the camera pose."* For N = 4 coplanar
points, there is a unique solution (up to an ambiguous flip that
the algorithm handles internally), and `cv2.solvePnP` returns it.

```
  marker frame                     camera frame
  ────────────                     ────────────

   (-15, +15)  ────► (u_TL, v_TL)
   (+15, +15)  ────► (u_TR, v_TR)         cv2.solvePnP   ┌─ tvec (X, Y, Z)
   (+15, -15)  ────► (u_BR, v_BR)   ───────────────────► │
   (-15, -15)  ────► (u_BL, v_BL)                        └─ rvec (rotation)
   millimetres        pixels
```

Output is two short vectors:

- `tvec` — `(X, Y, Z)` of the marker centre **in metres**, in the
  camera frame.
- `rvec` — axis-angle rotation of the marker, also in the camera
  frame. Converts trivially to a quaternion or a rotation matrix.

**This is why depth is unnecessary.** The known marker size *plus*
the known camera intrinsics already constrain the distance — a
30 mm square that occupies 20 pixels on screen *must* be ~0.83 m
away. Depth would be an extra channel of redundant info.

If you swapped the overhead camera for a webcam with no depth
sensor, this exercise would work identically. (If you ever want
the depth-redundancy check for noise rejection, exercise 8's
depth lookup pattern transfers — but it's optional.)

## What information arrives in ROS

The node publishes one topic, `vision_msgs/Detection3DArray`:

```
/aruco/markers
   header.frame_id  = camera optical frame   (from the input image)

   detections[i].bbox.center
       position.x, .y, .z      = marker centre in metres   (camera frame)
       orientation.x..w        = marker orientation as a quaternion

   detections[i].bbox.size
       x = y = marker_size, z ≈ 0           (marker is flat)

   detections[i].results[0].hypothesis.class_id = "aruco_3"   (marker ID)
   detections[i].results[0].hypothesis.score    = 1.0         (PnP either solved or didn't)
```

So for each detected marker, the camera passes one **PoseStamped-
shaped chunk of data** (6-DoF pose) plus the **integer ID** that
identifies which marker it is. **It does NOT pass the tray's
dimensions** — those are already known to us; the camera doesn't
need to measure them.

Concretely, if `aruco_3` is glued to the source tray, the message
above answers two questions at once:

- *Which tray is this?* → `class_id = "aruco_3"` → "source tray".
- *Where is the tray right now?* → `bbox.center` → 6-DoF pose of
  the marker, which is at a known offset from the tray origin.

## Putting markers on the source / destination trays

The autosampler use case has two trays: a source rack and a
destination tray. We stick **one ArUco marker per tray** at a
known location — typically the front-left corner. Pick a different
marker ID for each tray (e.g. `aruco_0` for source, `aruco_1` for
destination). From a single image:

```
   detections = aruco/markers
   marker_pose[0]   ← source tray corner
   marker_pose[1]   ← destination tray corner
```

The trays themselves do not need any markings on the slots
because we already know the **rack geometry** from CAD:

| Tray            | Marker ID | Marker location                  | Slot layout (known)       |
|-----------------|-----------|----------------------------------|---------------------------|
| Source rack     | 0         | Front-left corner of the rack     | 5 × 10 grid, 14 mm centres |
| Destination tray | 1         | Front-left corner of the tray     | 10 × 10 grid, 14 mm centres |

To find slot `B3` we apply a fixed local offset to the marker pose:

```python
# tray_marker_pose is the 6-DoF pose of the marker on the source tray.
# slot_local = the slot's (x, y) relative to the marker, from CAD.
# Both expressed in METRES.
slot_b3_local = np.array([0.014 * 2, 0.014 * 1, 0.0])   # column B, row 3
slot_b3_pose  = tray_marker_pose @ make_transform(slot_b3_local)
```

That single multiplication turns *"the source rack got bumped 2 cm
to the right when the tech loaded it"* into the new pose of every
one of its 50 slots, in one shot. No retraining, no manual reset.

## What the camera DOES NOT pass back

A list to remove confusion:

- **It does not pass the tray's physical dimensions.** Those are
  hard-coded from CAD. The camera only locates *one point* on the
  tray (where the marker is glued).
- **It does not pass vial positions.** YOLO (item 7 / 8) does
  that. ArUco is for things you control (trays, fixtures); YOLO is
  for things you can't (vials).
- **It does not pass depth.** No depth camera is used here.
- **It does not pass the tray's outline or contour.** Just one
  6-DoF pose per marker.

## Why ArUco alongside YOLO?

| Detects               | YOLO (items 4 / 7)                     | ArUco (this exercise)                |
|-----------------------|----------------------------------------|--------------------------------------|
| Source                | Pixel patterns learned from data       | A printed marker we glue on          |
| Use case              | Vials, caps, dynamic objects            | Trays, fixtures, the EE for calibration |
| Latency               | ~30–100 ms / frame                     | ~3–5 ms / frame                      |
| Failure mode          | Occasionally drops or mis-classifies    | Either detected perfectly or not at all |
| 6-DoF pose            | Bbox in 2D; depth from item 8           | 6-DoF straight from the detector     |

ArUco is the **deterministic, low-latency channel**: trays do not
move much, so we only need a coarse pose, and we want it to be
rock-solid when we re-home the system after a tray bump.

## What "Done when" means here

The checklist asks: *"6-DoF pose of the marker is published every
frame, with sub-degree orientation error in Gazebo."*

We do not ship a scorer. The Gazebo model state for the marker
plate (if you SDF-mount it) is the ground truth — compare its true
pose with the published `/aruco/markers` entry. Exercise 05's
`/gazebo/pose_info` bridge already gives you the GT plumbing.

## Run it

```bash
# 1. exercise 04's launch must already be up (overhead camera + bridge).
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

To actually see markers in Gazebo you need a textured marker plate
in the SDF. The 4×4 PNG images for every ID come from
`cv2.aruco.generateImageMarker(dictionary, id, 200)` — see
`IMPLEMENTATION_NOTES.md` for the SDF snippet.

## What this exercise is **not**

- **Not the hand-eye calibrator** — that's exercise 12; it
  *consumes* this node's topic.
- **Not a vial detector** — YOLO does that.
- **Not a depth or 3D pipeline** — operates on a flat RGB image.
- **Not tied to the trays specifically** — same node works for a
  marker on the EE (the calibration use case) or anywhere else.

## What's next

- **Item 12** — hand-eye calibration. The single biggest consumer
  of this node.
- **Slot-pose helper** (not on the checklist) — a small library
  that maps `aruco_<id>` + slot index → `geometry_msgs/Pose` for
  the pick controller.
- **Item 14** — QR codes on vial caps for per-vial identity (we
  identify *trays* with ArUco; *vials* would use QR / barcode).
