# Synthetic data — camera frames of the bench

This folder contains the synthetic-data scripts for the dissolution /
extraction world. Each script implements one of the six
domain-randomisation axes from
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md).

| # | Axis              | Script                    | Status |
|---|-------------------|---------------------------|--------|
| 1 | Camera pose       | `move_camera.py`          | **Done** — this README |
| 2 | Object pose       | `randomize_objects.py`    | **Done** — see [`README_object_pose.md`](README_object_pose.md) |
| 3 | Lighting          | `randomize_lighting.py`   | **Done** — see [`README_lighting.md`](README_lighting.md) |
| 4 | Materials         | —                         | not yet |
| 5 | Distractors       | `randomize_distractors.py`| **Done** — see [`README_distractors.md`](README_distractors.md) |
| 6 | Background        | `randomize_background.py` | **Done** — see [`README_background.md`](README_background.md) |

The rest of *this* file documents `move_camera.py` (axis #1). For the
object-pose script (axis #2), see
[`README_object_pose.md`](README_object_pose.md).

## Step 1 — `move_camera.py` (camera-pose variation)

Two pieces:

1. **`ketchup_extraction.sdf`** — already has an `overhead_camera`
   model with a sensor that publishes RGB frames on the Gazebo
   Transport topic `/overhead_camera/image_raw`.
2. **`move_camera.py`** — a single Python script that:
   - **subscribes** to that topic via the gz-transport Python
     bindings,
   - **teleports** the camera through five preset positions
     (top + front + back + left + right) using `gz service set_pose`,
   - **aims** each camera at a fixed `LOOK_AT_TARGET` on the bench
     (so the scene is always centred — the orientation is computed
     from the position, never hand-written),
   - **saves** the latest frame to disk as a PNG after each pose,
   - **also writes a YOLO label `.txt`** next to each PNG, by
     projecting the solvent bottle's known world-space bounding
     box through a pinhole camera model with the same intrinsics
     as the SDF camera. Single class for now
     (`solvent_bottle`, class id 0) — multi-class is a few extra
     lines in `LABELED_OBJECTS`,
   - **also saves a debug overlay PNG** under `<out>/overlays/`
     with the bbox drawn in green directly on the image, so you
     can eyeball-check that the labels actually wrap the object.
     Pass `--no-overlay` to skip these once you trust the math.

NO ROS. NO `ros_gz_bridge`. NO `cv_bridge`. NO complicated QoS dance.
NO manual labelling either: the labels come straight from the
simulator's ground-truth geometry.

## Why this rewrite

The previous version of this folder relied on the SDF `<save>`
element to make Gazebo itself write PNGs to disk. That element parses
cleanly but **does not actually fire** on every gz-sim build (in
particular, not on the WSL build the user is on). Adding our own
gz-transport subscriber both guarantees we get frames and gives a
clear error when something is wrong, instead of silently writing
nothing.

## Prerequisites — one-time install

| Distro                       | Install line                                                                            |
|------------------------------|-----------------------------------------------------------------------------------------|
| Ubuntu 24.04 + Jazzy + Harmonic | `sudo apt install python3-gz-transport13 python3-gz-msgs10 python3-numpy python3-pil` |
| Ubuntu 22.04 + Humble + Garden  | `sudo apt install python3-gz-transport12 python3-gz-msgs9 python3-numpy python3-pil`  |

To check which gz you are on:

```bash
gz sim --version          # Harmonic = v8.x, Garden = v7.x
apt-cache search 'gz-msgs[0-9]'
apt-cache search 'gz-transport[0-9]'
```

The script tries transport13 first, then falls back to transport12,
so the same code works on both. If neither package is installed it
exits with the exact apt command to copy-paste.

## Run it — two terminals

Both terminals must be in the repo root.

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

The `-r` flag auto-plays sim time. Confirm the camera topic is live:

```bash
gz topic -l | grep image_raw
# expect: /overhead_camera/image_raw
gz topic -i -t /overhead_camera/image_raw
# expect: ... Type: gz.msgs.Image ...
```

### Terminal 2 — teleport the camera + save PNGs

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/move_camera.py
```

Defaults: 5 views, 2 s dwell each, 1 PNG per view, one cycle then
exit. So one run produces 5 PNGs.

Sample output:

```
gz-transport Python: Harmonic (transport13 + msgs10)
subscribing to       /overhead_camera/image_raw
saving PNGs to       /home/.../place-items-on-shelf/captured_frames/
YOLO classes file    /home/.../captured_frames/classes.txt  (1 class(es))
image intrinsics     640x480  hfov=60deg  fx=554.3
bbox overlays to     /home/.../captured_frames/overlays/  (disable with --no-overlay)

waiting for the first frame ...
first frame received after 0.3 s (got 1 frames so far).
[top]       pos=(+0.05,+0.00,+1.50)  -> aim at (0.05, 0.0, 0.94)  pitch=+90deg  yaw=+0deg   set_pose=OK
[top]       -> /home/.../captured_frames/cycle00_top_0.png  (640x480)  labels=1 -> cycle00_top_0.txt  overlay=1 -> overlays/cycle00_top_0_bbox.png
[front_+x]  pos=(+0.60,+0.00,+1.40)  -> aim at (0.05, 0.0, 0.94)  pitch=+40deg  yaw=+180deg set_pose=OK
[front_+x]  -> /home/.../captured_frames/cycle00_front_+x_0.png  (640x480)  labels=1 -> cycle00_front_+x_0.txt  overlay=1 -> overlays/cycle00_front_+x_0_bbox.png
...

done. saved 5 PNGs -> /home/.../captured_frames/
```

Useful flags:

```bash
# Spend longer at each pose and save 3 PNGs per view -> 15 PNGs per cycle.
python3 .../move_camera.py --dwell 4 --shots 3

# Cycle forever; Ctrl+C to stop.
python3 .../move_camera.py --loop

# Save somewhere else.
python3 .../move_camera.py --out /tmp/my_dataset

# Production-mode capture: no overlays in the output dir.
# (The trainer ignores .txt files in subdirs, but skipping overlays
#  saves disk + skips the PIL draw step.)
python3 .../move_camera.py --no-overlay
```

## Where the images and labels land

By default: `./captured_frames/` relative to wherever you launched
`move_camera.py`. Following the recipe above, that is:

```
~/ros2_ws/src/place-items-on-shelf/captured_frames/
├── classes.txt                    # one class name per line, ordered by class id
├── cycle00_top_0.png              # the image
├── cycle00_top_0.txt              # the YOLO label for that image
├── cycle00_front_+x_0.png
├── cycle00_front_+x_0.txt
├── cycle00_back_-x_0.png
├── cycle00_back_-x_0.txt
├── cycle00_left_+y_0.png
├── cycle00_left_+y_0.txt
├── cycle00_right_-y_0.png
├── cycle00_right_-y_0.txt
└── overlays/                      # bbox-annotated copies for visual QA only
    ├── cycle00_top_0_bbox.png     #   - green rectangle = ground-truth bbox
    ├── cycle00_front_+x_0_bbox.png#   - text label = "<class_name> (<class_id>)"
    ├── cycle00_back_-x_0_bbox.png #   - in a subfolder so the YOLO trainer
    ├── cycle00_left_+y_0_bbox.png #     doesn't pick them up as extra images
    └── cycle00_right_-y_0_bbox.png
```

The `overlays/` subfolder is meant for **you**, not for training. Open
any `_bbox.png` and you should see the green rectangle hugging the
target object. If the rectangle is in the wrong place, the labels
in the sibling `.txt` are wrong — fix the projection math, not the
overlay. Pass `--no-overlay` to skip generating these once you trust
the math.

The script prints the absolute path on every save, so there is no
guessing — just copy the path it printed.

### YOLO label format (what's inside the `.txt`)

Each `.txt` is the standard Ultralytics YOLO format — one detection per line:

```
<class_id> <x_center_norm> <y_center_norm> <width_norm> <height_norm>
```

All four numbers are normalised to `[0, 1]` (so the dataset is
resolution-independent). For our single-class setup `<class_id>` is
always `0` and the class name is in `classes.txt`. Example contents:

```
0 0.100270 0.367055 0.200544 0.236877
```

An empty `.txt` is valid YOLO too — it means "no objects of any
labelled class are visible in this frame." The script writes an
empty file (rather than skipping it) so the image/label pairing
stays 1:1 even if the bottle moves off-screen later.

### How the labels are computed

There is **no neural network and no labelling tool**. The bbox is
pure geometry:

1. The solvent bottle's tight axis-aligned bbox in world coords is
   hard-coded in `LABELED_OBJECTS` (derived once from its SDF
   geometry: body Ø85×150 mm + cap Ø50×25 mm at world pose
   (0.10, 0.25, 0.975)).
2. For each viewpoint we transform the bbox's 8 corners into the
   camera's body frame using the same RPY we just teleported to.
3. We re-map body → optical (Gazebo's body +X is forward; the
   pinhole equation expects +Z = forward) and project with the
   pinhole formula `u = fx·X/Z + cx`, `v = fy·Y/Z + cy`. The
   intrinsics are derived from the SDF's `<horizontal_fov>1.0472</horizontal_fov>`
   and `640×480` image size.
4. Take the axis-aligned bbox of the 8 projected pixels, clamp to
   the image, normalise. Done.

This works only because the bottle is rigid and we know its 3D
geometry exactly. When Step 2 starts moving objects randomly, the
bbox center will change every frame — we'll read each object's
current pose from the world's pose-info topic instead of hard-coding
it in `LABELED_OBJECTS`.

## Troubleshooting

- **`ERROR: gz-transport Python bindings not found.`**
  Run the apt-install line for your distro (table above). If apt
  cannot find the package, you are on the other gz track — Garden
  has `gz-transport12`, Harmonic has `gz-transport13`.

- **`WARNING: no frame in 5 s`** despite gz sim being open.
  - Is the sim paused? Click ▶ in the GUI, or use `-r` on the CLI.
  - Is the topic actually published? Confirm with:
    ```bash
    gz topic -l | grep image_raw
    gz topic -e -t /overhead_camera/image_raw -n 1
    ```
    The second command prints one message — if it does, the topic
    is live and the Python subscriber should match it.
  - Are you on a gz version that does not match `transport12` or
    `transport13`? Check `gz sim --version`.

- **`set_pose=FAIL (is gz sim running?)`** on every line.
  The world's `UserCommands` plugin is not loaded. The SDF in this
  repo declares it explicitly (line ~498 of
  `ketchup_extraction.sdf`), so check you are running the right
  SDF file.

- **PNGs all look identical even though the script reports moves.**
  Either the camera is teleporting but not re-rendering (try
  `--dwell 4` so the sensor has more time to publish a fresh frame),
  or the camera is not actually being moved (re-run and check that
  every line ends in `set_pose=OK`).

- **Oblique frames are blank / show nothing but the floor.**
  The camera is moving but facing the wrong way. The script now
  computes pitch+yaw with `look_at()` aimed at `LOOK_AT_TARGET`,
  so if you have moved the bench objects somewhere new, edit
  `LOOK_AT_TARGET` at the top of `move_camera.py` to point at the
  new cluster.

- **Colours look wrong (BGR/RGB swap).**
  The SDF declares `<format>R8G8B8</format>` and the script saves
  with PIL `mode="RGB"`. If you swap to a BGR camera format, also
  swap the `mode="RGB"` argument in `msg_to_png()`.

## What's next — domain randomisation, the 6 axes

This folder currently implements **only one** of the six
randomisation axes used in production synthetic-data pipelines:
**camera-pose variation**. The full list — and where we stand on
each — is documented in
[`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md).
Short version:

| # | Axis              | Done here?                                   |
|---|-------------------|----------------------------------------------|
| 1 | Camera pose       | **Yes** — 5 viewpoints from `CAMERA_POSITIONS` (this script). |
| 2 | Object pose       | **Yes** — see [`README_object_pose.md`](README_object_pose.md) and `randomize_objects.py`. |
| 3 | Lighting          | **Yes** — see [`README_lighting.md`](README_lighting.md) and `randomize_lighting.py`. |
| 4 | Materials / textures | No — would require swapping `<material>` blocks per frame. |
| 5 | Distractor objects | **Yes** — see [`README_distractors.md`](README_distractors.md) and `randomize_distractors.py`. |
| 6 | Background        | **Yes** — see [`README_background.md`](README_background.md) and `randomize_background.py`. |

A real production-quality YOLO training set varies all six. We are
deliberately doing only #1 right now and shipping the labels for it
so the geometry / projection / file-format plumbing is in place
before we layer on the rest. When we move to NVIDIA Isaac Sim
Replicator, these same six axes become one-line Replicator
randomisers each.

The labels emitted by **this** script already match the format the
later steps will produce — so the same training command will work
whether you have 5 PNGs (now) or 5000 (after Step 2).

## File list

```
synthetic_data/
├── README.md                  (this file — Step 1, camera-pose variation)
├── README_object_pose.md      (Step 2 — object-pose randomisation walkthrough)
├── README_lighting.md         (Step 3 — lighting randomisation walkthrough)
├── README_distractors.md      (Step 5 — distractor-objects walkthrough)
├── README_background.md       (Step 6 — background-swap walkthrough)
├── move_camera.py             (subscribe + teleport camera + save PNGs)
├── randomize_objects.py       (subscribe + teleport every labelled object + save PNGs)
├── randomize_lighting.py      (subscribe + reconfigure the sun light + save PNGs)
├── randomize_distractors.py   (spawn random clutter on the bench + save PNGs)
└── randomize_background.py    (swap a coloured plane over the bench + save PNGs)
```

## Related docs

- [`../README.md`](../README.md) — what this Gazebo world represents.
- [`../../../docs/synthetic-data/`](../../../docs/synthetic-data/) —
  the customer-facing synthetic-data offering this implements.
- [`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md)
  — Feature 1, the bigger version of what this exercise warms up.
  Adds masks + labels on top of the raw frames produced here.
