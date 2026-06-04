# Architecture — exercise 12

One file, one job: collect 20 (`T_base_ee`, `T_cam_marker`) pairs
and solve `T_base_cam`.

```
12-hand-eye-calibration/
├── README.md                 # concept + eye-to-hand vs eye-in-hand
├── ARCHITECTURE.md           # this file
├── IMPLEMENTATION_NOTES.md   # solver choice, pose-variety trap, trade-offs
└── hand_eye_calibrate.py     # only new code
```

## What `hand_eye_calibrate.py` owns

A single ROS 2 node `HandEyeCalibrator` plus three pure functions
that handle the math:

| Function / class           | Responsibility                                                          |
|----------------------------|-------------------------------------------------------------------------|
| `quat_to_rmat`             | Quaternion → 3×3 rotation matrix. No SciPy dependency.                  |
| `pose_to_rt`               | `geometry_msgs Pose / Transform` → `(R, t)` numpy arrays.               |
| `invert_rt`                | Rigid-transform inverse — used for the eye-to-hand trick.               |
| `solve_eye_to_hand`        | Inverts EE poses, calls `cv2.calibrateHandEye`, returns `T_base_cam`.   |
| `rt_to_xyzrpy`             | For printing the result in human-friendly form.                         |
| `HandEyeCalibrator`        | The node — owns subscriptions, TF buffer, sample list, solve trigger.   |

The split keeps the solver testable without ROS. You can unit-test
`solve_eye_to_hand` with three handcrafted pose pairs and the
expected output, no `rclpy.init()` needed.

## Inputs / outputs at the ROS layer

```
SUBSCRIBES
   /aruco/marker_pose          geometry_msgs/PoseStamped
                               (marker in camera frame; item 10 is the source)

TF LISTENS
   base_link → tool0           queried per marker frame timestamp
                               (provided by exercise 18's MoveIt launch)

PUBLISHES
   (none — the output is printed plus a ready-to-paste
    static_transform_publisher command line)
```

The choice not to publish a TF directly is deliberate: calibration
should run once, write the result somewhere durable, then exit. A
live TF that disappears when the script stops would be worse than a
copy-paste-able command that goes into a launch file.

## Control flow

```
__init__
   declare parameters
   create TF listener, marker subscriber
   warm log line

_on_marker (per ArUco message, until N samples collected)
   look up base_link → tool0 at marker timestamp
   reject if duplicate-position (within min_pose_spread_m)
   append (R_be, t_be, R_cm, t_cm)
   if N reached → _solve_and_publish

_solve_and_publish
   call solve_eye_to_hand
   print T_base_cam
   print static_transform_publisher command
   print residuals
   rclpy.shutdown
```

State held by the node:

- `self._R_base_ee`, `self._t_base_ee` — arm leg of every sample.
- `self._R_cam_marker`, `self._t_cam_marker` — camera leg.
- TF buffer for `lookup_transform`.

Everything else is constants / parameters.

## What depends on what

- **Upstream (must exist or this exercise has no inputs):**
  - Item 10's ArUco detector publishing `/aruco/marker_pose`.
  - The MoveIt launch from exercise 18 (or any source of the
    `base_link → tool0` TF chain).
  - A small driver loop walking the arm through 20 varied poses
    (out of scope here — one `for` loop around exercise 19).
- **Downstream (consumes our output):**
  - Any node that calls `tf2.transform(pose_in_cam, "base_link")`.
    Once the static transform is published, that single line is the
    entire interface to this exercise. The next step in the
    pipeline is exercise 21's pick controller.

No other exercise's code imports from this folder; the output is a
TF, not a Python module.
