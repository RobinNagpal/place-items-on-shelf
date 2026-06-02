# place-items-on-shelf

A multi-robot evaluation monorepo. Current target: a stationary arm that picks small vials and places them into HPLC autosampler tray slots.

## What runs today

| Step | What | Status |
|---|---|---|
| 1 | myCobot 280 Pi URDF in RViz (with sliders) | ✅ |
| 2 | myCobot 280 Pi in Gazebo Sim — physics, ros2_control, JointTrajectoryController, ROS↔Gazebo bridge, RViz attached | ✅ |
| 3 | MoveIt 2 motion planning | ⬜ next |
| 4 | HPLC autosampler tray + vial-rack Gazebo scene (the only step we author ourselves) | ⬜ |
| 5–6 | Vision + scripted pick-and-place | ⬜ |
| 7 | Real hardware | ⬜ blocked on order |

Steps 1, 2, 3, 5, and 6 are covered by [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2), vendored as a git submodule pinned to commit `a75c80d`. Step 4 is the only project-specific piece left to write.

## Quick start (Ubuntu 24.04 + ROS 2 Jazzy)

```bash
# 0. Clone with submodule
git clone --recurse-submodules https://github.com/RobinNagpal/place-items-on-shelf.git \
  ~/ros2_ws/src/place-items-on-shelf

# 1. Bridge addison's hardcoded source path to our submodule (one-time)
ln -sfT \
  ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/src/mycobot_ros2 \
  ~/ros2_ws/src/mycobot_ros2

# 2. Install ROS 2 + Gazebo Harmonic deps
source /opt/ros/jazzy/setup.bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy

# 3. Build
colcon build \
  --packages-select mycobot_interfaces mycobot_description mycobot_moveit_config mycobot_gazebo \
  --symlink-install
source install/setup.bash

# 4a. Step 1 — RViz viewer
ros2 launch mycobot_description robot_state_publisher.launch.py

# 4b. Step 2 — Gazebo Sim
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py
```

Full setup and troubleshooting docs:
- [`robots/mycobot-280-pi/docs/install.md`](robots/mycobot-280-pi/docs/install.md)
- [`robots/mycobot-280-pi/docs/run.md`](robots/mycobot-280-pi/docs/run.md) — Step 1
- [`robots/mycobot-280-pi/docs/run_sim.md`](robots/mycobot-280-pi/docs/run_sim.md) — Step 2
- [`robots/mycobot-280-pi/README.md`](robots/mycobot-280-pi/README.md) — full roadmap + the "why this arm" decision record

## Why this arm

Decision record: [`robots/elephant-robotics-best-option/README.md`](robots/elephant-robotics-best-option/README.md). Short version: smallest in the Elephant Robotics lineup, biggest community footprint, easiest sensor integration, first-party ROS 2 / Gazebo / MoveIt packages.
