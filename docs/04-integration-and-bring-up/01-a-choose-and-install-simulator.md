# 01-a — Choose and Install the Simulator

This is the **first step of the simulation-first workflow.** Before
you touch real hardware, you build a virtual version of the cell and
run everything against it. This file is about *picking* the simulator
and confirming it launches — not about how to install each one (every
tool has its own install guide, and they change).

Layer 3's [`07-simulation.md`](../03-software-stack/07-simulation.md)
compared the simulator products in depth. Re-skim it if you haven't
chosen yet. This file picks up from "you've chosen one" and goes to
"it's running on your machine."

## What you need before this step

- A computer that meets the simulator's spec (CPU, GPU, RAM, disk).
- An OS the simulator supports (almost always Ubuntu LTS).
- The vendor's install guide bookmarked.

## The popular simulator options

For an arm-on-a-table pick-and-place project, the following come up
again and again. The first four are the most common defaults in
2025–2026.

### Gazebo (Harmonic / Fortress)

The default open simulator for ROS 2 work. Free, well-integrated,
huge model library (Gazebo Fuel). Harmonic pairs with ROS 2 Jazzy;
Fortress with Humble.

**Best for:** any ROS 2 project unless you have a specific reason to
go elsewhere.

### NVIDIA Isaac Sim

GPU-rendered, photo-realistic, RTX-required. Built on USD. Pairs
tightly with **Isaac Lab** for reinforcement learning at scale.

**Best for:** vision-heavy work, RL training, AI-included development
where you'll throw a serious GPU at the problem.

### MuJoCo (≥ 3.x)

Lightweight, fast, research-grade physics. The default in academic
robotics and the basis of many RL benchmarks. **MJX** (JAX bindings)
gives thousands of parallel envs on one GPU. ROS 2 plumbing is
younger than Gazebo's.

**Best for:** RL training, contact-rich research, sim-to-real.

### PyBullet

Older, smaller, Python-first. Easy to script. Less polish than the
others.

**Best for:** quick Python experiments, education, lightweight RL.

### Webots (Cyberbotics)

Polished GUI, very approachable, strong in education and competitions.
ROS 2 support is solid. Free since 2018.

**Best for:** teaching, demos, students, projects where the GUI
matters.

### CoppeliaSim (formerly V-REP)

Long-standing research simulator. Scriptable in Lua / Python. Free
EDU edition.

**Best for:** legacy research code, multi-language scripting.

### Drake (Toyota Research Institute)

Less a simulator, more a "robotics toolbox" with physics, planning,
and visualisation in one C++ / Python library. Excellent contact
physics.

**Best for:** contact-rich manipulation research, when you want the
planner and the simulator in one stack.

### Genesis (2025-)

GPU-accelerated unified physics + rendering, fast-growing in
2025–2026. Worth tracking.

**Best for:** RL training, future-proofing.

### Unity / Unreal + ROS bridges

Game engines repurposed for high-fidelity visuals. AirSim (drones),
CARLA (driving), and several custom rigs for vision research run on
them.

**Best for:** photo-realistic vision data, novel sensor models.

## If you're not sure, default to…

Start with **Gazebo (Harmonic if you're on ROS 2 Jazzy, Fortress if
you're on Humble).** It's free, ROS 2-native, and almost every
tutorial assumes it. You can always switch later — the URDF you build
in [01-b](01-b-build-the-virtual-cell.md) is portable.

## How to confirm it's actually working

A "yes it installed" check is **not** a "yes it works" check. After
install, verify:

1. The simulator window opens.
2. A default scene loads (an empty world, a hello-world robot).
3. Physics ticks — a dropped cube falls, an arm settles under
   gravity.
4. The ROS 2 bridge (if applicable) publishes the topics you'd
   expect — clock, transforms, joint states.
5. The visualiser (RViz 2 on ROS 2; the simulator's own viewer
   otherwise) can connect.

If any step fails, fix it now. Every later step assumes a working
simulator.

## Output of this step

```
Simulator chosen:        Gazebo / Isaac Sim / MuJoCo / PyBullet / Webots / CoppeliaSim / Drake / Genesis / other
Version:                 ___
Installed via:           OS package / Docker / pip / vendor launcher / source build
GPU required?:           yes / no — model: ___
ROS 2 bridge needed?:    yes / no — which: ___
Empty world launches?:   yes / no
Physics ticks?:          yes / no
ROS 2 topics visible?:   yes / no
Visualiser can connect?: yes / no
```

## Common mistakes

1. **Installing two simulators "to compare" before either works.**
   You end up debugging both. Get one fully running first.
2. **ROS 2 distro / simulator version mismatch.** Gazebo Harmonic
   pairs with ROS 2 Jazzy; Fortress with Humble. Mixing them is a
   rabbit hole.
3. **Trying Isaac Sim on a GPU that's too small.** The launcher
   appears to load, then crashes on the first scene. Check VRAM
   (16 GB+ comfortable for serious work).
4. **Skipping the "physics ticks" check.** A simulator window
   opening doesn't prove physics works. Drop a cube.
5. **Running the simulator inside a VM or WSL.** GPU passthrough is
   fiddly. Use bare metal for the simulator host if at all possible.

## What's next

The simulator runs. Now you put the *actual arm* and the *actual
scene* inside it.

→ Next: [01-b-build-the-virtual-cell.md](01-b-build-the-virtual-cell.md)
