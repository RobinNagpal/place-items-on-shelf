# Implementation notes — 18 Joint-space hello world

## Why reuse `ready` instead of defining a new "park" pose

The SRDF `ready` pose already folds the elbow and wrist up so the
gripper sits above and in front of the shoulder. That happens to be
exactly what we want for the autosampler park-between-trays role
(see [`../02-read-and-annotate-urdf/annotation.md`](../02-read-and-annotate-urdf/annotation.md)
for why this clears the rack at `y = +0.12` and the tray at
`y = -0.12`).

Defining a new named state would mean editing the upstream SRDF
(which we cannot do without forking) or shipping a duplicate SRDF in
this exercise. Reusing `ready` is shorter and keeps us aligned with
upstream.

If a future exercise needs a *different* park pose, drop
`setNamedTarget("ready")` and call `setJointValueTarget({...})` with
the joint values inline — no SRDF edits required.

## Why the launch file does NOT pass `robot_description`

`robot_description` is the URDF as a string. It is already published
as a parameter by `robot_state_publisher` inside the `mycobot_gazebo`
launch (Terminal A). If our launch passed it again we would have two
URDF publishers competing, and RViz / move_group would warn about it.

So the launch comment notes: "URDF is pulled from the running
robot_state_publisher's /robot_description topic, so we do NOT pass
moveit_config.robot_description here."

We *do* pass `robot_description_semantic` (the SRDF) and the YAML
configs, because those are not published by anything else in the
running stack.

## Why the 2-second sleep before the first plan call

`MoveGroupInterface` has to subscribe to several topics
(`/joint_states`, `/tf`, `/tf_static`) and connect to the MoveGroup
action server before it can plan. If we call `plan()` immediately
after construction, the first call sometimes fails with
"current state is not yet known".

Two seconds is a heuristic that works on a typical laptop. For a
slow machine bump to 5 s. The robust fix is an explicit "wait for
action server + first joint state" loop, but that is overkill for
a hello-world demo.

## Launch-flow gotcha: world arg support

`mycobot_gazebo.mycobot.gazebo.launch.py` historically takes a `world`
arg, but forks vary.

- **Fork accepts `world:=<path>`** — pass the absolute path to
  `autosampler_cell.sdf`. Everything works visually.
- **Fork ignores `world`** — Gazebo loads the upstream default world.
  The arm still moves correctly; the rack / tray / vials are just
  not visible. The exercise's "Done when" check still passes; the
  autosampler tie-in becomes a paper check (against the SDF) rather
  than a visual one.

If the world arg is not supported, the fallback is launching Gazebo
standalone on the SDF (`gz sim path/to/autosampler_cell.sdf`) and
then spawning the arm + controllers via the upstream spawner launch
files. This is more invasive and is intentionally out of scope for
this exercise.

## Failure modes

- **`MoveGroupInterface: No such group 'arm'`** — `move_group` is not
  running (Terminal B is missing) or the SRDF was not loaded. Check
  `ros2 node list | grep move_group`.
- **`Planning to 'home' failed`** — current joint state is outside
  the planner's assumptions. Re-launch Gazebo so the arm spawns at
  zero, or relax `setPlanningTime(2.0)` to 5 s.
- **Plan succeeds in RViz but arm does not move in Gazebo** — the
  joint trajectory controller is not active. Check
  `ros2 control list_controllers`; `arm_controller` should be
  `active`.
- **First plan call fails right after start-up** — the 2-second
  sleep is too short on a slow machine. Bump it to 5 s.

## What this exercise intentionally does NOT do

- No collision objects in the planning scene (that is exercise 20).
- No IK / Cartesian pose goals (that is exercise 19).
- No gripper open / close (that is exercise 17).
- No redeclaration of the world; the autosampler scene stays in
  [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).
