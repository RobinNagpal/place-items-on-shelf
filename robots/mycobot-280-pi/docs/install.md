# Install — myCobot 280 Pi (no hardware required)

The repo now leans on the **`automaticaddison/mycobot_ros2`** stack as upstream — it ships a working URDF, Gazebo simulation, MoveIt 2 config, MoveIt Task Constructor demos, and a pick-and-place example for this exact arm. Our job is to point at it correctly and add the HPLC-specific scene later.

## Target environment

| Ubuntu | ROS 2 | Python | Notes |
|---|---|---|---|
| **24.04 LTS** | **Jazzy** (recommended) | 3.12 | Default for fresh WSL 2 in 2026. |
| 22.04 LTS | Humble | 3.10 | Also supported by addison's repo. |

If you already have ROS 2 installed, run `ros2 --version` and `echo $ROS_DISTRO` to confirm which, then skip to step 2.

## 1a. Install ROS 2 Jazzy (Ubuntu 24.04 — recommended)

Official guide: <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>. Condensed:

```bash
sudo apt update && sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-jazzy-ros-base
```

## 1b. Install ROS 2 Humble (Ubuntu 22.04 — alternative)

Same idea, swap `jazzy` for `humble`:

```bash
sudo apt install -y ros-humble-ros-base
```

## 2. Install build tools

```bash
DISTRO=jazzy   # or: humble
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  build-essential \
  git
sudo rosdep init 2>/dev/null || true
rosdep update
```

## 3. Install Gazebo Harmonic (Jazzy only)

Required for Step 2 and beyond. Skip if you are stopping at Step 1.

```bash
sudo apt install -y gz-harmonic
gz sim --version
# Expected: Gazebo Sim, version 8.x.x   (Harmonic)
```

(On Humble, the equivalent is Gazebo Fortress — `sudo apt install ros-humble-ros-gz` and `gz-fortress`. Not covered in detail here.)

## 4. Install addison's stack dependencies via rosdep

The cleanest way to install everything `automaticaddison/mycobot_ros2` needs is to let `rosdep` read its `package.xml` files and fetch system packages automatically. From the workspace root, **after** the submodule is checked out (see [`run.md`](run.md) step 0):

```bash
DISTRO=jazzy
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y --rosdistro ${DISTRO}
```

That pulls in MoveIt 2, MoveIt Task Constructor, ros2_control, ros2_controllers, ros_gz_sim, ros_gz_bridge, ros_gz_image, gz_ros2_control, joint_state_publisher_gui, xacro, rviz2 — basically everything Steps 1 through 6 need in one shot.

If `rosdep` complains about unknown keys, that's a sign your `${DISTRO}` is wrong or `rosdep update` was skipped — fix and rerun.

## 5. Make sourcing automatic (optional)

```bash
DISTRO=jazzy   # or: humble
echo "source /opt/ros/${DISTRO}/setup.bash" >> ~/.bashrc
```

Open a fresh terminal afterwards.

## 6. WSL only — GUI passthrough

WSL 2 on Windows 11 has built-in WSLg, so RViz and Gazebo windows open natively with no extra setup. Quick smoke test:

```bash
sudo apt install -y x11-apps
xeyes
```

If a pair of eyes appears, GUI passthrough is working. Close it and continue.

## What's next

When this is done, go to [`docs/verify-env.md`](verify-env.md) to confirm everything is wired up before building.
