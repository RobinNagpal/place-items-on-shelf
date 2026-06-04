# 02 — Read and annotate the arm's URDF

Read the myCobot 280's URDF, draw the kinematic tree, and label every
link and joint in plain English. Implements checklist item **A.2** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

There is **no code** in this exercise. The deliverable is a single
annotation document.

## What this is

A reference document, [`annotation.md`](annotation.md), that turns the
machine-readable URDF into a human-readable map:

- which `<link>` is which physical part of the arm,
- which `<joint>` rotates around which axis,
- what the lower / upper / velocity limits of each joint are,
- where the home and ready poses send each joint.

## Main workflow

1. Open the upstream URDF on your disk
   (`~/ros2_ws/src/mycobot_ros2/mycobot_description/urdf/mycobot_280.urdf.xacro`).
2. Trace the parent-child chain from `base_link` to the gripper flange.
3. For each link, identify the physical part it represents.
4. For each joint, copy out the axis and the limit values.
5. Write everything down in one place — that's [`annotation.md`](annotation.md).

The exercise is about **building the mental map**, not about producing
the document. The document is just where you record what you found so
the rest of the project can refer to it.

## Core concepts

- **URDF (Unified Robot Description Format)** — an XML file that
  describes a robot as a tree of rigid bodies (`<link>`) connected by
  joints (`<joint>`). MoveIt, RViz, Gazebo, and ros2_control all parse
  the same URDF.
- **Kinematic tree** — the parent-child graph of links and joints. The
  root is usually `base_link` (or `world`). Each joint has exactly one
  parent link and one child link, so the graph is a *tree*, not a
  general graph.
- **Joint types** — `revolute` (hinge with limits), `continuous` (hinge
  with no limits), `prismatic` (sliding), `fixed` (no motion),
  `floating`, `planar`. The myCobot 280 arm uses only `revolute` for
  its six joints.
- **Joint axis** — a unit vector `xyz` in the *parent link's* frame
  saying which way the joint rotates. `0 0 1` = Z, `0 1 0` = Y,
  `1 0 0` = X.
- **Joint limits** — `lower` and `upper` in radians, `velocity` in
  rad/s, `effort` in newton-metres. MoveIt's planner refuses any joint
  goal outside these limits, so getting them right early saves a lot of
  debugging later.
- **End-effector frame (TCP)** — a fixed-offset frame at the actual
  contact point of the gripper. MoveIt plans against this frame, not
  against the `link6` flange.

## Libraries / frameworks used

None. This exercise is read-only.

The tools you use for reading are:

- a plain text editor (the URDF is XML),
- optionally `urdf_to_graphiz` for a visual tree,
- optionally RViz with a `RobotModel` display for a 3D view of the same
  tree.

## Data flow

```
   mycobot_280.urdf.xacro        (machine-readable, ~hundreds of lines)
              |
              | you read it
              v
        your brain                (kinematic tree, link/joint identities)
              |
              | you write it down
              v
        annotation.md             (human-readable summary, this folder)
              |
              | read by you and future readers
              v
   every later exercise that touches a joint
```

## Inputs

- `mycobot_280.urdf.xacro` from
  [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2)
  (or your own cloned URDF if you forked the project).
- The matching SRDF
  (`mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf`) for the
  named poses (`home`, `ready`).

## Outputs

- One file: [`annotation.md`](annotation.md).
- No code, no compiled artefacts, no ROS topics.

## Example execution

There is nothing to execute. The "execution" is reading and writing:

```bash
# 1. Look at the URDF.
less ~/ros2_ws/src/mycobot_ros2/mycobot_description/urdf/mycobot_280.urdf.xacro

# 2. Render the tree (optional but useful).
cd /tmp
xacro ~/ros2_ws/src/mycobot_ros2/mycobot_description/urdf/mycobot_280.urdf.xacro > mycobot_280.urdf
urdf_to_graphiz mycobot_280.urdf
# This writes mycobot_280.pdf showing every link/joint.

# 3. Compare what you found against annotation.md in this folder.
```

You are **done** when you can open RViz, click any frame in the
`RobotModel` display, and say what link and joint it corresponds to
without looking it up. That's the "Done when" check from the checklist.

## What's next

The annotation feeds three later exercises:

- **18** (joint-space hello world) — uses the joint *names* and *limits*
  to set goals.
- **19** (Cartesian pose goal) — uses the end-effector frame as the
  pose target.
- **20** (collision avoidance) — relies on the link geometry to know
  which parts of the arm can hit the table.
