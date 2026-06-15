# Synthetic data — Step 1: camera frames of the bench

The simplest possible synthetic dataset for the dissolution / extraction
world. Just two things:

1. **Place a camera.** Done already — `ketchup_extraction.sdf` has an
   `overhead_camera` model that points straight down at the bench top.
2. **Save the camera frames.** The camera sensor has
   `<save enabled="true"><path>captured_frames</path></save>`, so
   **Gazebo itself** writes every rendered frame to disk as a PNG.
   No ROS, no `ros_gz_bridge`, no `cv_bridge`, no Python subscriber.

That's the whole capture loop. The optional `move_camera.py` script
teleports the camera through five preset viewpoints (top + four
obliques) so the dataset has more than one angle.

## What changed vs. the previous attempt

The earlier version of this folder tried to do too much at once:
ROS 2 subscription + pose-info subscription + manual pinhole bbox
projection + `gz service` jitter for both objects and camera + YOLO
labels. It got stuck on QoS mismatches in the ROS bridge and was
hard to recover from. The new version is the **first step only** —
just images, no labels — using Gazebo's own `<save>` element instead
of any ROS plumbing. Labels (Step 2) and lighting variation (Step 3)
are planned follow-ups, listed at the bottom of this README.

## Requirements

- **WSL2 Ubuntu 22.04 or 24.04** (or native Linux).
- **Gazebo (`gz sim`)** — Garden, Harmonic, or newer. No ROS needed
  for the capture itself.
- **Python 3** (for the optional `move_camera.py`). Standard library
  only — no `pip install` step.

## Run it — one or two terminals

Both terminals must be in the repo root (so the relative
`captured_frames/` path works as expected).

### Terminal 1 — start Gazebo

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

The `-r` flag auto-plays sim time, so the camera starts rendering
straight away. Frames appear in `./captured_frames/` immediately —
one new PNG every ~0.5 s (the sensor's `<update_rate>` is 2 Hz).

To stop, close the Gazebo window or press `Ctrl+C` in the terminal.

### Terminal 2 (optional) — cycle the camera through views

```bash
cd ~/ros2_ws/src/place-items-on-shelf
python3 gazebo_worlds/02-dissolution-and-extraction/synthetic_data/move_camera.py
```

Defaults: 2 s dwell per view, 5 views, one cycle then exit. With
2 Hz capture that's ~4 PNGs per view, ~20 PNGs per cycle from five
different angles.

Useful flags:

```bash
# Stay longer at each pose -> more frames per angle.
python3 .../move_camera.py --dwell 5

# Loop forever (Ctrl+C to stop). Use this if you want a bigger dataset.
python3 .../move_camera.py --loop
```

### Headless WSL fallback (no GUI)

If `gz sim` cannot open a GUI window on your WSL setup, run it
headless:

```bash
gz sim -s -r gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

`-s` is "server only, no GUI", and `-r` still auto-plays. The
camera sensor still renders and `<save>` still writes PNGs.

## Output

```
./captured_frames/
├── 1.png
├── 2.png
├── 3.png
└── ...
```

Filenames are auto-assigned by Gazebo — sequential integers starting
at 1. Each PNG is 640 × 480 BGR.

Gazebo does NOT label the files with the camera pose, so if you want
"this PNG was taken at view X" you need to look at the timestamps and
match them against the print-out from `move_camera.py`. For Step 1
that mapping is good enough; the proper "label-per-frame" pipeline is
deferred to Step 2.

## What's next (the three-step plan)

This folder implements **Step 1 only**: place a camera, save its
frames, and optionally move the camera between captures.

- **Step 1 — move the camera.** (this README) Different angles of
  the same static scene. → ~20 PNGs per `--loop` cycle.
- **Step 2 — move the objects.** Random jitter on the beakers and the
  solvent bottle between captures, plus a per-frame YOLO / COCO label
  derived from the world's pose-info topic. → labelled detection
  dataset.
- **Step 3 — change lighting.** Vary `<light>` direction and intensity
  for domain randomisation. → a model trained on this data survives
  the real lighting in a real lab.

Step 2 reuses the `set_pose` pattern from `move_camera.py` — same
`gz service` call, applied to the beakers and the bottle instead of
(or in addition to) the camera. Step 3 edits the `<light>` block in
the SDF before each cycle.

## Troubleshooting

- **`captured_frames/` does not appear.** Either Gazebo is paused
  (click ▶ in the GUI, or use `-r` on the CLI) or you launched
  `gz sim` from a folder where the user has no write permission.
  Try `cd` to the repo root before running.
- **`gz service` says "service call timed out".** The world's
  `UserCommands` plugin is not loaded. The SDF in this repo
  declares it explicitly (line ~498 of `ketchup_extraction.sdf`),
  so check you are running the right SDF.
- **PNGs all look identical.** Either the camera is not moving
  (`move_camera.py` not running), or its `set_pose` calls all fail
  silently. Re-run `move_camera.py` in the foreground and look for
  `set_pose=FAIL` lines.
- **`gz` command not found.** You did not source the Gazebo
  environment. Modern gz sim does not need a source script if it
  was installed via apt (`gz` lands in `/usr/bin/`); if you built
  it from source, source the workspace's `install/setup.bash`.

## File list

```
synthetic_data/
├── README.md         (this file)
└── move_camera.py    (optional: teleport the camera through preset views)
```

Capture itself is handled by the SDF — no Python required to take
the first picture.

## Related docs

- [`../README.md`](../README.md) — what this Gazebo world represents.
- [`../../../docs/synthetic-data/`](../../../docs/synthetic-data/) —
  the customer-facing synthetic-data offering this implements.
- [`../../../docs/synthetic-data/features/01-detection-images-and-masks.md`](../../../docs/synthetic-data/features/01-detection-images-and-masks.md)
  — Feature 1, which this exercise is the simplest possible warm-up
  for. The "labels at every pixel" half of that feature lands in
  Step 2.
