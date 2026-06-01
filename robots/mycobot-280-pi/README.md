# myCobot 280 Pi — Step 1: no-hardware RViz viewer

This folder is the first step of bringing up the **Elephant Robotics myCobot 280 Pi** in this project. It is intentionally narrow: it lets you load the manufacturer URDF, see the arm rendered at exact hardware scale in RViz, and drag a slider per joint to confirm the kinematics and joint limits.

It does **not** simulate physics, motion planning, contact, or grasping. Those are later steps. The point of Step 1 is to validate the URDF + your ROS 2 toolchain before any other work — and before any hardware purchase.

## What's in this folder

```
.
├── launch/
│   └── view_in_rviz.launch.py   # robot_state_publisher + JSP-GUI + RViz
├── rviz/
│   └── view.rviz                # pinned RViz config (RobotModel on /robot_description, grid, TF)
├── docs/
│   ├── install.md               # one-time: ROS 2 Humble on Ubuntu 22.04 (incl. WSL)
│   ├── verify-env.md            # quick checks before you build
│   └── run.md                   # build + launch, with the ~/ros2_ws layout you mentioned
└── src/
    └── mycobot_ros2/            # git submodule: elephantrobotics/mycobot_ros2 (branch: humble)
```

The submodule is the upstream Elephant Robotics ROS 2 package set. We only build `mycobot_description` from it for this step — see `docs/run.md`.

## Do all myCobot 280 variants share the same shape?

**Yes — for our purposes.** The myCobot 280 ships in three controller variants:

| Variant | Onboard compute | URDF in `mycobot_description` |
|---|---|---|
| myCobot 280 M5 | ESP32 (M5Stack), no Linux | `urdf/mycobot_280/mycobot_280.urdf` |
| **myCobot 280 Pi** | Raspberry Pi 4, Ubuntu Mate | `urdf/mycobot_280_pi/mycobot_280_pi.urdf` ← we use this |
| myCobot 280 JN | NVIDIA Jetson Nano | `urdf/mycobot_280_jn/mycobot_280_jn.urdf` |

The **arm above the base flange is identical** across all three — same 6-DOF kinematics, same link lengths, same 280 mm reach, same 250 g payload, same ±0.5 mm repeatability. The only difference is the **controller box at the base**: a small M5Stack box on the M5, a thicker Raspberry Pi enclosure on the Pi, a Jetson Nano carrier on the JN. The vendor maintains a separate URDF per variant primarily so the base box visual matches the real hardware — the kinematic chain from the base flange upward is shared.

We pin to `mycobot_280_pi.urdf` to match the hardware we'll actually order. If we later want to flip to the M5 or JN, swap one path in `view_in_rviz.launch.py` — the arm itself will not change shape.

## Quick start

The condensed version of `docs/run.md`. Use `jazzy` if you are on Ubuntu 24.04, `humble` if you are on 22.04.

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

# 4. Launch
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/view_in_rviz.launch.py
```

You should see an RViz window with the arm at 280 mm scale and a slider GUI with six joints.

## How this folder fits the bigger plan

Step 1 (this PR): URDF in RViz, no physics. **You are here.**
Step 2: Gazebo Harmonic bring-up with `ros2_control` so the same joint commands work in sim and on the real arm.
Step 3: MoveIt 2 for motion planning.
Step 4: A scene — tabletop + shelf + a small target object.
Step 5: USB camera + AprilTag detection.
Step 6: First scripted pick-and-place in sim.
Step 7 (after hardware arrives): Plug in the real arm, same launch file with `use_real_hardware:=true`.

The decision record that picked this arm lives in [`../elephant-robotics-best-option/README.md`](../elephant-robotics-best-option/README.md).

## Sources

- [`elephantrobotics/mycobot_ros2`](https://github.com/elephantrobotics/mycobot_ros2) — the upstream ROS 2 package set we vendor as a submodule.
- [`mycobot_280_pi.urdf` on `humble`](https://github.com/elephantrobotics/mycobot_ros2/blob/humble/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf) — the specific URDF we load.
- [Elephant Robotics myCobot 280 Pi product page](https://shop.elephantrobotics.com/products/mycobot-pi-worlds-smallest-and-lightest-six-axis-collaborative-robot)
