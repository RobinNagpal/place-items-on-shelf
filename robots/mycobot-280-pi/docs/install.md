# Install — myCobot 280 Pi (no hardware required)

Target environment, matching Elephant Robotics' officially supported stack for `mycobot_ros2`:

- **OS:** Ubuntu 22.04 LTS (native or WSL 2 on Windows 11)
- **ROS 2:** Humble
- **Python:** 3.10 (system Python; do **not** use conda)

> The `mycobot_ros2` repo's `humble` branch is what Elephant Robotics ships and tests against. Ubuntu 24.04 + ROS 2 Jazzy is reported to work with the same branch (see Elephant Robotics docs), but Humble is the safer default for a first pass.

If you already have ROS 2 Humble installed, skip to step 2.

## 1. Install ROS 2 Humble

Follow the official guide: <https://docs.ros.org/en/humble/Installation/Ubuntu-Install-Debs.html>. The condensed version:

```bash
sudo apt update && sudo apt install -y software-properties-common curl
sudo add-apt-repository universe
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key \
  -o /usr/share/keyrings/ros-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] \
  http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" \
  | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null
sudo apt update
sudo apt install -y ros-humble-ros-base
```

## 2. Install the dev tools we need

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-humble-rviz2 \
  ros-humble-robot-state-publisher \
  ros-humble-joint-state-publisher-gui \
  ros-humble-xacro

# First-time rosdep init (skip the init line if it complains it's already done)
sudo rosdep init 2>/dev/null || true
rosdep update
```

## 3. Make sourcing automatic (optional but convenient)

```bash
echo 'source /opt/ros/humble/setup.bash' >> ~/.bashrc
```

Open a fresh terminal afterwards.

## 4. WSL only — GUI passthrough

WSL 2 on Windows 11 has built-in WSLg, so RViz windows open natively with no extra setup. Verify with:

```bash
sudo apt install -y x11-apps
xeyes
```

If a pair of eyes appears, GUI passthrough is working. Close it and continue.

## What's next

When this is done, go to [`docs/verify-env.md`](verify-env.md) to confirm everything is wired up before building.
