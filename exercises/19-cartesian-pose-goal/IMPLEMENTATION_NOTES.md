# Implementation notes — 19 Cartesian pose goal

## Why KDL for IK (and not TracIK or an analytical solver)

`kinematics.yaml` in upstream `mycobot_moveit_config` already wires
`kdl_kinematics_plugin/KDLKinematicsPlugin` to the `arm` group. We
inherit it. KDL is numerical (it iterates from a seed until the
position+orientation error is small), works on any chain MoveIt can
parse, and is good enough for the 6-DoF myCobot 280.

We do **not** swap to TracIK or write an analytical 6-DoF closed-form
solver:

- Analytical solvers for 6-DoF arms exist but they're per-arm and
  hard to maintain — KDL covers the demo with one config line.
- TracIK is faster on hard targets but requires installing
  `trac_ik_kinematics_plugin`. Out of scope for a hello-world.

If a future exercise needs faster, more reliable IK at the edge of
the reach envelope, replace the `kinematics_solver:` line in a copy
of `kinematics.yaml` and rebuild — no C++ changes here.

## Why the four targets sit at the corner of the rack / tray, not the centre

The myCobot 280 has a 280 mm reach. The rack and tray centres are at
arm-local distance ≈ 0.27 m — right at the edge, where KDL often
returns "no solution" or returns a solution that wraps a joint into a
near-limit pose. Picking the **corner nearest the arm** brings the
target down to ~0.20 m, comfortably inside the workspace.

This still demonstrates the autosampler workflow (hover, descend,
lift, cross-over). Exercise 20 — collision objects — will use full
rack / tray geometry; exercise 21 — pick-and-place — will deal with
unreachable wells by repositioning the arm base.

## Why roll = π (gripper down) and not a more natural orientation

For an autosampler the gripper must come **straight down** onto a
vial cap so the jaws straddle the cap, not graze it. Roll = π flips
`link6_flange`'s local +Z axis (which is "out of the tool") to
point along world −Z.

Pitch = 0, yaw = 0 means the gripper is oriented along the world
+X / +Y axes. The vials in the SDF are axis-aligned, so this lines
up the jaws with the grid by default. No yaw search needed.

## Why we set goal_position_tolerance to 1 mm but check 5 mm

`setGoalPositionTolerance(0.001)` is the **planner's slop**: it tells
OMPL "you can stop searching once the planned final state is within
1 mm of the IK answer". That's an internal margin.

The 5 mm tolerance in the "Done when" check is what we measure
**after** execute, in real (sim) space. The two are different: the
planner can promise 1 mm, but trajectory execution + controller
following error eats some of it.

If the post-execute error is consistently over 1 mm but under 5 mm,
that's normal joint-trajectory-controller settling. If it ever
exceeds 5 mm, the controller PID gains in `mycobot_gazebo` are too
loose; see that package's `controllers.yaml`.

## Why 5 planning attempts and 3-second planning time

IK + OMPL is non-deterministic. A single attempt at a hard pose
sometimes fails when a second attempt would succeed (different
random seed → different sample sequence). 5 attempts × 0.6 s each
fits inside `setPlanningTime(3.0)`.

For the four targets in this demo, the first attempt almost always
succeeds. The retries are a cheap insurance policy that matters more
in exercise 21 when there are dozens of consecutive pose goals.

## Why the orientation error uses |dot| and not the raw quaternion difference

Quaternions are double-cover: `q` and `−q` represent the same rotation.
`acos(dot(a, b))` would give π when the two rotations are actually
identical but expressed with opposite signs. `acos(|dot|)` collapses
the two halves of the cover and returns the real angle.

The factor `2.0 *` is because a quaternion's scalar part is
`cos(angle/2)`, so the dot product of two unit quaternions equals
`cos(half-angle-between-them)`.

## Failure modes

- **`Found a solution but it was outside of the joint limits`** —
  KDL found IK that wraps a joint past its limit. Usually fixed by
  bringing the target closer to the arm base (smaller x or |y|).
- **`No IK solution found`** — pose is genuinely outside the reach
  envelope, **or** the orientation conflicts with the chain geometry.
  Try `roll = π/2` first to see if it's an orientation problem.
- **Plan succeeds in RViz but the arm doesn't move in Gazebo** —
  same as exercise 18: `arm_controller` is not active. Check
  `ros2 control list_controllers`.
- **Post-execute pos_err > 5 mm** — joint trajectory controller
  isn't tracking tight enough. Increase the velocity/acceleration
  scaling factors slightly, or tune controller gains in
  `mycobot_gazebo/config/controllers.yaml`.
- **`Failed to fetch current state` on the first call** — same
  2-second start-up sleep heuristic as exercise 18. Bump to 5 s on
  slow machines.

## What this exercise intentionally does NOT do

- No gripper open / close (that is exercise 17).
- No collision objects in the planning scene (that is exercise 20).
- No full pick-and-place stringing the gripper, IK and collisions
  together (that is exercise 21).
- No straight-line Cartesian path (`computeCartesianPath`) — we use
  ordinary joint-space planning between Cartesian endpoints. A
  straight-line Cartesian descent is a separate technique and would
  belong in a follow-up exercise.
- No redeclaration of the world; the autosampler scene stays in
  [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).
