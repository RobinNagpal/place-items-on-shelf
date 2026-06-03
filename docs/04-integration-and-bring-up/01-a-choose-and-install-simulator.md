# 01-a — Choose and Install the Simulator

This is the **first step of the simulation-first workflow.** Before
you touch real hardware, you build a virtual version of the cell and
run everything against it. This file is just about getting the
simulator on disk and confirming it launches.

Layer 3's [`07-simulation.md`](../03-software-stack/07-simulation.md)
compared the simulator products in depth. Re-skim it if you haven't
chosen yet. This file picks up from "you've chosen one" and goes to
"it's running on your machine."

## What you need before this step

- A computer that meets the simulator's spec (CPU, GPU, RAM, disk).
- An OS that the simulator supports (almost always Ubuntu LTS).
- A ROS 2 distro installed and sourced if you're going Gazebo or
  Isaac Sim.

## The four realistic picks

For an arm-on-a-table pick-and-place project, you're almost certainly
using one of:

| Simulator | Install path | Disk | Notes |
|-----------|--------------|------|-------|
| **Gazebo Harmonic** | `sudo apt install ros-${ROS_DISTRO}-ros-gz` | ~3 GB | The default for ROS 2. What this repo's myCobot 280 Pi setup uses. |
| **NVIDIA Isaac Sim** | Download via Omniverse Launcher, or pull the Docker image | ~30 GB | RTX-rendered, GPU required. Heavyweight. |
| **MuJoCo (≥ 3.x)** | `pip install mujoco`, plus `mujoco_menagerie` for arm models | ~500 MB | Research-grade physics. Less ROS 2 plumbing. |
| **PyBullet** | `pip install pybullet` | ~50 MB | Smallest, oldest. Use it if you just want to script Python. |

If you're not sure, **start with Gazebo Harmonic.** It's free, it's
ROS 2-native, and almost every tutorial assumes it.

## Install — by simulator

### Gazebo Harmonic (with ROS 2 Jazzy or Humble)

```
sudo apt update
sudo apt install ros-${ROS_DISTRO}-ros-gz ros-${ROS_DISTRO}-gz-ros2-control
gz sim --version          # confirm it runs
ros2 launch ros_gz_sim gz_sim.launch.py   # launches an empty world
```

For Humble (Gazebo Fortress instead of Harmonic):

```
sudo apt install ros-humble-ros-ign
```

### NVIDIA Isaac Sim

The supported install today is **container or Omniverse Launcher**.

```
docker pull nvcr.io/nvidia/isaac-sim:4.5.0
# OR
# download the Omniverse Launcher, then install Isaac Sim from there.
```

You need:

- An RTX-class GPU (3000-series or later).
- NVIDIA driver ≥ 535.
- Recent `nvidia-container-toolkit` if running in Docker.

Verify by running the launcher's "open Hello World" scene.

### MuJoCo

```
pip install mujoco
git clone https://github.com/google-deepmind/mujoco_menagerie.git
python -m mujoco.viewer --mjcf mujoco_menagerie/franka_emika_panda/scene.xml
```

For ROS 2 integration there's a `mujoco_ros2_control` plugin, plus
several community wrappers. The ROS 2 story is younger than Gazebo's;
expect to write some glue.

### PyBullet

```
pip install pybullet
python -c "import pybullet_data, pybullet as p; p.connect(p.GUI); p.setAdditionalSearchPath(pybullet_data.getDataPath()); p.loadURDF('plane.urdf'); input('press enter')"
```

You won't get a ROS 2 graph out of the box. Useful for pure-Python RL
experiments.

## How to confirm it's actually working

A "yes it installed" test is **not** a "yes it works" test. After
install, check:

1. The simulator window opens.
2. A default scene loads (an empty world, a hello-world robot).
3. Physics ticks (a dropped cube falls, an arm settles under gravity).
4. The ROS 2 bridge publishes topics — `ros2 topic list` shows the
   `clock`, `tf`, and joint-state topics if you used a robot scene.
5. (Isaac / Gazebo) RViz 2 can connect and visualise.

If any step fails, fix it now. Every later step assumes a working
simulator.

## Output of this step

```
Simulator chosen:     Gazebo Harmonic / Isaac Sim / MuJoCo / PyBullet
Version:              ___
Installed via:        apt / docker / pip / launcher
ROS 2 bridge:         ros_gz_bridge / isaac_ros / mujoco_ros2_control / none
GPU required:         yes / no — model: ___
Empty world launches?: yes / no
ROS 2 topics visible?: yes / no
RViz can connect?:    yes / no
```

## Common mistakes

1. **Installing two simulators "to compare" before either works.** You
   end up debugging both. Get one fully running first.
2. **ROS 2 distro / Gazebo version mismatch.** Harmonic pairs with
   Jazzy; Fortress with Humble. Mixing them is a rabbit hole.
3. **Trying Isaac Sim on a laptop GPU that's too small.** The
   launcher will look like it loads, then crash on the first scene.
   Check VRAM (16 GB+ comfortable for serious work).
4. **Skipping the "physics ticks" test.** A simulator window opening
   doesn't prove physics works. Drop a cube.
5. **Running the simulator inside a VM or WSL.** GPU passthrough is
   fiddly. Use bare metal for the simulator host if at all possible.

## What's next

The simulator runs. Now you put the *actual arm* and the *actual
scene* inside it.

→ Next: [01-b-build-the-virtual-cell.md](01-b-build-the-virtual-cell.md)
