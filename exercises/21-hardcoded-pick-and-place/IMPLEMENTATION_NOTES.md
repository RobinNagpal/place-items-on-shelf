# Implementation notes — 21 Hardcoded pick-and-place

## Why the vial doesn't actually move with the gripper

The gripper joint opens and closes at the right moments in the
sequence, but in Gazebo the simulated vial stays where the SDF put
it — it does not stick to the gripper. The reason: a closed gripper
touching a vial does not, by itself, create a parent-child link in
the physics world. Three options to actually make the vial follow:

1. **`AttachedCollisionObject`** in MoveIt's planning scene.
   Tells the *planner* the vial is now part of the arm so it's
   collision-checked along with the arm. Does **not** glue the vial
   to the gripper in Gazebo physics — it's a planner-only concept.

2. **A Gazebo grasp plugin** (e.g. `gz::sim::systems::DetachableJoint`
   in modern Gazebo, or `gazebo_grasp_plugin` in classic Gazebo).
   Creates / removes a temporary fixed joint between the vial and
   the gripper when the gripper closes / opens. This is what makes
   the vial actually move with the arm in sim.

3. **A small script that manually teleports the vial** to follow the
   gripper while it is "closed". Hacky but works for sim demos.

Doing any of these properly is a separate exercise. The checklist
explicitly calls out item 21 as "hardcoded instructions only" — the
point is the sequence, not the grasping physics. We note the gap
here so a learner doesn't think the code is broken.

## Why `MoveGroupInterface("gripper")` and not direct controller calls

`MoveGroupInterface` gives us the same `setNamedTarget` /
`plan` / `execute` API for the gripper group that we use for the
arm group. It also lets the SRDF `<group_state>` names (`open`,
`closed`, `half_closed`) be the single source of truth for
gripper positions — no hardcoded joint values in our code.

The alternative — publishing directly to
`/gripper_controller/follow_joint_trajectory` — is shorter to write
but bypasses the SRDF. If someone later retunes the gripper open /
closed values in the SRDF, our hardcoded numbers would be wrong and
nobody would notice until the gripper started slipping. The named
target approach inherits the retune for free.

## Why we drop the `no_fly_a1` collision object from exercise 20

Exercise 20 added a cylinder above `vial_a1` to mark it as "already
loaded — do not descend." Exercise 21 is **picking** from the source
side, which is conceptually where `vial_a1` lives. Keeping the no-fly
cylinder would refuse our entire pick sequence.

In a real autosampler the no-fly list is a *snapshot of slot status*
that changes as vials are added and removed. The right move is to
recompute that list right before each plan, not to ship it as a
static obstacle. That's a piece of "state machine outside MoveIt"
plumbing — exactly what this exercise leaves to a future layer
(`What's next` section in the README).

## Why no new SDF world

Exercise 20 created `autosampler_cell_v2.sdf` to render the housing
back wall and a visual no-fly marker. Exercise 21 cares about neither
in Gazebo:

- We don't want the no-fly marker (we're picking from that slot).
- We don't strictly need the wall visible in Gazebo — the planning
  scene enforces it for the planner, RViz draws it in the
  `PlanningScene` display.

Reusing the v1 world keeps this exercise's footprint to just the
package directory. Trade-off: an observer watching Gazebo alone
won't see the wall the planner is avoiding. Acceptable for a
sequence demo.

## Why the four Cartesian targets are at (0.180, +/-0.120, *)

Both XY pairs are about 22 cm from the arm base in `base_link` frame,
comfortably inside the 280 mm reach envelope with gripper-down
orientation (roll = pi). The y = +/-0.120 puts the two work points on
opposite sides of the bench so the cross-over swing is visible.

The Z values are picked to clear the rack and tray collision boxes
even at the descend step:

- `z = 0.130` (hover) — clears everything by ~5 cm.
- `z = 0.080` (work) — sits above the top of the rack collision box
  at z = 0.075, so the goal state is collision-free.

If you change the rack or tray sizes in the SDF / collision objects,
the work height needs to come up with them or the goal state will
collide.

## Why a hardcoded sequence is the standard production pattern

Most lab cells, including commercial HPLC autosamplers, are
shipped with a hand-written sequence per task. The "smart" layers
that get added on top later — perception, retry logic, error
recovery, online replanning — depend on the hardcoded sequence
actually working. If the hardcoded version isn't reliable, layering
more code on it just hides the underlying problem.

So getting this exercise to run cleanly is a meaningful checkpoint,
not just a learning exercise: it tells you the motion stack
(URDF + SRDF + MoveIt + controllers + Gazebo) is wired correctly
end-to-end. Everything later builds on this.

## Failure modes

- **`Found a solution but it was outside of the joint limits`** at
  `above_pick` or `above_drop` — the hover Z (0.130) sits right at
  the edge of the reach envelope for some IK seeds. Bring the
  targets closer to the arm (e.g. y = +/-0.100) or lower the hover
  to z = 0.120.
- **Gripper plan succeeds but jaws don't visibly move in Gazebo** —
  the gripper controller is not loaded. Check
  `ros2 control list_controllers`; you should see both
  `arm_controller` and `gripper_controller` as `active`. If the
  gripper one is missing, the upstream `mycobot_gazebo` controllers
  spawner didn't include it.
- **Plan fails on the cross-over step (`above_drop`)** — the
  housing wall is too close. Move it back (increase
  `autosampler_housing_wall` y from 0.23 to 0.25 in the planning
  scene) and rebuild.
- **Sequence runs once, fails on the second invocation** — the
  collision objects from the first run are still in the planning
  scene, getting double-registered. Restart `move_group` between
  runs, or send `obj.operation = obj.REMOVE` before re-adding.
  (Not an issue if you only run the demo once per launch.)
- **`Failed to fetch current state` on the first call** — same
  2-second start-up sleep heuristic as exercises 18-20. Bump to 5 s
  on slow machines.

## What this exercise intentionally does NOT do

- No vision / perception (covered later in the checklist).
- No state machine / BehaviorTree above this loop.
- No `AttachedCollisionObject` and no Gazebo grasp plugin (see
  above).
- No retry logic on failed plans — a single failure aborts the run.
- No `computeCartesianPath` for straight-line descent — we use
  ordinary joint-space planning between hover and work poses, which
  is enough for the sequence to look right.
- No per-vial loop — only one pick / one place. Looping over a
  row of wells is a natural one-line addition but belongs in
  whatever wraps this script, not this script itself.
