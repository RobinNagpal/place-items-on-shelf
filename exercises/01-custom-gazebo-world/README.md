# 01 — Create a custom Gazebo world

A minimal Gazebo simulation scene with a table, the myCobot 280 arm, and
three coloured cubes on the table top. Implements checklist item **A.1**
from [`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What this is

A single SDF file ([`worlds/pick_place_world.sdf`](worlds/pick_place_world.sdf))
that describes a virtual world. Gazebo loads the file and renders a 3D
scene you can fly around in and interact with.

## Main workflow

1. You launch Gazebo and point it at the SDF file.
2. Gazebo reads the SDF, downloads any referenced models (sun,
   ground_plane, mycobot_280), and renders the scene.
3. You see the table, the arm in its home pose, and three cubes.
4. You drag any cube with the mouse — it moves and reacts to gravity.

That's the whole exercise. No code runs. Everything is declarative.

## Core concepts

- **SDF (Simulation Description Format)** — an XML format that describes
  a world: lights, ground, objects (called *models*), their shapes,
  colours, masses, and starting positions.
- **Model** — one object in the world. A model has one or more *links*
  (rigid bodies) glued together by *joints*. A cube is a model with one
  link. A robot arm is a model with many links and joints.
- **Static vs dynamic model** — `<static>true</static>` means physics
  ignores the model (it cannot move, cannot be pushed). The table is
  static. The cubes are not — they fall under gravity and you can drag
  them.
- **`<include>`** — load a model from a model database instead of writing
  it out inline. We use this for the sun, the ground plane, and the
  myCobot arm.
- **Pose** — six numbers: x y z roll pitch yaw. Units are metres and
  radians. The world origin is at `(0, 0, 0)`; +Z is up.

## Libraries / frameworks used

- **Gazebo** — the simulator. Two flavours work with this file:
  - **Gazebo Classic 11** (`gazebo` command) — older but most ROS 2
    tutorials still use it.
  - **Gazebo Sim / Ignition Gazebo Garden+** (`gz sim` command) — the
    new line. Same SDF, different launch command.
- **myCobot 280 Gazebo model** — comes from the upstream
  [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2)
  repo. We do *not* duplicate it here; we reference it by URI.

## Data flow

```
       pick_place_world.sdf
                |
                v
   +------------+------------+
   |   Gazebo (gazebo / gz)   |   <-- parses SDF, builds scene
   +------------+------------+
                |
                v
   +-------------------------+
   |   3D GUI window         |
   |   - table               |
   |   - myCobot 280 arm     |
   |   - 3 cubes (draggable) |
   +-------------------------+
```

## Inputs

- The SDF file itself.
- The Gazebo model database (for `sun`, `ground_plane`).
- The `mycobot_280` Gazebo model on your model path.

## Outputs

- A live Gazebo window. No files are written. Nothing is published on a
  ROS topic — perception and motion live in later exercises.

## Example execution

```bash
# Step 1: Make sure the myCobot model is on Gazebo's search path.
# Adjust the path to wherever you cloned automaticaddison/mycobot_ros2.
export GAZEBO_MODEL_PATH=~/ros2_ws/src/mycobot_ros2/mycobot_description/models:$GAZEBO_MODEL_PATH
# For Gazebo Sim Garden+ use this instead:
# export GZ_SIM_RESOURCE_PATH=~/ros2_ws/src/mycobot_ros2/mycobot_description/models:$GZ_SIM_RESOURCE_PATH

# Step 2: Launch Gazebo on the world.
gazebo exercises/01-custom-gazebo-world/worlds/pick_place_world.sdf
# Or on Garden+:
# gz sim exercises/01-custom-gazebo-world/worlds/pick_place_world.sdf
```

When the window opens you should see:

- A flat grey ground.
- A brown table at hip height.
- The myCobot 280 mounted at the back edge of the table, in its zero
  (home) pose.
- A red, a green, and a blue cube on the table top.

Click and drag any cube with the mouse. It should slide on the table and
fall off the edge if you push it too far. That's the **Done when** check
from the checklist.

## What's next

Once this world opens, you have a scene every later exercise can re-use:
[`02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/) studies the
arm that appears in this world.
