# 01 — Custom Gazebo world (autosampler cell)

A minimal Gazebo world for the HPLC autosampler tray-loading cell.
Implements checklist item **A.1** (autosampler tie-in) from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Dimensions follow
[`../../docs/hplc-autosamplers/requirements/`](../../docs/hplc-autosamplers/requirements/).

## What's in the scene

- **Bench** (600 × 400 × 50 mm) — the table the cell sits on.
- **myCobot 280 Pi** at the back-centre of the bench, mounted on the
  bench top.
- **Source rack** (90 × 180 × 50 mm) at the front-left — a stand-in for
  the MicroSolv 5 × 10 rack from
  [`requirements/01-task-and-objects.md`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md).
- **Destination tray on alignment plate** at the front-right — a
  stand-in for the Agilent 100-position 10 × 10 classic tray.
- **Three 12 × 32 mm vials** in the back row of the rack with red,
  blue, and green PP caps — enough to verify pick poses against later
  exercises.

All peripherals fit inside the 40 × 40 cm cell centred on the arm,
matching [`requirements/04-workspace-and-reach.md`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md).

## Run it

```bash
# Point Gazebo at the upstream myCobot model.
export GAZEBO_MODEL_PATH=~/ros2_ws/src/mycobot_ros2/mycobot_description/models:$GAZEBO_MODEL_PATH
# Or for Gazebo Sim Garden+:
# export GZ_SIM_RESOURCE_PATH=~/ros2_ws/src/mycobot_ros2/mycobot_description/models:$GZ_SIM_RESOURCE_PATH

gazebo exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf
# Or: gz sim exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf
```

You should see the bench, the arm in its zero pose, the white rack
with three capped vials on the back row, and the dark tray on its
alignment plate. Dragging a vial with the mouse should move it; the
rack, tray, and bench should stay put.

That's the "Done when" check.

## What's next

Exercise [`02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/)
uses this layout to confirm every rack and tray slot is inside the
myCobot's reach.
