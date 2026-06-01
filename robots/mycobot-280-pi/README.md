# myCobot 280 Pi — simulation-first bring-up

This folder builds up the **Elephant Robotics myCobot 280 Pi** in simulation, step by step, before any hardware is ordered. Each step adds one capability on top of the previous one and is intended to be runnable on its own.

The target end behaviour is a **stationary arm** that picks small items (HPLC autosampler vials) from a holder and places them into specific slots in a tray — i.e. "place items on shelf." Everything below is sized around that goal.

## Roadmap — where you are, where to start next

| # | Step | Status | Lives at | Verify command |
|---|---|---|---|---|
| 1 | URDF viewer in RViz (no physics, no controllers) | ✅ done | [`launch/view_in_rviz.launch.py`](launch/view_in_rviz.launch.py) | `ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/view_in_rviz.launch.py` |
| 2 | Gazebo Sim with `ros2_control` + `JointTrajectoryController` (gravity off, kinematic) | ✅ scaffolded — needs you to install Gazebo + run | [`launch/sim_in_gazebo.launch.py`](launch/sim_in_gazebo.launch.py) | `ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/sim_in_gazebo.launch.py` |
| 2.1 | Add link inertials, flip gravity back on | ⬜ not started | — | — |
| 3 | MoveIt 2 — motion planning + collision avoidance | ⬜ not started | — | — |
| 4 | Scene: HPLC autosampler tray + vial rack as Gazebo models | ⬜ not started | — | — |
| 5 | Vision: USB camera + AprilTag detection of tray slots | ⬜ not started | — | — |
| 6 | First scripted pick-and-place of a vial into one tray slot | ⬜ not started | — | — |
| 7 | Real hardware: same launch file with `use_real_hardware:=true` | ⬜ blocked on order | — | — |

When you come back to this repo, look at the top "⬜ not started" / "🟨 in progress" row — that's where to pick up.

## What's in this folder

```
.
├── launch/
│   ├── view_in_rviz.launch.py        # Step 1: robot_state_publisher + JSP-GUI + RViz
│   └── sim_in_gazebo.launch.py       # Step 2: gz sim + spawn + ros2_control + JTC
├── description/
│   └── mycobot_280_pi_sim.urdf.xacro # Step 2: wrapper around vendor URDF (adds ros2_control + gz plugin)
├── config/
│   └── controllers.yaml              # Step 2: joint_state_broadcaster + arm_controller (JTC)
├── worlds/
│   └── empty.sdf                     # Step 2: ground plane + sun, gravity disabled
├── rviz/
│   └── view.rviz                     # Step 1: RViz config (RobotModel on /robot_description, grid, TF)
├── docs/
│   ├── install.md                    # one-time setup (Ubuntu + ROS 2 + optional Gazebo)
│   ├── verify-env.md                 # checks before you build
│   ├── run.md                        # Step 1 build + launch
│   └── run_sim.md                    # Step 2 build + launch + test trajectory
└── src/
    └── mycobot_ros2/                 # git submodule: elephantrobotics/mycobot_ros2 (branch: humble)
```

The submodule is the upstream Elephant Robotics ROS 2 package set. We build only `mycobot_description` from it for both Step 1 and Step 2 — see the docs for exact commands.

## Do all myCobot 280 variants share the same shape?

**Yes — for our purposes.** The myCobot 280 ships in three controller variants:

| Variant | Onboard compute | URDF in `mycobot_description` |
|---|---|---|
| myCobot 280 M5 | ESP32 (M5Stack), no Linux | `urdf/mycobot_280/mycobot_280.urdf` |
| **myCobot 280 Pi** | Raspberry Pi 4, Ubuntu Mate | `urdf/mycobot_280_pi/mycobot_280_pi.urdf` ← we use this |
| myCobot 280 JN | NVIDIA Jetson Nano | `urdf/mycobot_280_jn/mycobot_280_jn.urdf` |

The **arm above the base flange is identical** across all three — same 6-DOF kinematics, same link lengths, same 280 mm reach, same 250 g payload, same ±0.5 mm repeatability. Only the controller box at the base differs (M5Stack box / Raspberry Pi enclosure / Jetson Nano carrier). The vendor maintains a separate URDF per variant so the base-box visual matches the real hardware — the kinematic chain above the base flange is shared.

We pin to `mycobot_280_pi.urdf` to match the hardware we'll actually order. If we later want to flip to the M5 or JN, swap one path in the launch file — the arm itself will not change shape.

## Quick start

Use `jazzy` if you are on Ubuntu 24.04, `humble` if you are on 22.04. Step 2 (Gazebo) is Jazzy-only for now.

```bash
# 0. Make sure you are on a branch that actually has this folder
cd ~/ros2_ws/src/place-items-on-shelf
git fetch origin
git switch add-elephant-robotics-best-option-task   # or `main` once this PR is merged

# 1. Init the submodule (only needed once, after the first clone)
git submodule update --init --recursive

# 2. Build only what we need
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash        # or /opt/ros/humble/setup.bash
colcon build --packages-select mycobot_description --symlink-install

# 3. Source the workspace
source ~/ros2_ws/install/setup.bash

# 4a. Launch Step 1 (RViz viewer — always works)
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/view_in_rviz.launch.py

# 4b. Launch Step 2 (Gazebo Sim — needs gz-harmonic + ros2_control packages first)
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/sim_in_gazebo.launch.py
```

For full instructions including the apt installs for Step 2, see [`docs/run.md`](docs/run.md) and [`docs/run_sim.md`](docs/run_sim.md).

## How this folder fits the bigger plan

The end goal is the HPLC autosampler use case described in the project README: a stationary arm that picks vials and places them into tray slots. Steps 1–3 give us a controllable arm in simulation; Step 4 brings the autosampler tray and vial racks into the scene; Steps 5–6 close the perception → planning → execution loop; Step 7 swaps the simulator for the real arm.

The decision record that picked this arm in the first place lives in [`../elephant-robotics-best-option/README.md`](../elephant-robotics-best-option/README.md).

## Sources

- [`elephantrobotics/mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) — the upstream ROS 2 package set we vendor as a submodule.
- [`mycobot_280_pi.urdf` on `humble`](https://github.com/elephantrobotics/mycobot_ros2/blob/humble/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf) — the specific URDF we load.
- [Elephant Robotics myCobot 280 Pi product page](https://shop.elephantrobotics.com/products/mycobot-pi-worlds-smallest-and-lightest-six-axis-collaborative-robot)
- [`gz_ros2_control`](https://github.com/ros-controls/gz_ros2_control) — the Gazebo Sim hardware interface plugin we use in Step 2.
