# v1_simple_pick — mobile-manipulator pick-and-place

This is the first runnable end-to-end demo of place-items-on-shelf. A
differential-drive mobile base with an attached 3-DOF arm and parallel-jaw
gripper drives to a shelf, picks up a standard 355 ml soda can, carries it
back, and places it on an onboard tray.

The robot structure is the canonical "mobile manipulator" pairing seen in
ROS courses (a small diff-drive base + a Robotis-OpenManipulator-X-style 4-link
arm with a parallel-jaw gripper), built from scratch in URDF so it has
zero external package dependencies. The target object is a standard
355 ml soda can (66 mm diameter × 123 mm tall, 355 g) — real-world
dimensions so the gripper geometry, arm reach, and shelf height are all
constrained by something physical.

## Architecture

```
                 ┌────────────┐  /cmd_vel               ┌─────────────────┐
                 │ task node  │ /arm/{shoulder,elbow,   │  Gazebo Harmonic │
   logs to T2 ←──│ (Python)   │  wrist}_cmd            ─┤  store.sdf world │
                 │            │ /gripper/{left,right}_  │   + pos_robot    │
                 │            │  cmd                    │   (URDF spawned) │
                 │            │ /grasp/{attach,detach}  │                  │
                 └────────────┘  /odom (in)             └─────────────────┘
                       ▲                                       │
                       └────── ros_gz_bridge (config YAML) ───┘
```

The task node sequences nine stages: drive forward → arm pre-grasp → arm
grasp → close gripper → attach detachable joint → lift → carry-fold →
drive back → arm place → detach + open gripper. Each arm command is
absorbed by a `gz-sim-joint-position-controller-system` plugin in the
URDF, one per joint. The grasp itself uses `gz-sim-detachable-joint-system`:
the plugin is declared in the robot URDF with the soda can as its child
model, starts ATTACHED at world load, and the task script publishes
`/grasp/detach` during startup to release it. At grasp time, the script
publishes `/grasp/attach` and the joint re-forms at the current
gripper-to-can offset, so the can rigidly follows the gripper. The release
publishes detach again and gravity drops the can onto the tray.

## What v1 does NOT do (deferred to later versions)

- **Closed-loop control.** Arm motions are open-loop sequences of
  hand-tuned joint angles, no trajectory planning, no IK, no MoveIt.
  Drive distance is sim-time-based, not odometry-feedback-based.
- **Perception.** The can position is hard-coded; no camera, no detection.
- **Navigation.** No Nav2 — just straight `cmd_vel` for a fixed sim time.
- **Friction-based grasp.** The grasp is rigidly held by a Gazebo
  DetachableJoint, not by friction between the gripper fingers and the
  can. The fingers visibly close around the can, but the joint is what
  actually keeps it in the gripper.

## Packages

| Package | Role |
|---|---|
| `pos_v1_description` | Robot URDF (base + 3-DOF arm + 2-finger gripper, all gz-sim plugins) |
| `pos_v1_bringup` | Gazebo world (`store.sdf`), launch file, ROS↔Gazebo bridge config |
| `pos_v1_task` | Python node that sequences the pick-and-place behaviour |

## Build (on WSL2 Ubuntu 24.04 with ROS 2 Jazzy)

Assuming your workspace is `~/ros2_ws` and this repo is cloned at
`~/ros2_ws/src/place-items-on-shelf/`:

```bash
# (one-time) symlink so colcon discovers the v1 packages under a short path
ln -s ~/ros2_ws/src/place-items-on-shelf/v1_simple_pick ~/ros2_ws/src/pos_v1

# build only the v1 packages
cd ~/ros2_ws
rosdep install --from-paths src/pos_v1 --ignore-src -r -y
colcon build --packages-select pos_v1_description pos_v1_bringup pos_v1_task
source install/setup.bash
```

`colcon build` also works without the symlink — it scans recursively — but
the symlink keeps the `--packages-select` line short.

## Run

In **terminal 1**:
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch pos_v1_bringup sim.launch.py
```

You should see Gazebo with: a blue boxy robot (orange arm folded over its
back, two-finger gripper at the end), a brown shelf in front of it, and a
single red soda can on the shelf. The arm starts in a stowed pose.

In **terminal 2** (after Gazebo is fully loaded):
```bash
source ~/ros2_ws/install/setup.bash
ros2 run pos_v1_task pick_and_place
```

Sequence (sim-seconds):

| Stage | What you should see |
|---|---|
| INIT (3 s) | Arm stows, gripper opens, grasp joint detaches (can stays on shelf) |
| 1 (7.5 s)  | Robot drives forward to the shelf |
| 2 (2.5 s)  | Arm extends out forward, gripper above can |
| 3 (2.5 s)  | Arm lowers so gripper surrounds the can |
| 4 (1.0 s)  | Gripper fingers close around the can |
| 5 (0.5 s)  | Grasp joint re-attaches (can is now "held") |
| 6 (2.5 s)  | Arm lifts can clear of the shelf |
| 7 (2.5 s)  | Arm folds up over the tray (can goes with it) |
| 8 (7.5 s)  | Robot drives back to the start, still carrying the can |
| 9 (2.5 s)  | Arm lowers toward the tray |
| 10 (1.5 s) | Grasp joint detaches, gripper opens, can drops onto tray |
| 11 (2.5 s) | Arm stows |

Total sim-time ≈ 39 s. Wall-clock will be ~80–90 s on WSL2 + Iris Xe (RTF
~45%) — that's expected and not a bug.

## Tunable knobs

Top of `pos_v1_task/pos_v1_task/pick_and_place.py`:

| Constant | Default | Meaning |
|---|---|---|
| `DRIVE_SPEED` | `0.2` m/s | Linear speed forward and back |
| `DRIVE_TIME_S` | `7.5` | Sim-s to drive (1.5 m at 0.2 m/s) |
| `STARTUP_DELAY_S` | `3.0` | Sim-s for sim + controllers + initial detach to settle |
| `ARM_MOVE_TIME_S` | `2.5` | Sim-s allowed for a single arm joint move |
| `GRIPPER_MOVE_TIME_S` | `1.0` | Sim-s for fingers to open/close |
| `POSE_*` | varies | (shoulder, elbow, wrist) target angles in radians |
| `GRIPPER_*` | varies | Finger offsets in metres (0=closed, 0.045=fully open) |

PID gains for each joint controller are in `pos_v1_description/urdf/pos_robot.urdf`
inside the `<gazebo>` block — one `gz::sim::systems::JointPositionController`
plugin per joint.

## What we expect to break first time

This is the first attempt at the proper-arm version and it has not been
tested on the user's machine. Likely issues:

1. **Arm pose tuning.** `POSE_PRE_GRASP` / `POSE_GRASP` assume the robot
   stops with its base centre at world x ≈ 1.5 and the can at world
   (1.88, 0, 0.5865). If `git pull` plus a fresh `colcon build` shows the
   gripper missing the can (too high, too low, too far, too close), nudge
   `POSE_GRASP`'s shoulder ±0.05 rad (height) or `DRIVE_TIME_S` ±0.5
   (distance).
2. **PID gains.** Joint controller P/I/D defaults are conservative. If a
   joint visibly oscillates or undershoots its target by a lot, edit the
   `<p_gain>` / `<d_gain>` for that joint in the URDF and rebuild
   `pos_v1_description`.
3. **DetachableJoint at world load.** The plugin defaults to ATTACHED, so
   there's a brief window between Gazebo loading the world and the task
   script publishing the first `/grasp/detach` where the can is rigidly
   linked to the gripper 1.5 m away. If `STARTUP_DELAY_S` is too short
   (or the task is started before Gazebo finishes loading), the can may
   start in a weird place. The 3-s default and "start the task only after
   Gazebo is fully up" should handle this; if you see the can floating in
   mid-air or stuck to the gripper, restart and wait longer before
   running the task.
4. **Topic naming mismatch.** Gazebo Harmonic's `DiffDrive` plugin defaults
   to `/model/<model_name>/cmd_vel`. The bridge assumes the model name is
   exactly `pos_robot` (matches the launch file's `-name` arg). The
   joint-state topic name uses both world name (`store`) and model name —
   if you rename either, update `config/gz_bridge.yaml`.
5. **`gz` vs `ign` commands.** All commands assume Gazebo Harmonic (`gz`
   CLI). If you have Gazebo Fortress instead, swap to `ign`.

Report any of these and we'll fix in a follow-up commit.

## Where we go next (proposed)

- **v2_ros2_control** — replace the per-joint gz-sim
  `JointPositionController` plugins with a proper `ros2_control` hardware
  interface + `joint_trajectory_controller`. Lets us send trajectories
  instead of single position setpoints.
- **v3_friction_grasp** — drop the DetachableJoint, rely on contact-based
  friction between gripper fingers and the can. Closer to real-world
  physics.
- **v4_nav2** — replace open-loop `cmd_vel` with Nav2 navigation to shelf
  waypoints.
- **v5_perception** — replace hard-coded can position with OpenCV HSV
  detection on an RGB-D camera.
- **v6_moveit** — replace `POSE_*` constants with MoveIt 2 motion planning
  from current pose to a target Cartesian pose.

Each is a separate sibling folder so this v1 stays as a "hello world"
baseline.
