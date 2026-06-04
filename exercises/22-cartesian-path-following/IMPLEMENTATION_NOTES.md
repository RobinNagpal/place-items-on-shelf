# Implementation notes — 22 Straight-line Cartesian path

## Why we use the MoveIt 2 Jazzy signature (no `jump_threshold`)

The `computeCartesianPath` API took five arguments through ROS 2
Humble and Iron:

```cpp
double computeCartesianPath(waypoints, eef_step,
                            double jump_threshold,           // <-- this
                            trajectory, avoid_collisions);
```

`jump_threshold` was used to abort the path if two consecutive IK
solutions differed in joint space by more than a threshold (a
heuristic for "the IK solver switched solution branches mid-line").

In Jazzy and Rolling the `jump_threshold` parameter is **deprecated
and ignored** — a 4-arg signature is the canonical one:

```cpp
double computeCartesianPath(waypoints, eef_step,
                            trajectory, avoid_collisions = true);
```

Upstream `automaticaddison/mycobot_ros2` targets Jazzy
([their README shield](https://github.com/automaticaddison/mycobot_ros2/blob/main/README.md))
so we use the new signature directly. If you compile against Humble
or Iron, swap to the 5-arg version and pass any positive number
(e.g. `0.0`) for `jump_threshold`.

## Why `eef_step = 0.005` (5 mm)

`eef_step` is the spacing between consecutive IK calls along the
Cartesian line. Smaller step = smoother trajectory but more IK
work; larger step = coarser path but cheaper to compute.

For a 5 cm descent, 5 mm gives 10 IK calls — fine on any modern CPU.
1 mm would also work; 10 mm is the upper end of what still produces
a visually-straight trace. MoveIt 2 tutorials usually default to
0.01 m (1 cm) — we pick 0.005 m so the trajectory is visibly smooth
in RViz's planned-path display.

## Why we wrap `computeCartesianPath` in a fraction check

The function returns `0.0 <= fraction <= 1.0`. Less than 1.0 means
the planner had to stop early. Causes:

- An IK call mid-line failed (the requested intermediate pose is
  unreachable).
- An intermediate pose collided with the planning scene (only checked
  when `avoid_collisions = true`).
- Two consecutive IK solutions came from different solution
  branches, producing a discontinuous joint jump. (In Humble / Iron
  this would be caught explicitly via `jump_threshold`; in Jazzy
  the planner skips the comparison and may simply return a smaller
  fraction.)

If we execute a trajectory with `fraction < 1.0`, the arm moves part
of the way and stops — the gripper does **not** reach the goal. So
we check `fraction >= 0.99` and only call `execute` in that case.
0.99 (not 1.00) gives a tiny margin for floating-point round-off in
the fraction calculation; in practice the function returns exactly
1.0 when the full line is achievable.

## Why we use `setPoseTarget` (exercise 19) to reach the hover pose

`computeCartesianPath` needs a current EE pose to start from. We
have to get the arm into the start of the line *somehow*. Two
options:

1. `setNamedTarget` — if a convenient named state lined up with our
   intended hover. None does, so we'd have to invent one.
2. `setPoseTarget` — the exercise-19 approach. Hand over the hover
   pose; let MoveIt plan a joint-space path to it.

Option 2 wins because the hover pose is arbitrary and lives only in
this exercise. The Cartesian-vs-joint-space distinction matters
**after** we're at the hover, not on the way to it.

This is also the standard production pattern: use joint-space to
*get to* the start of a controlled segment, then Cartesian for the
controlled segment itself.

## Why the descend / lift line is in `(0.180, +0.100, *)` and not over an actual vial

`computeCartesianPath` needs IK to succeed at every 5 mm step. At
the corners of the workspace (where the actual vials in the SDF
sit), KDL has a small chance of failing at some intermediate pose
even when both endpoints are reachable — and the function reports
`fraction < 1.0` instead of completing.

`(0.180, +0.100, *)` sits 20 cm from the arm base, well inside the
reach envelope and away from any singular wrist configuration. The
demo's purpose is to make the *technique* land cleanly. Mapping the
technique onto the real rack geometry comes later (it's a small
fix once perception is in play).

## Why we keep the same collision objects from exercises 20 / 21

`avoid_collisions = true` makes the function check each intermediate
pose against the planning scene. If the bench / rack / housing wall
weren't in the scene, the function would happily produce a path that
clips them (just like a joint-space plan without collision objects
would). Keeping the same four boxes guarantees parity with the
earlier exercises.

## Failure modes

- **`fraction = 0.0` on the descend step** — the start pose isn't
  where we think it is. Check that Step 1 (`go_pose(hover)`) really
  finished. Common cause: the `setPoseTarget` plan in Step 1
  succeeded but `execute` returned before the controller fully
  settled. Add a 500 ms sleep after Step 1.
- **`fraction = 0.4` or some other partial value** — one of the
  intermediate IK calls failed. Move the line by a centimeter or
  two (e.g. change `+0.100` to `+0.090`) and retry. If the failure
  is consistent at a specific z, KDL is hitting a near-singular
  configuration there; swapping to TRAC-IK in `kinematics.yaml`
  usually fixes it.
- **`fraction = 1.0` but the arm visibly jerks during execution** —
  the trajectory contains a discontinuity. In Jazzy this can happen
  if KDL returned different solution branches at adjacent steps;
  use `time_parameterization` or switch to TRAC-IK to smooth it.
- **`fraction = 1.0`, execution returns success, but the EE didn't
  actually reach the goal** — the joint trajectory controller is
  under-tuned. Same fix as exercise 19 (tune PID gains in
  `mycobot_gazebo/config/controllers.yaml`).

## What this exercise intentionally does NOT do

- No gripper open / close (exercise 17 / 21).
- No multi-waypoint Cartesian path. The API accepts a list of
  waypoints (each segment is a straight line between consecutive
  waypoints); we use a single waypoint per call to keep the demo
  focused on the "one straight line" behaviour. Multi-waypoint use
  is a one-line change.
- No `path_constraints` argument. The overload that takes path
  constraints (e.g. "keep the wrist orientation locked while moving
  in XY") is useful for pouring, but adds a layer that isn't needed
  to demonstrate the technique.
- No timestep parameterization tweaking. Default
  `time_parameterization` gives a reasonable execution speed for
  the 5 cm segments shipped here.
