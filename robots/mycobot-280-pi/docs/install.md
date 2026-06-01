# Install — myCobot 280 Pi (no hardware required)

Two supported environments. Pick whichever matches the Ubuntu version you already have on your machine / in WSL. You do **not** need both.

| Ubuntu | ROS 2 | Python | Notes |
|---|---|---|---|
| **24.04 LTS** | **Jazzy** (recommended for new installs) | 3.12 | What you get on a fresh WSL 2 Ubuntu install in 2026. |
| 22.04 LTS | Humble | 3.10 | Matches Elephant Robotics' nominally tested branch. |

The `mycobot_description` package we build for this step is just URDF + meshes + `ament_cmake`. It has no distro-specific code, so it works equally well on either. Pick the one that matches your OS — don't try to install both side by side.

> If you already have one of these installed, run `ros2 --version` and `echo $ROS_DISTRO` to confirm which. Then skip to step 2.

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

Same commands as above, but swap `jazzy` for `humble`:

```bash
sudo apt install -y ros-humble-ros-base
```

## 2. Install the dev tools we need

Replace `<distro>` with `jazzy` or `humble` to match what you installed:

```bash
DISTRO=jazzy   # or: humble
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-${DISTRO}-rviz2 \
  ros-${DISTRO}-robot-state-publisher \
  ros-${DISTRO}-joint-state-publisher-gui \
  ros-${DISTRO}-xacro

# First-time rosdep init (skip the init line if it complains it's already done)
sudo rosdep init 2>/dev/null || true
rosdep update
```

## 3. Make sourcing automatic (optional but convenient)

```bash
DISTRO=jazzy   # or: humble
echo "source /opt/ros/${DISTRO}/setup.bash" >> ~/.bashrc
```

Open a fresh terminal afterwards.

## 4. WSL only — GUI passthrough

WSL 2 on Windows 11 has built-in WSLg, so RViz windows open natively with no extra setup. Verify with:

```bash
sudo apt install -y x11-apps
xeyes
```

If a pair of eyes appears, GUI passthrough is working. Close it and continue.

## 5. (Step 2 only — Jazzy) Gazebo Harmonic + ros2_control

You only need this section if you are moving on to the **Gazebo simulation** step. For just the RViz viewer (Step 1), skip it.

```bash
DISTRO=jazzy
sudo apt install -y \
  ros-${DISTRO}-ros-gz \
  ros-${DISTRO}-gz-ros2-control \
  ros-${DISTRO}-ros2-control \
  ros-${DISTRO}-ros2-controllers \
  ros-${DISTRO}-joint-state-broadcaster \
  ros-${DISTRO}-joint-trajectory-controller \
  ros-${DISTRO}-control-msgs \
  gz-harmonic
```

The Humble path (Ubuntu 22.04, Gazebo Fortress + `ign_ros2_control`) is not documented yet — open an issue if you need it.

## What's next

When this is done, go to [`docs/verify-env.md`](verify-env.md) to confirm everything is wired up before building.
