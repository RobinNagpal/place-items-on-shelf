# 01-b — Build the Virtual Cell

You have a simulator running. Now you put **your robot, your table,
and a few objects** inside it. The goal is to create a virtual
version of the workspace your real cell will eventually have.

You do this once. After this step, everything you build runs against
this scene — motion planning, perception, the task code, and (later)
the policy you might train.

## What you need before this step

- A working simulator from
  [step 1](01-choose-and-install-simulator.md).
- A description of your arm in a format the simulator can read —
  usually **URDF** (ROS 2 ecosystem), **MJCF** (MuJoCo), or **USD**
  (Isaac Sim). Most arm vendors ship at least a URDF.
- A rough idea of:
  - **Where the arm mounts** — table corner? Centred? Hanging?
  - **The table dimensions.**
  - **The objects you'll pick** — even a placeholder cube is fine.
  - **Where the camera sits** — overhead? Wrist-mounted? Both?

## What "the virtual cell" actually contains

A minimum useful cell has six things:

1. **Ground / world frame.** A reference origin.
2. **A table mesh** at the real height and footprint.
3. **The arm**, mounted to the table at the real location.
4. **At least one object** to pick (a cube, a cylinder, a cup mesh).
5. **A camera**, mounted where the real camera will be.
6. **A bin / drop zone** if your task has one.

That's it. Resist adding a fancy environment now — every prop is one
more thing to debug.

## The decisions you make in this step

### The arm

- Source the description from the vendor's package, the
  manufacturer's CAD, or a community repo. Confirm it parses cleanly
  before going further.
- Decide whether you'll keep the description as-is or parameterise
  it (xacro on ROS 2 is the usual choice) for different gripper
  variants.

### The table

- A box at real height and footprint. Set realistic mass and
  friction — defaults that work for grasping start around
  `mu = 0.5–1.0`.
- Place the arm's base at the corner / centre / wherever the real
  mount will be. Get this right *now*; a wrong mount pose makes
  every later pose wrong.

### The objects

- Start with **primitives** (boxes, cylinders). Use realistic mass
  and friction (a steel cube ≈ 2.7 g/cm³; an empty plastic cup
  ≈ 30 g).
- Swap to mesh imports later, only if shape matters for grasping.

### The camera

- Match the **real** camera's resolution (e.g. 1280×720 RGB) and
  field of view (~60–90° for a typical RealSense / Kinect).
- Mount it at the planned real-world pose. If the real camera is
  depth, add the depth sensor variant.

### The transform tree

The simulator publishes a tree of frames: `world → base_link →
link_1 → … → tool0` for the arm, and a separate frame for the
camera. **Every later step assumes this tree is correct.**

When you open the visualiser:

- The chain should be intact end-to-end.
- The camera frame should sit at the planned pose.
- The arm should stand upright — not exploded, not sunk through the
  table.

If the tree is broken, fix it before going further.

## How long this should take

For a vendor-supported arm in the default simulator: **half a day
the first time.** It shortens fast once you have a template scene.
Don't get sucked into making the scene pretty.

## Assets and tools that save time

- **Asset libraries** — **Gazebo Fuel** (`fuel.gazebosim.org`),
  **NVIDIA Omniverse assets**, **MuJoCo Menagerie**. Don't model a
  coffee cup from scratch.
- **xacro** (ROS 2) — parameterises the URDF; one file, many gripper
  variants.
- **MoveIt Setup Assistant** — generates the SRDF you'll need in
  [step 3](03-bring-up-moveit-in-sim.md), if you're using MoveIt.
- **Blender → mesh export** — for custom object meshes; export to
  Collada (`.dae`) or USD.

## Output of this step

```
Arm description format:   URDF / MJCF / USD (source: ___)
Table dims (m):           ___ × ___ × ___
Arm mount point:          corner / centre / edge (offset: ___ )
Objects in scene:         cube / cylinder / vendor mesh (list: ___ )
Camera type:              RGB / RGB-D / stereo (model: ___ )
Camera mount:             overhead at (x, y, z) / wrist-mounted
Transform tree intact?:   yes / no — broken at: ___
Scene file:               ___
Simulator version pinned: ___
```

## Common mistakes

1. **Wrong arm mounting pose.** A 90° rotation later means nothing
   reaches anywhere. Match the real plan now.
2. **Massless objects.** Default mass = 0 turns objects into
   collision-less ghosts. Always set realistic mass and inertia.
3. **No friction.** Defaults are often too low for grasping. Tune
   roughly to `0.5–1.0` for graspable objects.
4. **Cluttered scene from day one.** Build the minimum: table, arm,
   one object, one camera. Add clutter only when the basics work.
5. **Camera resolution that doesn't match real.** When the real
   camera arrives at 1280×720, your sim-trained code expects
   640×480. Match early.
6. **Skipping the transform-tree check.** Fix tree problems while
   they're small.

## What's next

The cell exists in sim. Now you give the arm a *brain* — a motion
planner.

→ Next: [03-bring-up-moveit-in-sim.md](03-bring-up-moveit-in-sim.md)
