# Verify your environment — myCobot 280 Pi (using addison's stack)

Quick checks to make sure the install actually worked before you spend time on `colcon build`.

## 1. ROS 2 is on PATH

```bash
ros2 --version
# Expected: ros2 cli version: 0.x.x

echo $ROS_DISTRO
# Expected: jazzy   (or: humble)
```

If `ros2` is not found, source the setup file matching whichever distro you installed:

```bash
source /opt/ros/jazzy/setup.bash      # Ubuntu 24.04
# or
source /opt/ros/humble/setup.bash     # Ubuntu 22.04
```

## 2. You are on a branch that has this folder

If you cloned the repo before this folder existed (or you switched back to `main` before it was merged), the submodule pointer won't be on disk. From the repo root:

```bash
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_gazebo/launch/mycobot.gazebo.launch.py
```

If that prints `No such file or directory`, you are on the wrong branch or the submodule isn't checked out. See [`run.md`](run.md) step 0.

## 3. addison's packages are visible to colcon

From the workspace root:

```bash
cd ~/ros2_ws
colcon list --packages-up-to mycobot_gazebo 2>/dev/null | sort
```

Expected (order may vary): `mycobot_bringup`, `mycobot_description`, `mycobot_gazebo`, `mycobot_interfaces`, `mycobot_moveit_config`. If colcon prints nothing, the submodule isn't initialised — see [`run.md`](run.md) step 0.

## 4. Gazebo Sim is installed (Jazzy only — skip for pure RViz)

```bash
gz sim --version
# Expected (Jazzy): Gazebo Sim, version 8.x.x   (Harmonic)
```

If not found, re-run the `gz-harmonic` apt install in [`install.md`](install.md) step 3.

## 5. addison's runtime dependencies are present

```bash
ros2 pkg list | grep -E '^(rviz2|robot_state_publisher|joint_state_publisher_gui|xacro|ros_gz_sim|ros_gz_bridge|gz_ros2_control|joint_trajectory_controller|joint_state_broadcaster|moveit_ros_planning|moveit_task_constructor_core|control_msgs)$' | sort
```

Expected (order may vary):

```
control_msgs
gz_ros2_control
joint_state_broadcaster
joint_state_publisher_gui
joint_trajectory_controller
moveit_ros_planning
moveit_task_constructor_core
robot_state_publisher
ros_gz_bridge
ros_gz_sim
rviz2
xacro
```

Anything missing means `rosdep install ...` in [`install.md`](install.md) step 4 didn't finish — rerun it.

## 6. WSL GUI passthrough (WSL only)

```bash
xeyes
```

A pair of cartoon eyes should appear. Close them. If `xeyes` is missing: `sudo apt install -y x11-apps`.

## What's next

If checks 1–3 + 6 pass, go to [`docs/run.md`](run.md) for Step 1 (URDF in RViz).
If 4 and 5 also pass, go to [`docs/run_sim.md`](run_sim.md) for Step 2 (Gazebo simulation).
