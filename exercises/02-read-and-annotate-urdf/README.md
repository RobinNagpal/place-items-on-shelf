# 02 — Read and annotate the arm's URDF (autosampler reach check)

Read the myCobot 280's URDF, label every link and joint, and confirm
the arm can reach every slot in the autosampler cell from
[`../01-custom-gazebo-world/`](../01-custom-gazebo-world/).
Implements checklist item **A.2** (autosampler tie-in) from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

No code. The deliverable is [`annotation.md`](annotation.md).

## What's inside the annotation

- **Kinematic tree** — six revolute joints, what each one does.
- **Joint table** — axis, lower / upper limits in radians and degrees.
- **Link table** — which physical part each `<link>` represents.
- **Reach check** — arithmetic that takes the SDF poses of the rack
  and tray and compares the far-corner distance to the arm's 280 mm
  reach. Surfaces whether the v1 layout fits before any code is
  written.

## How to use it

1. Read the joint / link tables before writing any motion code — they
   tell you which joint to touch for a given motion.
2. Re-run the reach arithmetic any time you move a peripheral in
   `autosampler_cell.sdf` — the formula is `sqrt(Δx² + Δy²)` from the
   arm base to the far corner, must be ≤ 0.280 m.

You are **done** when you can open RViz on the URDF, click any frame
in `RobotModel`, and name the corresponding link and joint without
looking it up.

## Inputs

- `mycobot_280.urdf.xacro` from
  [`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2).
- The SDF poses in
  [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).
- The cell layout in
  [`../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md).

## Outputs

One file: [`annotation.md`](annotation.md). No code.
