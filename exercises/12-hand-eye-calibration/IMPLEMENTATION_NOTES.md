# Implementation notes — exercise 12

## Why `cv2.calibrateHandEye` and not write our own AX = XB solver

There are several well-known algorithms (Tsai-Lenz 1989,
Park-Martin 1994, Horaud-Dornaika 1995, Daniilidis 1999, dual-
quaternion variants). OpenCV ships all of the major ones behind a
single API. Two reasons we use it directly:

- Battle-tested numerics. The decomposition into rotation-then-
  translation, the dual-quaternion formulation in Daniilidis — all
  handled. Easy to get subtly wrong by hand.
- One-line method swap. If a noisier real-world setup makes
  Daniilidis unstable, switch to `cv2.CALIB_HAND_EYE_PARK` by
  changing one keyword arg.

The default we pick is `CALIB_HAND_EYE_DANIILIDIS`. Empirically it
is the most robust to translation noise of the five, which matches
our setup (ArUco pose has small translation jitter and small
rotation jitter).

## The eye-to-hand inversion trick

`cv2.calibrateHandEye` is documented for eye-IN-hand: camera bolted
to the gripper. Its inputs are (gripper→base) and (target→cam); its
output is the camera-in-gripper transform.

For eye-TO-hand (our overhead camera), we want the camera-in-base
transform. The OpenCV docs give the variant: **invert each
gripper→base pose** before feeding it in, run the same solver, and
the returned transform is now camera-in-**base** instead of
camera-in-gripper.

Proof in one line: the AX = XB equation is symmetric under swapping
"world" and "gripper" labels. Inverting the gripper-pose list
performs that swap.

We isolate this in `solve_eye_to_hand()` so the rest of the code
deals only with the layout that actually exists in this repo.

## The "pose variety" trap

The single biggest mistake in hand-eye calibration is moving the
arm through 20 poses that *translate* a lot but *rotate* very
little. Rotation is what disambiguates the solver — without it,
the linear system becomes rank-deficient and the result is hand-
wavy.

Rule of thumb for the arm dance:

- ≥ 3 distinct rotation axes covered.
- Each pose ≥ 15° rotation from its nearest neighbour.
- Translations spread by ≥ 5 cm.

We enforce the translation half automatically (drop samples within
`min_pose_spread_m`), but we do **not** enforce rotation diversity
in code. That's a discipline-of-the-arm-dance problem; the script
just consumes whatever poses arrive.

Symptom of a bad dance: small `residual mean` but a calibrated
transform that gives wildly different answers when you test with
poses outside the calibration set. The cure is to redo the dance
with more rotation.

## Why the residual is "relative", not "absolute"

`_report_residuals` compares:

- Marker position via the camera path: `R_bc @ t_cm + t_bc`
- Marker position via the arm path: `t_be` (EE position only,
  ignoring the fixed marker-on-EE mount offset)

The arm path is missing the constant offset between the EE link
origin and the marker centre. That offset is the **same number for
every sample**, so it does not affect the *variance* of the
residuals — only their mean. We print mean and std side by side;
**std is the trustworthy number**. A clean fit gives std under a
millimetre in Gazebo regardless of how the marker is mounted on
the EE.

If you want a true 5 mm "Done when" measurement, hold one pose out
of the 20, calibrate on the remaining 19, then re-project the
held-out marker observation into the base frame and compare against
the known EE position plus a *measured* marker-mount offset. We
don't ship that here — the constant-offset residual is enough to
tell whether the fit converged.

## TF timing

`lookup_transform(..., marker_msg.header.stamp)` rather than
`Time(0)` is deliberate. We want the **arm pose at the moment the
camera frame was captured**, not the latest TF. If the arm is
moving while the dance runs, the latest TF lags the image by some
controller cycles and the pairing drifts. Using the message
timestamp pulls the right interpolation.

If TF is not yet buffered for that stamp (the marker arrived before
the matching TF was published) we drop the sample with a warning
and wait for the next marker. This is robust but biases sampling
toward the slowest part of the dance — fine.

## Why we don't ship the arm-dance driver

The driver is one for-loop around exercise 19:

```python
for tx, ty, tz, rr, rp, ry in CALIBRATION_POSES:    # 20 hand-picked tuples
    move_arm.set_pose_target(...)
    move_arm.move()
    rclpy.spin_once(timeout_sec=0.5)
```

`CALIBRATION_POSES` lives in the caller's launch / task code — what
the right 20 poses are depends on the arm's reach envelope and
where the camera FOV is. Hard-coding 20 myCobot-280 poses here
would bake an assumption that breaks the moment you swap arms.
Better to leave it as a hook.

## Output handling

We print the static-transform command instead of writing a file.
Reasons:

- The user almost always wants to **bake the transform into a
  launch file**, not load it at runtime from a random YAML.
- Calibration is rare (once at install, once after a bump). A
  human-in-the-loop copy-paste is appropriate.
- Avoids an opinion about which launch file the result belongs to.

If you want a YAML, three lines of `yaml.safe_dump(...)` at the end
of `_solve_and_publish` does it.

## Failure modes you'll see first

| Symptom                                                   | Most likely cause                                                |
|-----------------------------------------------------------|------------------------------------------------------------------|
| `TF unavailable` for every sample                         | MoveIt launch not running, or frames named differently           |
| Solver returns NaN                                        | All 20 poses near-coplanar in rotation — redo dance              |
| Residual mean < 1 mm, std < 0.2 mm — but pick is 3 cm off | Marker mounted with backlash on the EE, or wrong marker ID       |
| Residual std > 5 mm                                       | Image is blurry (motion during capture), or marker too small     |
| Static TF works in RViz but centroid still off            | Centroid frame_id is wrong; check exercise 08 `header.frame_id`  |

## Where this exercise sits in the pipeline

This is the **last calibration step** the v1 pipeline needs. Once
the static transform is published, every centroid from exercise 08
flows through `tf2_buffer.transform(...)` into `base_link` with no
additional math. The pick controller then takes the base-frame
centroid + the 5-number grasp recipe from the autosampler use case
and hands it to MoveIt. That's the whole stack.
