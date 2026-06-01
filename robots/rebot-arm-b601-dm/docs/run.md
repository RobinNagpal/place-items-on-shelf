# Run the no-hardware viewer

Prerequisite: you have completed [`install.md`](install.md) and [`verify-env.md`](verify-env.md).

## Launch

From this folder (`robots/rebot-arm-b601-dm/`):

```bash
source /opt/ros/jazzy/setup.bash
source install/setup.bash
ros2 launch $(pwd)/launch/view_in_rviz.launch.py
```

A few seconds later, two windows should open on your desktop:

1. **RViz 2** — shows the reBot Arm 3D model on a base frame.
2. **joint_state_publisher_gui** — a small panel with one slider per joint (joint1 … joint6, plus the gripper).

Drag any slider; the corresponding joint in RViz rotates in real time. That's it — you now have the arm rendered and articulated on your own machine, with no robot connected.

## What this actually proves

- ✅ Seeed's URDF parses correctly and the meshes render.
- ✅ Your ROS 2 Jazzy + colcon workspace + WSL GUI passthrough are all working.
- ✅ You understand the arm's joint layout, range of motion, and reach visually.

## What this does NOT prove

- ❌ Motion planning (no MoveIt2 in this launch).
- ❌ Collision checking against a shelf or other obstacles.
- ❌ Grasping or contact physics (RViz is a viewer, not a physics simulator).
- ❌ Whether real hardware would behave the same way.

For physics-accurate simulation, wait for Seeed's Isaac Sim drop (~2026-06-20) — when it lands, we will add `launch/sim_in_isaac.launch.py` to this same folder.

## Stop the launch

`Ctrl+C` in the terminal. Both windows will close.

## Troubleshooting

**`Package 'rebotarm_bringup' not found`**

Two possible causes:

1. **Submodule not initialized** (most common when you reached this branch via `git switch` or `git checkout` instead of `git clone --recurse-submodules`). Check:
   ```bash
   ls $(git rev-parse --show-toplevel)/robots/rebot-arm-b601-dm/src/rebotarm_ros2/src
   ```
   If that directory is empty, fix it:
   ```bash
   cd $(git rev-parse --show-toplevel)
   git submodule update --init --recursive
   cd robots/rebot-arm-b601-dm
   rm -rf build install log
   colcon build --symlink-install
   source install/setup.bash
   ```
   The build should now report **3 packages finished**.

2. **Forgot to source the local workspace.** Run `source install/setup.bash` from `robots/rebot-arm-b601-dm/` after building.

**`cannot open display` / no windows appear (WSL)**
WSLg is not working. See the WSL section of [`verify-env.md`](verify-env.md).

**RViz opens but the robot model is missing / shows red error text**
robot_state_publisher could not load the URDF. Confirm the submodule is checked out:
```bash
git submodule status
ls src/rebotarm_ros2/src/rebotarm_bringup/description/urdf/reBot-DevArm_fixend.urdf
```

**Joint sliders move but RViz doesn't update**
The `Fixed Frame` in RViz might not be set. In the RViz left panel, set `Global Options → Fixed Frame` to `base_link`. (Our shipped `rviz/view.rviz` already sets this; if you somehow loaded the Seeed-shipped `rebotarm.rviz` stub instead, re-launch with our `view_in_rviz.launch.py`.)

**RViz opens but the arm is a tiny dot, mouse won't pan/zoom, no Displays panel on the left**
You're looking at Seeed's `rebotarm.rviz` stub — it declares no Tools/Views/panels, so the camera defaults to ~10m away (making the 30cm arm look like a pixel) and no `MoveCamera` tool is loaded (so the mouse does nothing). Re-launch with `ros2 launch $(pwd)/launch/view_in_rviz.launch.py` from `robots/rebot-arm-b601-dm/` — that points RViz at our `rviz/view.rviz`, which sets the camera at 0.8 m, enables the MoveCamera/Select/FocusCamera tools, and shows the standard Displays/Views panels.
