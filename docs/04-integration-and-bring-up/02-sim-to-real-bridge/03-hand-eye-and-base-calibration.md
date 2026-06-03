# 02-c — Hand-eye and Base Calibration

In sim, the camera and the arm always agreed perfectly on where
things were — because you placed both. On real, they don't. The
camera is bolted somewhere by a human, the arm is mounted at *almost*
the right pose, and the transform between them is wrong by a few mm
to a few cm.

You measure and fix this once. It's the single most important
real-world step in this layer.

## What you need before this step

- Real arm running through `ros2_control` from
  [step 2](02-ros2-control-driver-swap.md).
- Real camera connected, calibrated for intrinsics (lens parameters),
  and publishing `/image` + `/camera_info`.
- A printed **ArUco** or **ChArUco** calibration board. A4-size with
  a 5×7 grid of 30 mm markers is a fine default.

## Three calibrations, in order

1. **Camera intrinsics.** Lens parameters: focal length, principal
   point, distortion. Usually done with `camera_calibration` (ROS 2)
   on ~20 board images.
2. **Hand-eye calibration.** The transform from the **camera** to a
   **robot frame** — depends on whether the camera is wrist-mounted
   or scene-mounted.
3. **Base calibration.** The transform from `world` to `base_link` —
   where exactly the arm sits in your workspace.

Intrinsics first, hand-eye second, base last. Each later step depends
on the earlier ones being correct.

## Camera intrinsics

```
ros2 run camera_calibration cameracalibrator \
  --size 5x7 --square 0.030 \
  --ros-args -r image:=/camera/image_raw -r camera:=/camera
```

Wave the board in front of the camera covering the FOV — corners,
centre, tilted, near, far. After ~20 captures click **Calibrate**.
Click **Save** to write `ost.yaml` and **Commit** to publish it to the
camera info topic.

**Acceptance bar:** reprojection error under **0.3 pixels** RMS for a
1280×720 camera. Higher than that, redo it.

## Hand-eye calibration

The transform you're solving for is one of:

- **Eye-in-hand** — camera bolted to the arm's wrist. You're solving
  `tool0 → camera_link`.
- **Eye-to-hand** — camera bolted to a tripod / overhead. You're
  solving `base_link → camera_link`.

The procedure is the same: move the arm to many poses, detect the
calibration board at each pose, solve.

### Tools

- **`MoveIt Calibration`** — a MoveIt 2 plugin with an RViz GUI for
  hand-eye. Recommended first choice.
- **`easy_handeye2`** — ROS 2 port of the popular `easy_handeye`
  package. Wraps OpenCV's `calibrateHandEye`.
- **OpenCV's `cv2.calibrateHandEye`** — call it directly if you want
  full control.

### The recipe (eye-in-hand)

1. Fix the calibration board to the table.
2. Move the arm to 15–25 poses where the camera sees the board at
   different orientations and distances.
3. At each pose, record:
   - The arm's `tool0 ← base_link` transform (from TF).
   - The board's `target ← camera_link` transform (from the detector).
4. Run the solver. It returns `tool0 → camera_link`.
5. Save the result as a static transform in your project's
   `calibration.yaml`.

### The recipe (eye-to-hand)

Same idea, but:

- The board is **mounted on the gripper**.
- The arm moves and you record `base_link ← tool0` (from TF) and
  `target ← camera_link` (from the detector).
- The solver returns `base_link → camera_link`.

### Acceptance bars

- **Reprojection RMS error:** under **2 mm** for a tabletop arm,
  under **5 mm** for a larger workspace.
- **Spread the poses widely.** If they're all in one part of the
  workspace, the solver overfits. Aim for a range of orientations
  spanning > 60° per axis.

## Base calibration (`world → base_link`)

Often the arm's `base_link` is *almost* at the origin you wrote in
your URDF — but a couple of millimetres off, and a degree or two
rotated.

A simple recipe:

1. Stick an ArUco tag at a **known** place in the world (e.g. a corner
   of the table with measured offsets).
2. Use the camera (now hand-eye calibrated) to detect that tag in
   `world` coordinates.
3. Compare to the known location → solve the `world → base_link`
   offset.

Save the result as a static transform alongside the hand-eye one.

## Where the calibration lives

Not in the URDF. In a runtime YAML:

```yaml
calibration:
  world_to_base_link: { x: 0.001, y: -0.002, z: 0.000, roll: 0.0, pitch: 0.0, yaw: 0.005 }
  tool0_to_camera:    { x: 0.030, y: 0.000, z: 0.050, roll: 0.0, pitch: 0.0, yaw: 0.0 }
```

Load it in `real.launch.py` as `static_transform_publisher` nodes.
**Never** edit the URDF to encode calibration.

## Verifying the calibration

Three quick tests:

1. **Re-detect the board** from a new pose. Reproject corners; should
   land within 1–3 mm of the visual corners.
2. **Touch test.** Place a small object at a known location; ask the
   robot to move `tool0` to that location. The gripper tip should hit
   the object dead-on.
3. **Pick a fixed object.** Run the [step 4 of 01-simulation-first-development](../01-simulation-first-development/04-scripted-first-task.md)
   task with the *real* perception pose. The grasp should land.

If (2) or (3) is off by more than 5 mm, redo the calibration. Don't
plaster over the error in code.

## When to recalibrate

- After any **physical change** — moving the camera, remounting the
  arm, a tap on the camera.
- After a **driver upgrade** that changes how the arm reports
  positions.
- **Quarterly** as a hygiene check.

Write the calibration date into the YAML so you can spot stale
calibrations.

## Output of this step

```
Camera intrinsics calibrated:    yes — reprojection RMS: ___ px
Camera intrinsics file:          ___
Hand-eye type:                   eye-in-hand / eye-to-hand
Hand-eye RMS error:              ___ mm
Hand-eye transform:              tool0 → camera_link = (x, y, z, roll, pitch, yaw)
Base calibration RMS error:      ___ mm
Base transform:                  world → base_link = (___, ___, ___)
Calibration YAML path:           ___
Date calibrated:                 ___
Touch test passes (≤ 2 mm):      yes / no
```

## Common mistakes

1. **Skipping intrinsics, assuming the factory default.** Lens
   distortion varies between cameras of the same model.
2. **Hand-eye with only 5 poses.** The solver works but the error
   bar is huge. Use 15–25.
3. **All poses at one orientation.** Solver overfits to one axis.
   Spread orientations.
4. **Calibration data in the URDF.** Now you can't update without a
   rebuild. Put it in YAML.
5. **Re-running calibration "to refresh" without changing anything.**
   You'll get slightly different numbers and drift. Only recalibrate
   on physical changes or quarterly.
6. **No date / version on the calibration file.** A 6-month-old
   calibration that nobody updated silently rots.

## What's next

Calibration is in. Now you let your task code drive the real arm,
but **carefully** — read-only first, then slow speeds.

→ Next: [04-shadow-mode-and-slow-speeds.md](04-shadow-mode-and-slow-speeds.md)
