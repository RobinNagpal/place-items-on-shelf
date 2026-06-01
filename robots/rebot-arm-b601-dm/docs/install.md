# Install — reBot Arm B601 DM (no hardware required)

Target environment, matching Seeed's recommended stack:

- **OS:** Ubuntu 24.04 LTS (native or WSL 2 on Windows 11)
- **ROS 2:** Jazzy
- **Python:** 3.12 (system Python; do not use conda)

If you already have ROS 2 Jazzy installed, skip to step 2.

## 1. Install ROS 2 Jazzy

Follow the official guide: <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>. The summary:

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

## 2. Install the dev tools we need

```bash
sudo apt install -y \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool \
  ros-jazzy-rviz2 \
  ros-jazzy-robot-state-publisher \
  ros-jazzy-joint-state-publisher-gui \
  ros-jazzy-xacro

# First-time rosdep init (skip the init line if it complains it's already done)
sudo rosdep init 2>/dev/null || true
rosdep update
```

## 3. Make sourcing automatic (optional but convenient)

```bash
echo 'source /opt/ros/jazzy/setup.bash' >> ~/.bashrc
```

Open a fresh terminal afterwards.

## 4. Clone this monorepo with submodules

The Seeed ROS 2 SDK is pulled in as a git submodule. **You must initialize it, or colcon will find zero packages to build.**

Fresh clone (recommended):

```bash
git clone --recurse-submodules https://github.com/RobinNagpal/place-items-on-shelf.git
cd place-items-on-shelf
```

If you already cloned without `--recurse-submodules`, or you switched branches with `git switch`/`git checkout` (which updates the submodule pointer but does NOT update the working tree), run this from the repo root:

```bash
git submodule update --init --recursive
```

Verify the submodule actually has content:

```bash
ls robots/rebot-arm-b601-dm/src/rebotarm_ros2/src
# Expect: rebotarm_bringup  rebotarm_msgs  rebotarmcontroller
```

If that directory is empty, the submodule init did not happen — re-run the command above.

## 5. Build the colcon workspace

```bash
cd robots/rebot-arm-b601-dm     # this folder is the colcon workspace root
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
source install/setup.bash
```

The build should report **3 packages finished** (`rebotarm_msgs`, `rebotarm_bringup`, `rebotarmcontroller`). If it says `0 packages finished`, the submodule is not initialized — go back to step 4.

The build will warn (loudly) that the controller node expects hardware. That is expected — we are not running the controller, only the URDF viewer.

## 6. Verify your environment

Before trying to launch, run through [`verify-env.md`](verify-env.md).

## Notes

- We do **not** need `git-lfs`. The Seeed repo does not use it.
- We do **not** install `motorbridge` or `reBotArm_control_py` (Seeed's hardware SDK). Those are only needed when you have the real arm plugged in.
