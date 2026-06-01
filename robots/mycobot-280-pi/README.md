# myCobot 280 Pi — simulation-first bring-up

This folder builds up the **Elephant Robotics myCobot 280 Pi** in simulation, step by step, before any hardware is ordered. Each step adds one capability on top of the previous one and is intended to be runnable on its own.

The target end behaviour is a **stationary arm** that picks small items (HPLC autosampler vials) from a holder and places them into specific slots in a tray — i.e. "place items on shelf." Everything below is sized around that goal.

**Upstream stack:** we lean on [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2), vendored as a git submodule at `src/mycobot_ros2/` and pinned to commit `a75c80d` (Jul 2025). That repo already ships URDF, Gazebo, MoveIt 2, MoveIt Task Constructor demos, and a pick-and-place example for this exact arm. We don't reimplement any of that — we configure it, run it, and add the HPLC-specific scene later.

## Roadmap — where you are, where to start next

| # | Step | Status | How to verify |
|---|---|---|---|
| 1 | URDF in RViz (no physics, no controllers) | ✅ via upstream — `mycobot_description` | `ros2 launch mycobot_description robot_state_publisher.launch.py` |
| 2 | Gazebo Sim + `ros2_control` + JTC + ROS↔Gazebo bridge | ✅ via upstream — `mycobot_gazebo` | `ros2 launch mycobot_gazebo mycobot.gazebo.launch.py` |
| 3 | MoveIt 2 motion planning | ✅ via upstream — `mycobot_moveit_config`, `mycobot_moveit_demos` | `ros2 launch mycobot_moveit_demos <demo>.launch.py` |
| 4 | Scene: HPLC autosampler tray + vial rack | 🟨 **next — ours to author** | new world file under `worlds/`, swap with `world_file:=hplc_autosampler.world` |
| 5 | Vision: RGBD camera + object detection | ✅ via upstream — `mycobot_mtc_pick_place_demo` covers RGBD + RANSAC/Hough | (run the addison MTC demo, see their README) |
| 6 | Scripted pick-and-place — vial → tray slot | 🟨 next after Step 4 — retarget addison's MTC demo | adapt `mycobot_mtc_pick_place_demo` to our HPLC scene |
| 7 | Real hardware — `use_real_hardware:=true` | ⬜ blocked on order | (after hardware arrives) |

When you come back cold, look at the top "🟨" or "⬜" row — that's where to pick up.

## What's in this folder

```
.
├── docs/
│   ├── install.md       # one-time setup (ROS 2 + Gazebo + addison's rosdep deps)
│   ├── verify-env.md    # quick checks before you build
│   ├── run.md           # Step 1: ros2 launch mycobot_description robot_state_publisher.launch.py
│   └── run_sim.md       # Step 2: ros2 launch mycobot_gazebo mycobot.gazebo.launch.py
└── src/
    └── mycobot_ros2/    # git submodule: automaticaddison/mycobot_ros2 @ a75c80d
```

There are no launch files, RViz configs, controllers.yaml, world files, or URDFs of our own in this folder — addison's repo ships all of that for Steps 1–3 and 5–6. The only thing we'll add later is `worlds/hplc_autosampler.world` (Step 4).

## Why addison's stack and not our own scaffold

The previous round of this PR had us authoring a Gazebo + ros2_control + URDF wrapper from scratch. That work is reverted because [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2) already ships an end-to-end, ROS 2 Jazzy / Humble–targeted stack for **this exact arm**, including:

- A complete URDF (`mycobot_description/urdf/robots/mycobot_280.urdf.xacro`) with adaptive gripper, optional RGBD camera, ros2_control + Gazebo plugin baked in.
- A working Gazebo launch (`mycobot_gazebo/mycobot.gazebo.launch.py`) with three worlds, including a `pick_and_place_demo.world`.
- A MoveIt 2 config (`mycobot_moveit_config`) ready to plan.
- A MoveIt Task Constructor pick-and-place demo (`mycobot_mtc_pick_place_demo`) with RGBD object detection.

Re-implementing any of this would be churn. The right move is to stand on it and add only what addison's repo can't know about — the HPLC autosampler scene.

## Do all myCobot 280 variants share the same shape?

**Yes — for our purposes.** The myCobot 280 ships in three controller variants:

| Variant | Onboard compute | Arm shape |
|---|---|---|
| myCobot 280 M5 | ESP32 (M5Stack), no Linux | same |
| **myCobot 280 Pi** | Raspberry Pi 4, Ubuntu Mate | same — we order this one |
| myCobot 280 JN | NVIDIA Jetson Nano | same |

The arm above the base flange is identical across all three — same 6-DOF kinematics, same link lengths, same 280 mm reach, same 250 g payload, same ±0.5 mm repeatability. Only the controller box at the base differs. addison's `mycobot_280.urdf.xacro` models the shared arm, so it represents all three variants for simulation purposes.

## Quick start

```bash
# 0. Be on the branch with this folder
cd ~/ros2_ws/src/place-items-on-shelf
git fetch origin
git switch add-elephant-robotics-best-option-task

# 1. Init the submodule (only once per clone)
git submodule update --init --recursive

# 2. Source ROS 2
source /opt/ros/jazzy/setup.bash       # or /opt/ros/humble/setup.bash

# 3. Install addison's runtime deps via rosdep (one shot for Steps 1-6)
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy

# 4. Build
colcon build --symlink-install   # everything; or --packages-up-to mycobot_gazebo for Step 2

# 5. Source the workspace
source install/setup.bash

# 6a. Run Step 1 (RViz viewer)
ros2 launch mycobot_description robot_state_publisher.launch.py

# 6b. Run Step 2 (Gazebo Sim)
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py
```

Full prose-form instructions in [`docs/install.md`](docs/install.md), [`docs/run.md`](docs/run.md), and [`docs/run_sim.md`](docs/run_sim.md).

## How this folder fits the bigger plan

The end goal is the HPLC autosampler use case described above: a stationary arm that picks vials and places them into tray slots. addison's stack gets us Steps 1–3 + 5–6 essentially for free; our job reduces to **Step 4** — model the HPLC autosampler tray, the vial rack, and the vials as Gazebo objects, then drop them into a world that swaps in for `pick_and_place_demo.world`.

The decision record that picked this arm lives in [`../elephant-robotics-best-option/README.md`](../elephant-robotics-best-option/README.md).

## Sources

- [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2) — the upstream ROS 2 stack we vendor as a submodule.
- [`mycobot_280.urdf.xacro` @ a75c80d](https://github.com/automaticaddison/mycobot_ros2/blob/a75c80d/mycobot_description/urdf/robots/mycobot_280.urdf.xacro) — the URDF we load (gripper + ros2_control + gz plugin already included).
- [`mycobot.gazebo.launch.py` @ a75c80d](https://github.com/automaticaddison/mycobot_ros2/blob/a75c80d/mycobot_gazebo/launch/mycobot.gazebo.launch.py) — the Step 2 launch file.
- [Elephant Robotics myCobot 280 Pi product page](https://shop.elephantrobotics.com/products/mycobot-pi-worlds-smallest-and-lightest-six-axis-collaborative-robot)
