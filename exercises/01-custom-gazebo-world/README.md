# 01 — Custom Gazebo world (autosampler cell)

A minimal Gazebo world for the HPLC autosampler tray-loading cell.
Implements checklist item **A.1** (autosampler tie-in) from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).
Dimensions follow
[`../../docs/hplc-autosamplers/requirements/`](../../docs/hplc-autosamplers/requirements/).

## What an `.sdf` file is

SDF stands for **Simulation Description Format**. It is an XML file
that tells the **Gazebo** simulator what to put in the scene and
where: lights, the floor, a table, a robot, objects. Gazebo reads the
file and renders the 3D world from it.

You do not run the file directly. You hand it to Gazebo:

```bash
gazebo path/to/world.sdf       # Gazebo Classic
gz sim path/to/world.sdf       # Gazebo Sim Garden+ / Ignition
```

Everything in this exercise lives in one file:
[`worlds/autosampler_cell.sdf`](worlds/autosampler_cell.sdf).

## What's in the scene

- **Bench** (600 × 400 × 50 mm) — the table the cell sits on.
- **myCobot 280 Pi** at the back-centre of the bench. The arm is
  *included* from the upstream URDF (see "How the arm is loaded"
  below) — we do not redefine it here.
- **Source rack** (90 × 180 × 50 mm) at the front-left — a stand-in
  for the MicroSolv 5 × 10 rack from
  [`requirements/01-task-and-objects.md`](../../docs/hplc-autosamplers/requirements/01-task-and-objects.md).
- **Destination tray on alignment plate** at the front-right — a
  stand-in for the Agilent 100-position 10 × 10 classic tray.
- **Three 12 × 32 mm vials** in the back row of the rack, with **red,
  blue, and green** PP caps.

All peripherals fit inside the 40 × 40 cm cell centred on the arm,
matching [`requirements/04-workspace-and-reach.md`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md).

## The main SDF tags you'll see in the file

| Tag | What it does |
|---|---|
| `<sdf version="1.7">` | wraps the whole document; declares the SDF version |
| `<world>` | top-level container — every object lives inside it. One `<world>` per file |
| `<include><uri>model://...</uri></include>` | load a pre-built model from a model database (e.g. `model://sun` pulls in Gazebo's built-in sun) |
| `<model>` | one object in the world (the bench, the rack, a vial, the arm). A model contains one or more links |
| `<static>` | if `true`, physics ignores the model — it cannot fall or be pushed. The bench and rack are static; vials are not |
| `<pose>` | six numbers `x y z roll pitch yaw`, in metres and radians. Position + orientation in the world |
| `<link>` | one rigid body inside a model. A vial = 1 link. The arm = many links connected by joints |
| `<visual>` | what the GUI draws for a link — its shape and colour |
| `<collision>` | the shape physics uses for contacts (can be a simpler version of the visual mesh) |
| `<geometry>` | the actual shape: `<box>`, `<cylinder>`, `<sphere>`, or `<mesh>` |
| `<material>` | the surface colours: `<ambient>` (base colour under shade) and `<diffuse>` (the main visible colour) |
| `<inertial>` | mass + inertia tensor. Required on any link that physics has to move |

A `<material>` colour is **four numbers**: `red green blue alpha`,
each 0..1. So `0.8 0.1 0.1 1` means "mostly red, a little green, a
little blue, fully opaque".

## How the three vials get different colours

Each vial is its own `<model>` with one `<link>`. Inside that link
there are **two `<visual>` blocks** — one for the glass body, one
for the cap — each with its own `<material>`.

The glass body uses the same pale-blue translucent material in every
vial:

```xml
<visual name="body">
  <pose>0 0 -0.002 0 0 0</pose>
  <geometry><cylinder><radius>0.006</radius><length>0.028</length></cylinder></geometry>
  <material>
    <ambient>0.85 0.9 0.9 0.8</ambient>
    <diffuse>0.85 0.9 0.9 0.8</diffuse>
  </material>
</visual>
```

Only the cap material changes between vials. For the red-cap vial
(`vial_a1`):

```xml
<visual name="cap">
  <pose>0 0 0.014 0 0 0</pose>
  <geometry><cylinder><radius>0.0045</radius><length>0.008</length></cylinder></geometry>
  <material>
    <ambient>0.8 0.1 0.1 1</ambient>     <!-- red -->
    <diffuse>0.8 0.1 0.1 1</diffuse>
  </material>
</visual>
```

For the blue-cap vial (`vial_a3`) the cap colour becomes
`0.1 0.5 0.9 1`. For the green-cap vial (`vial_a5`) it becomes
`0.1 0.7 0.2 1`. Everything else about the three models is identical;
only those two RGBA quadruples change.

This matches the lab convention from
[`requirements/02-environment.md`](../../docs/hplc-autosamplers/requirements/02-environment.md):
cap colour codes sample type (e.g. blue = standard, red = unknown,
green = QC), so later perception exercises can filter by cap colour.

## How the arm is loaded

We do **not** copy the arm's geometry into this file. Instead the
file has one line:

```xml
<include>
  <name>mycobot_280</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.18 0 0.775 0 0 0</pose>
</include>
```

Gazebo resolves `model://mycobot_280` against your
`GAZEBO_MODEL_PATH` (Classic) or `GZ_SIM_RESOURCE_PATH` (Garden+) and
loads the model from there.

The actual arm definition lives upstream at
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2),
across two `.urdf.xacro` files. See
**[`robot-arm-urdf-primer.md`](robot-arm-urdf-primer.md)** in this
folder — it explains what the `.urdf.xacro` extension means and walks
through both files (the top-level composer and the arm definition)
section by section. Exercise [`../02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/)
then pulls every link, joint, axis, and limit out of those files into
one table.

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

Exercise [`../02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/)
uses this layout to confirm every rack and tray slot is inside the
myCobot's reach — and to map every link name in the URDF to a real
physical part.
