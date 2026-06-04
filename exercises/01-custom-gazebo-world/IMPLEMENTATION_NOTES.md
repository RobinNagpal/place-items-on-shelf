# Implementation notes — 01 Custom Gazebo world

## Why SDF and not URDF

URDF describes a *robot*. SDF describes a *world*, including robots in
that world. We need a world with a table, a floor, a sun, three cubes,
and the arm — SDF is the right tool. URDF cannot express the floor or
the cubes at all.

The arm is included from its own URDF inside the upstream Gazebo model
package, which is what `<include><uri>model://mycobot_280</uri></include>`
resolves to under the hood.

## Why SDF 1.7 (not the very latest)

SDF 1.7 is the most recent version that **both** Gazebo Classic 11 and
Gazebo Sim Garden+ load without warnings. Going higher (1.9, 1.10) breaks
Classic. Going lower (1.6) gets you a deprecation warning on Garden+.
1.7 is the sweet spot until Classic is retired.

## Why the table is defined inline, but the arm is included

The arm is a complex model with meshes, inertias, transmissions, joint
limits, and a control plugin. Inlining it would mean copying ~2000 lines
of XML and bit-rotting it forever. `<include>` lets us track the upstream
copy.

The table is the opposite: a single static box. Writing it out inline (5
lines of geometry) is shorter than fetching it from a model database and
removes one dependency.

The cubes follow the same rule as the table: dead simple boxes, no point
referencing an external model.

## Why three cubes and not, say, two or five

The checklist explicitly says "3 coloured cubes". Three is also the
smallest count that lets later exercises practise:

- detecting *which* of several objects to pick (item 25, LLM router),
- counting / matching against a target (items 4 and 5, YOLO).

Two would not exercise selection logic. Five would clutter the scene at
this stage.

## Why the cubes are 40 mm and the table top is at 0.75 m

- **40 mm cube** — the myCobot 280's parallel-jaw gripper opens to about
  60 mm. A 40 mm cube fits comfortably with margin on both sides.
- **0.75 m table** — a typical bench height. Combined with the arm's
  ~280 mm reach, every cube position used in this scene is reachable.
  Going taller would push the cubes near or past the arm's reach.

These numbers come from the myCobot 280 spec sheet and the
`docs/02-hardware-selection/` notes. They are not arbitrary, but they are
also not contractual — bumping the table height by 5 cm has no effect on
this exercise.

## Why the cubes are dynamic and the table is static

`<static>true</static>` removes the model from physics. Static models are
faster (no integrator updates) and cannot tip over.

- The **table** is static. We do not want a 0.75 m bench wobbling under
  gravity, and we do not want to push it around accidentally.
- The **cubes** are dynamic. The checklist's "Done when" check is "you
  can drag them with the mouse" — that requires physics to be active for
  the cube.

## Why the arm pose is `(-0.30, 0, 0.775)`

- `x = -0.30 m` puts the arm at the back edge of an 0.80 m wide table
  (table edge is at x = -0.40 m; the arm base is 10 cm in from that
  edge). This leaves the front 50 cm of the table for cubes and for the
  arm to reach.
- `y = 0` centres the arm side-to-side.
- `z = 0.775 m` = table-pose-z (0.75) + half-thickness (0.025). The base
  of the arm rests on the top surface.
- `roll = pitch = yaw = 0` means the arm's base x-axis points forward,
  which matches the convention in
  [`../02-read-and-annotate-urdf/`](../02-read-and-annotate-urdf/).

## Trade-off: GAZEBO_MODEL_PATH dependency

The cleanest alternative would be to ship a copy of the myCobot 280
Gazebo model inside this folder, so that the SDF loads with no extra env
vars. We did not do that for three reasons:

1. The upstream model is several MB of meshes and is updated regularly.
2. Vendoring it would create a silent drift problem the first time
   upstream fixes a joint limit or a mesh.
3. The rest of the project already assumes the user has cloned
   `automaticaddison/mycobot_ros2` (see the main `README.md` and the
   `cobot280_moveit_task` README).

The cost: the user must set one env var before launching. That cost is
documented in this folder's README.

## Failure cases

- **"Model `mycobot_280` not found"** — your model path is wrong. Echo
  it: `echo $GAZEBO_MODEL_PATH` (or `$GZ_SIM_RESOURCE_PATH`). Make sure
  the directory `mycobot_280/` (with a `model.config` file inside) is
  directly on the path.
- **Cubes fall through the table** — physics is OK but collision is off.
  Check that `<collision>` blocks are present and have the same size as
  the visuals. The bundled SDF has these correct; this only happens if
  you delete a `<collision>` while editing.
- **Arm sinks into the table on spawn** — `pose z` is too low. The base
  link must spawn above the table's top surface; we use `z = 0.775 m`
  for that reason.
- **Black scene on launch** — no light. Check that the `model://sun`
  include is present and that Gazebo's model database is reachable
  (Classic needs internet on first run to fetch built-in models, then
  they are cached).

## Debugging tips

- Open the SDF in any text editor and check it against the SDF schema:
  `gz sdf -k worlds/pick_place_world.sdf` (Garden+) or
  `gz sdf -p worlds/pick_place_world.sdf` (some older builds) — these
  print the parsed tree and flag errors with a file/line.
- To verify the cubes are dynamic, drop the simulation rate to 0.1 (top
  bar in Classic, GUI panel in Sim) and watch them. A static cube will
  not move at all; a dynamic one will settle on the table.
- If the arm includes but does not move, that is correct here. Motion
  needs MoveIt and ros2_control, neither of which this exercise wires up
  — those live in later exercises (18–21).

## Things this exercise intentionally does *not* do

- No ROS topics, no controllers, no MoveIt — those are items 18–21.
- No camera in the world — that is item 4.
- No collision objects for MoveIt's planning scene — that is item 20.
- No autosampler-specific geometry (rack, tray, vials) — the checklist's
  autosampler tie-in for this item replaces the cubes with vials, but
  that is its own exercise and would obscure the basic-world goal.
