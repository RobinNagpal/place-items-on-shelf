# Verify your environment — myCobot 280 Pi viewer

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

> If `$ROS_DISTRO` is empty after sourcing, your `~/.bashrc` may be sourcing the wrong distro or none at all. Check it and re-source.

## 2. The packages we need are installed

```bash
ros2 pkg list | grep -E '^(rviz2|robot_state_publisher|joint_state_publisher_gui|xacro)$'
```

Expected output (order may differ):

```
joint_state_publisher_gui
robot_state_publisher
rviz2
xacro
```

If any are missing, re-run the `sudo apt install` block in [`install.md`](install.md) — make sure you used the right `ros-<distro>-...` prefix for your ROS 2 distro.

## 3. You are on a branch that has this folder

If you cloned the repo before this folder existed (or you switched back to `main` before it was merged), the launch file won't be on disk yet. From the repo root:

```bash
ls robots/mycobot-280-pi/launch/view_in_rviz.launch.py
```

If that prints `No such file or directory`, you are on the wrong branch. See [`run.md`](run.md) step 0 for how to fix it.

## 4. The submodule is checked out

From the repo root:

```bash
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf
```

Expected: the file path is printed back. If you get `No such file or directory`, the submodule is not initialised — see [`run.md`](run.md) step 0.

## 5. WSL GUI passthrough (WSL only)

```bash
xeyes
```

A pair of cartoon eyes should appear. Close them.

If `xeyes` is missing: `sudo apt install -y x11-apps`. If it installs but the window does not appear, you are on Windows 10 or an older WSL build — upgrade to WSL 2 on Windows 11 (WSLg ships built-in), or install a third-party X server (VcXsrv) and export `DISPLAY` manually.

## What's next

If all five checks pass, go to [`docs/run.md`](run.md) to build and launch the viewer.
