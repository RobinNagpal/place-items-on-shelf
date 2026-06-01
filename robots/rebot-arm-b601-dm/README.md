# reBot Arm B601 DM — software evaluation

We are evaluating whether to order the [Seeed reBot Arm B601 DM](https://www.seeedstudio.com/reBot-Arm-B601-DM-Bundle.html). This folder lets us exercise as much of its software stack as possible **without owning the hardware**.

## What this gives you today

A no-hardware URDF viewer in RViz. You see the arm model rendered with its meshes, and you can drag a slider for each joint to watch the arm move on screen. This validates Seeed's URDF, your ROS 2 toolchain, and your WSL GUI passthrough — three things that need to work before you spend money.

It does **not** simulate motion planning, contact physics, or grasping. Those need the real arm or Isaac Sim (Seeed has it on their roadmap for ~2026-06-20).

## Source code we depend on

The Seeed ROS 2 SDK is pulled in as a git submodule at:

```
src/rebotarm_ros2/   →   https://github.com/Seeed-Projects/reBotArmController_ROS2
```

It contains three ROS 2 packages:
- `rebotarm_msgs` — custom messages, services, actions
- `rebotarmcontroller` — controller node + example scripts (hardware-only)
- `rebotarm_bringup` — launch files, URDF (`reBot-DevArm_fixend.urdf`), RViz config

## Files in this folder

```
.
├── launch/
│   └── view_in_rviz.launch.py    # our no-hardware viewer (uses Seeed's URDF + RViz config)
├── docs/
│   ├── install.md                # one-time setup: ROS 2 Jazzy + dev tools
│   ├── verify-env.md             # check your environment is ready
│   └── run.md                    # how to run the viewer
└── src/
    └── rebotarm_ros2/            # git submodule, see above
```

## Quick start

See [`docs/run.md`](docs/run.md). The short version:

```bash
# from this directory
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
ros2 launch $(pwd)/launch/view_in_rviz.launch.py
```

## What's next

When Seeed releases their Isaac Sim integration (~2026-06-20 per their roadmap), we will add a sibling launch file here (e.g. `launch/sim_in_isaac.launch.py`) that loads their official USD model instead of swapping out anything in this scaffold.
