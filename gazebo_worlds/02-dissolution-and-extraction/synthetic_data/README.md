# Synthetic data — Step 1: camera frames of the bench

The simplest possible synthetic dataset for the dissolution / extraction
world. Two pieces:

1. **`ketchup_extraction.sdf`** — already has an `overhead_camera`
   model with a sensor that publishes RGB frames on the Gazebo
   Transport topic `/overhead_camera/image_raw`.
2. **`move_camera.py`** — a single Python script that:
   - **subscribes** to that topic via the gz-transport Python
     bindings,
   - **teleports** the camera through five preset viewpoints
     (top + four obliques) using `gz service set_pose`,
   - **saves** the latest frame to disk as a PNG after each pose.

NO ROS. NO `ros_gz_bridge`. NO `cv_bridge`. NO complicated QoS dance.

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

waiting for the first frame ...
first frame received after 0.3 s (got 1 frames so far).
[top]         pos=(+0.00, +0.00, +1.50)  rpy=(+0.00, +1.57, +0.00)  set_pose=OK
[top]         -> /home/.../captured_frames/cycle00_top_0.png  (640x480)
[oblique_+x]  pos=(+0.45, +0.00, +1.25)  rpy=(+0.00, +1.05, +0.00)  set_pose=OK
[oblique_+x]  -> /home/.../captured_frames/cycle00_oblique_+x_0.png  (640x480)
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
```

## Where the images land

By default: `./captured_frames/` relative to wherever you launched
`move_camera.py`. Following the recipe above, that is:

```
~/ros2_ws/src/place-items-on-shelf/captured_frames/
├── cycle00_top_0.png
├── cycle00_oblique_+x_0.png
├── cycle00_oblique_-x_0.png
├── cycle00_oblique_+y_0.png
└── cycle00_oblique_-y_0.png
```

The script prints the absolute path on every save, so there is no
guessing — just copy the path it printed.

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

- **Colours look wrong (BGR/RGB swap).**
  The SDF declares `<format>R8G8B8</format>` and the script saves
  with PIL `mode="RGB"`. If you swap to a BGR camera format, also
  swap the `mode="RGB"` argument in `msg_to_png()`.

## What's next (the three-step plan)

This folder implements **Step 1 only**: place a camera, subscribe
to its frames, move the camera between captures.

- **Step 1 — move the camera.** (this README) Different angles of
  the same static scene. → ~5 PNGs per default cycle, ~15 with
  `--shots 3`.
- **Step 2 — move the objects.** Random jitter on the beakers and the
  solvent bottle between captures, plus a per-frame YOLO / COCO label
  derived from the world's pose-info topic.
- **Step 3 — change lighting.** Vary `<light>` direction and intensity
  for domain randomisation.

Step 2 reuses the `set_pose` pattern from `move_camera.py` —
same `gz service` call, applied to the beakers and the bottle
instead of (or in addition to) the camera. Step 3 edits the
`<light>` block in the SDF, or calls `gz service` on the light
entity, between cycles.

## File list

```
synthetic_data/
├── README.md         (this file)
└── move_camera.py    (subscribe + teleport + save PNGs)
```

## Related docs

- [`../README.md`](../README.md) — what this Gazebo world represents.
- [`../../../docs/synthetic-data/`](../../../docs/synthetic-data/) —
  the customer-facing synthetic-data offering this implements.
- [`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md)
  — Feature 1, the bigger version of what this exercise warms up.
  Adds masks + labels on top of the raw frames produced here.
