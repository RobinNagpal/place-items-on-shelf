# v3_mycobot_pi

v3 of place-items-on-shelf, built around the **Elephant Robotics myCobot
280 Pi** — a 6-DOF educational arm with a built-in Raspberry Pi 4 running
Ubuntu / ROS 2. Hardware ordered, expected in ~2 weeks; this folder holds
the simulation work we can start on **before** the physical arm arrives.

## Why myCobot 280 Pi (vs the simulated v1 robot)

| | v1 (`v1_simple_pick/`) | v3 (this folder) |
|---|---|---|
| Robot | invented mobile manipulator | real product, Elephant myCobot 280 Pi |
| Reach | n/a | 280 mm working radius |
| DOF | 3 arm + gripper | 6 arm + parallel gripper |
| Payload | n/a | ~250 g |
| Software ships with it | n/a | `pymycobot` SDK, `mycobot_ros2` URDF + MoveIt + Gazebo |
| Will it run on real HW? | no | yes — same code, sim and hardware |

## Roadmap (each step is one PR)

1. **Step 1 — this PR.** Minimum viable URDF of the arm at the *real
   hardware dimensions*, viewable in RViz with joint sliders so we can
   sanity-check the size before hardware arrives.
2. **Step 2.** Vendor in Elephant Robotics' official
   [`mycobot_description`](https://github.com/elephantrobotics/mycobot_ros2)
   package to swap our primitive-geometry visuals for the real STL meshes.
3. **Step 3.** Bring the arm up in Gazebo Harmonic with `ros2_control` and
   a `joint_trajectory_controller` (so the same commands work in sim and
   on the real arm).
4. **Step 4.** Add MoveIt 2 for motion planning (`mycobot_280pi_moveit`
   configs already exist in `mycobot_ros2`).
5. **Step 5.** Add a small "scene" — a tabletop with a foam cube target
   object.
6. **Step 6.** Vision: USB camera + AprilTag detection (`apriltag_ros`)
   to find the cube.
7. **Step 7.** First scripted pick: detect cube → plan → grasp → drop.
8. **Step 8 (after hardware arrives).** Plug the real arm in, run the
   same launch file with `use_real_hardware:=true`.
9. **Step 9+.** Imitation learning with [LeRobot](https://github.com/huggingface/lerobot).

## What's in this PR (Step 1)

- `pos_v3_description/` — ROS 2 ament_cmake package holding the URDF.
- `pos_v3_bringup/` — launch file that displays the URDF in RViz with a
  joint-state sliders GUI. No physics, no Gazebo yet — that's Step 3.

### Source of dimensions

Link lengths come from Elephant Robotics' published spec sheet for the
myCobot 280 family. Joint limits use the documented ±165° / ±175° values
(in radians).

| Parameter | Value (m) | What it is |
|---|---|---|
| `d1` | 0.13156 | base mount → joint 2 (vertical) |
| `a2` | 0.1104  | joint 2 → joint 3 (upper arm length) |
| `a3` | 0.096   | joint 3 → joint 4 (forearm length) |
| `d4` | 0.06639 | joint 4 → joint 5 |
| `d5` | 0.07318 | joint 5 → joint 6 |
| `d6` | 0.0436  | joint 6 → tool flange |

Total working radius ≈ 280 mm, matching the manufacturer spec.

Visuals are simple primitives (cylinders + boxes) for now. The real STLs
ship with `mycobot_description` and will replace these in Step 2 — the
dimensions are accurate, only the *appearance* is approximate.

## How to run (Step 1)

Pre-requisites on the dev machine:

- Ubuntu 22.04
- ROS 2 Humble installed and sourced (`source /opt/ros/humble/setup.bash`)
- `joint_state_publisher_gui`, `xacro`, `rviz2` installed
  (`sudo apt install ros-humble-joint-state-publisher-gui ros-humble-xacro ros-humble-rviz2`)

Build and launch:

```bash
cd <repo root>
colcon build --packages-select pos_v3_description pos_v3_bringup
source install/setup.bash
ros2 launch pos_v3_bringup view_robot.launch.py
```

You should see:

1. An RViz window with the arm displayed at exact scale (280 mm reach).
2. A separate "joint_state_publisher" GUI window with 6 sliders, one per
   joint. Dragging a slider moves the corresponding joint in RViz.

Use the sliders to confirm the joint limits (±165° on most joints, ±175°
on joint 6) and the overall reach match the real arm's spec sheet.

## What's NOT here yet (intentionally)

- No Gazebo physics — RViz is just a viewer; gravity / collisions don't
  apply. That comes in Step 3.
- No real STL meshes — the official meshes will be vendored in Step 2.
- No gripper — the URDF stops at the tool flange (`tool0`). Gripper is
  added with the meshes in Step 2.
- No controllers, no MoveIt, no camera, no task code. Those are later
  steps.

## Quality checks

This is a docs + URDF + launch file change in a new ROS 2 package. There
is no repo-wide build/lint configured at the root; the package is built
with `colcon build` on a machine that has ROS 2 Humble installed.

Local verification done before commit:

- URDF is well-formed XML (read end-to-end).
- Launch file is syntactically valid Python.
- Link / joint names match between URDF and launch file.

Verification the user should do after pulling on a ROS 2 machine:

```bash
# Build
colcon build --packages-select pos_v3_description pos_v3_bringup
source install/setup.bash

# Lint the URDF (optional but useful)
check_urdf "$(xacro src/place-items-on-shelf/v3_mycobot_pi/pos_v3_description/urdf/mycobot_280pi.urdf)"

# Run it
ros2 launch pos_v3_bringup view_robot.launch.py
```
