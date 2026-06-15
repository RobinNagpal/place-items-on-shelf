# Synthetic data — Step 2: object-pose randomisation

## TL;DR

The simplest possible object-pose randomisation pass.

- The **camera stays put** at the straight-down overhead view.
- Every frame, the four labelled objects on the bench
  (`solvent_bottle`, `beaker_1`, `beaker_2`, `beaker_3`) are teleported
  to a new random (x, y, yaw): ±5 cm of translation and ±20° of yaw.
- Five frames are captured by default, mirroring the camera-pose step.
- The same YOLO `.txt` + green-rectangle overlay pipeline that
  `move_camera.py` already uses now reads each object's *randomised*
  pose instead of the SDF default.

This implements axis #2 of the six domain-randomisation axes listed
in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md):

| # | Axis              | Where it lives                              |
|---|-------------------|---------------------------------------------|
| 1 | Camera pose       | `move_camera.py`                            |
| 2 | Object pose       | `randomize_objects.py`  **<-- this file**   |
| 3 | Lighting          | not yet                                     |
| 4 | Materials         | not yet                                     |
| 5 | Distractors       | not yet                                     |
| 6 | Background        | not yet                                     |

## What it actually does

`randomize_objects.py`:

1. **Subscribes** to `/overhead_camera/image_raw` via the gz-transport
   Python bindings, just like `move_camera.py`.
2. **Parks the camera** at the fixed overhead pose
   `CAMERA_POSITION = (0.05, 0.00, 1.50)` aimed at
   `LOOK_AT_TARGET = (0.05, 0.0, 0.94)` — set once at startup and
   never touched again.
3. For each of N frames (default 5):
   - **Rolls a new (x, y, yaw) per object** using
     `random.Random(seed)` so the run is reproducible. Jitter
     ranges are `TRANS_JITTER_M = 0.05` (±5 cm in x and y) and
     `YAW_JITTER_RAD = math.radians(20)` (±20° about world z). z is
     held at the SDF default so the objects stay on the bench top.
   - **Teleports** every object with one
     `gz service /world/.../set_pose` call each.
   - **Waits** `--dwell` seconds (default 2 s) so the sensor
     publishes a fresh frame for the new layout.
   - **Saves** `captured_frames/frame_NN.png` plus a sibling
     `frame_NN.txt` (YOLO labels) and, if overlays are enabled,
     `captured_frames/overlays/frame_NN_bbox.png`.
   - **Appends** one JSON line to `captured_frames/poses.jsonl`
     recording every object's exact pose. This makes the dataset
     fully reproducible from disk alone, even without re-running
     the script.

NO ROS. NO `ros_gz_bridge`. NO `cv_bridge`. NO manual labelling.

## Run it — two terminals

Same recipe as `move_camera.py`. Both terminals must be in the repo
root.

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

### Terminal 2 — randomise + capture

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/randomize_objects.py
```

Defaults: 5 frames, 2 s dwell, seed 0. So one run produces 5 PNGs.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../place-items-on-shelf/captured_frames/
YOLO classes file    /home/.../captured_frames/classes.txt  (2 class(es), 4 object(s))
image intrinsics     640x480  hfov=60deg  fx=554.3
camera (fixed)       pos=(0.05, 0.0, 1.5)  aim=(0.05, 0.0, 0.94)  pitch=+90deg yaw=+0deg
random seed          0  (jitter: +/-5 cm x/y, +/-20 deg yaw)
bbox overlays to     /home/.../captured_frames/overlays/  (disable with --no-overlay)

waiting for the first frame ...
first frame received after 0.4 s (got 1 frames so far).

[frame 00]
  set_pose   solvent_bottle: pos=(+0.134, +0.276, +0.975)  yaw=-3.1deg  OK
  set_pose         beaker_1: pos=(+0.026, -0.299, +0.935)  yaw=-3.8deg  OK
  set_pose         beaker_2: pos=(+0.078, -0.200, +0.935)  yaw=-0.9deg  OK
  set_pose         beaker_3: pos=(+0.058, -0.019, +0.935)  yaw=+0.2deg  OK
  -> /home/.../captured_frames/frame_00.png  (640x480)  labels=4 -> frame_00.txt  overlay=4 -> overlays/frame_00_bbox.png
...
done. saved 5 PNGs -> /home/.../captured_frames/
      per-frame poses -> /home/.../captured_frames/poses.jsonl
```

Useful flags:

```bash
# Capture 20 frames instead of 5.
python3 .../randomize_objects.py --frames 20

# Use a different seed -> a different (still deterministic) dataset.
python3 .../randomize_objects.py --seed 42

# Spend longer at each pose (helps if your render is slow).
python3 .../randomize_objects.py --dwell 4

# Save somewhere else.
python3 .../randomize_objects.py --out /tmp/my_dataset

# Skip the green-rectangle overlays.
python3 .../randomize_objects.py --no-overlay
```

## Where the images and labels land

By default: `./captured_frames/` relative to wherever you launched
the script. After one run with defaults:

```
captured_frames/
├── classes.txt                  # 'solvent_bottle' and 'beaker', one per line
├── frame_00.png                 # the image
├── frame_00.txt                 # the YOLO label for that image
├── frame_01.png
├── frame_01.txt
├── frame_02.png
├── frame_02.txt
├── frame_03.png
├── frame_03.txt
├── frame_04.png
├── frame_04.txt
├── poses.jsonl                  # one JSON line per frame; what object went where
└── overlays/                    # bbox-annotated copies for visual QA only
    ├── frame_00_bbox.png
    ├── frame_01_bbox.png
    ├── frame_02_bbox.png
    ├── frame_03_bbox.png
    └── frame_04_bbox.png
```

`classes.txt` now has **two** classes (the solvent bottle plus the
shared `beaker` class for the three beakers), so the YOLO trainer
sees a multi-class problem out of the box. To collapse beakers into
the same class as the bottle, edit `class_id` for the beaker entries
in `RANDOMISED_OBJECTS`.

`poses.jsonl` is plain JSON-lines, one per frame:

```
{"frame": 0, "image": "frame_00.png", "objects": [
  {"class_id": 0, "class_name": "solvent_bottle", "model": "solvent_bottle",
   "x": 0.134, "y": 0.276, "z": 0.975, "yaw": -0.055},
  ...
]}
```

Cross-checking a label against the log is straightforward — match
`frame.image` to the PNG file name and you have every object's exact
(x, y, z, yaw) for that frame.

### How the labels are computed (now that objects can move and yaw)

Same projection plumbing as `move_camera.py`, with one extra step at
the top:

1. The **per-frame** randomised `(x, y, yaw)` for each object is
   pulled from the seeded RNG (`jittered_poses()`).
2. The object's **local AABB** (from its SDF geometry — stored once
   in `RANDOMISED_OBJECTS`) gets transformed to world coords by
   rotating its 8 corners about world `z` by `yaw` and translating
   by `(x, y, z)`. That gives 8 world points that wrap the object
   in its current pose.
3. Each world point is projected to a pixel through the **fixed**
   camera pose using the same pinhole math as `move_camera.py`.
4. The axis-aligned bbox of the 8 projected pixels is clamped to
   `[0, W] x [0, H]` and written to the YOLO `.txt`.

The local-frame AABB is symmetric in x/y for every model in this
world (all are upright cylinders), so yaw doesn't actually change
the world-space AABB for cylinders. The code applies the rotation
anyway so the same path will work for non-cylindrical models
(e.g. a clamp, a vial holder) we may add later.

## Troubleshooting

Most failure modes are shared with `move_camera.py` — see its
README for the gz-transport / version / topic / set_pose checklist.
Object-pose specific:

- **`set_pose <name>: FAIL` on every line.** The model name in
  `RANDOMISED_OBJECTS` does not match a model in the world. Check
  `gz model -l` (or grep for `<model name="...">` in
  `ketchup_extraction.sdf`).

- **Bboxes drift off the object after a few frames.** The script
  *teleports* (instant `set_pose`) — physics has no time to settle.
  Either bump `--dwell` so the sensor publishes after the move, or
  drop physics by editing the SDF (`<plugin name=...Physics...>`).
  The current 2 s dwell is plenty on the test machine.

- **An object is missing from the overlay.** Either the random
  pose pushed it outside the image (legitimate — its `.txt` line
  is omitted), or its model name in the world differs from the
  `RANDOMISED_OBJECTS` entry. Check the run log for the matching
  `set_pose ... OK` line.

- **The dataset is non-deterministic between runs.** Make sure you
  pass `--seed`. The default is `0`, but if you change the order of
  entries in `RANDOMISED_OBJECTS`, the same seed yields a *different*
  sequence because the RNG calls happen in entry order.

## Next axis

The next thing to add (axis #3) is **lighting**: vary the world's
`<light>` direction / colour temperature / intensity each frame.
The plumbing is identical — call `gz service set_pose` on a `<light>`
target — but it requires the world SDF to expose the lights as
named entities. That is a future PR.
