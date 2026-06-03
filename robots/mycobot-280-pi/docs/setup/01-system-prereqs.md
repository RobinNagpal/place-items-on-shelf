# 01 — System Prerequisites

What you need installed on your machine **before** you can clone anything or build
anything. This document is the "step zero" that the rest of the docs (concepts,
recipes, four-terminals) take for granted.

## Target platform

The whole pipeline has been exercised on:

- **Ubuntu 24.04 LTS** (Noble Numbat) — desktop install, not server.
- **x86_64**. ARM64 (a real Raspberry Pi) is the long-term target for hardware, but
  the simulation pipeline was not validated on ARM as of this writing.
- **NVIDIA or integrated GPU** is *not* required. Gazebo Sim renders fine on CPU; it
  just runs slower.

You can use a VM, but:

- Give it ≥ 8 GB RAM and ≥ 4 CPU cores. Gazebo + MoveIt + RViz together push past
  4 GB.
- Enable 3D acceleration in the hypervisor settings. Without it, Gazebo's GUI may
  crash on launch.

## ROS 2 distribution: Jazzy

Every command in this repo's docs assumes **ROS 2 Jazzy Jalisco**. Jazzy ships with
Ubuntu 24.04 and pairs with **Gazebo Harmonic** (the version used by addison's
`mycobot_gazebo` package). Mixing distributions (e.g. Humble on 22.04 with a
backported Gazebo) is not supported here.

Install ROS 2 Jazzy from the official instructions:

- <https://docs.ros.org/en/jazzy/Installation/Ubuntu-Install-Debs.html>

Pick the **desktop** variant (`ros-jazzy-desktop`) — it includes RViz 2, demo nodes,
and the visualization stack the docs reference.

Verify the install:

```bash
source /opt/ros/jazzy/setup.bash
ros2 --version
ros2 doctor --report   # optional but useful
```

## Build tools

In addition to ROS itself, you need the colcon workspace toolchain and a working
C++ build environment.

```bash
sudo apt update
sudo apt install -y \
  build-essential \
  cmake \
  git \
  python3-colcon-common-extensions \
  python3-rosdep \
  python3-vcstool
```

If `rosdep` has never been initialised on this machine, run it once:

```bash
sudo rosdep init       # ignore "already exists" errors
rosdep update
```

## ROS 2 / MoveIt / Gazebo apt packages

The pieces the docs lean on most:

```bash
sudo apt install -y \
  ros-jazzy-moveit \
  ros-jazzy-moveit-task-constructor \
  ros-jazzy-moveit-task-constructor-capabilities \
  ros-jazzy-ros-gz \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-joint-state-publisher \
  ros-jazzy-xacro
```

A few of these are pulled in transitively by `ros-jazzy-desktop`, but listing them
explicitly makes apt errors easier to diagnose if one is missing.

The `moveit-task-constructor-capabilities` package matters specifically: without
it, the **Terminal 2** `move_group` log will be missing
`ExecuteTaskSolutionCapability`, and the MTC demo in
[`recipes/the-four-terminals.md`](../recipes/the-four-terminals.md) will not
execute (it'll plan and then silently stop).

## Sanity check

Once the apt installs finish, sourcing Jazzy should give you working `ros2`,
`colcon`, and Gazebo commands:

```bash
source /opt/ros/jazzy/setup.bash
ros2 pkg list | grep moveit          # should print many lines
gz sim --version                     # should print a Gazebo Harmonic version
```

If `gz sim` is missing, check that `ros-jazzy-ros-gz` actually installed — apt may
have skipped it on minimal ISOs.

## What's next

You now have the *base* installation. Nothing repo-specific yet. The next doc
sets up a colcon workspace and clones the upstream `mycobot_ros2` packages our
project depends on.

→ Next: [02-workspace-and-upstream.md](02-workspace-and-upstream.md)
