# Implementation notes — 20 Collision objects

## Why we duplicated the v1 SDF instead of including it

SDF's `<include>` mechanism only loads **models** from a model
database (`model://name`). There is no syntax for "include all the
content of another world file." So to add two new models to the v1
world we had two options:

1. Edit v1 in place (and break exercise 1).
2. Make a standalone v2 file that repeats v1's content.

We picked option 2. The downside is duplication; the upside is that
exercise 1 stays untouched and a learner can `diff` the two files to
see exactly what exercise 20 adds (one wall, one visual marker). For
a tutorial repo that traceability is worth more than DRY.

A production cell would generate both the SDF and the
`CollisionObject` list from a single config (one source of truth);
see the ARCHITECTURE note on the "two parallel models" problem.

## Why the no-fly marker has no `<collision>` tag

The no-fly cylinder represents **a rule, not an object**. In the real
world there is no physical no-fly volume above an already-loaded slot
— there is just a vial sitting in the slot. The "don't lower the arm
here" rule is purely a software construct.

If we put a `<collision>` tag on the marker, Gazebo would treat it
as a real physical wall: vials couldn't be placed in the slot, the
arm couldn't pass through it even if MoveIt allowed it, etc. That
makes the visualization misleading.

So the marker is a `<visual>`-only model. Its only job is to make the
MoveIt rule visible to a human watcher (otherwise the planner would
appear to mysteriously refuse a goal for no visible reason).

## Why `applyCollisionObjects` and not `addCollisionObjects`

`addCollisionObjects` is the legacy API — it publishes to the
`/collision_object` topic and returns immediately, so we'd have to
sleep before planning to be sure the planning scene caught up.

`applyCollisionObjects` calls a service (`/apply_planning_scene`) and
waits for the planning scene to acknowledge the change. By the time
the call returns, the obstacles are guaranteed to be in the scene
that `move_group` uses for collision checks. No race, no sleep
needed.

(The 500 ms sleep we DO have after the call is a small belt-and-
braces wait for RViz's `PlanningScene` display to refresh.)

## Why we don't make the bench a thick slab

The bench in the SDF is 50 mm thick (z = 0.75 to 0.80). In the
planning scene we model it as a 5 mm slab right below `base_link`
(`z = -0.030`, half-thickness 0.0025). The reason: a thick bench box
extending downward would not change planner behaviour (the arm can't
reach into it anyway), and a thick box extending upward would clip
the arm's `link1`, which is mounted ON the bench — causing the
planner to refuse every plan as "start state in collision."

A thin slab keeps it simple and stops only what we care about: a goal
or trajectory below the bench top.

## Why Goal A is "above vial_a3" and not "above vial_a5"

Goal A's job is to demonstrate "route around the housing wall." The
straight-line path from the arm's start configuration to a point
above the back row of vials would clip the wall behind them.
`vial_a3` (the green one in the centre of the back row) gives the
clearest "before/after" RViz difference — with the wall in the
planning scene, the path arcs noticeably; without it, the path is
nearly straight.

`vial_a5` would also work but its position is further right
(positive x), so a portion of the unobstructed path is already a
swing path. Less visually obvious.

## Why Goal B targets z = 0.090 specifically

`no_fly_a1` is a cylinder from z = 0.080 to z = 0.180 in the
`base_link` frame (the cap top is at z ≈ 0.080). Goal B targets
z = 0.090 — 1 cm inside the cylinder — so the goal state's collision
check fails outright. Picking z = 0.075 (just below the cylinder)
would let the goal succeed; picking z = 0.200 (above the cylinder)
would also succeed. We pick a clearly-inside z so the refusal is
unambiguous.

## Why we don't add the vials themselves as collision objects

The three vials are dynamic objects (gravity is on, they have mass).
A `CollisionObject` in the planning scene is treated as **static** by
default — moving it requires another `applyCollisionObjects` call.
If we added them as static collision objects and then a vial fell
over or got grasped, the planning scene would still think the vial
is at the original pose, and the planner would refuse legitimate
paths around the moved vial.

The correct handling is to use **attached collision objects**
(`AttachedCollisionObject`) once a vial is grasped, and to update the
planning scene from a perception layer that tracks where each vial
actually is. Both are out of scope for this exercise; they belong
with exercise 21 (pick-and-place) and the later perception items.

## Failure modes

- **`Failed to add collision object`** in the log — `move_group` is
  not running (start Terminal B) or the planning scene monitor is
  not subscribed yet (bump the start-up sleep from 2 s to 5 s).
- **Goal A is REFUSED even though it should succeed** — the wall is
  too close. Move `autosampler_housing_wall` further back (increase
  its `y` from 0.23 to 0.25) and rebuild.
- **Goal B is accepted even though it should be REFUSED** — the
  no-fly cylinder is too small or too high. Check that `no_fly_a1`'s
  z range covers the goal z. With the values shipped here it should
  fail cleanly.
- **Both goals fail with "current state in collision"** — `link1`
  is intersecting `bench_top`. Make the bench thinner or lower its
  z (we use z = -0.030 by default to leave 30 mm clearance).
- **No obstacles visible in RViz** — add the `PlanningScene` display
  under the MoveIt group, and check the "Scene Geometry" topic is
  `/planning_scene`. Set "Scene Alpha" higher to see them clearly.

## What this exercise intentionally does NOT do

- No gripper open / close (exercise 17 / 21).
- No `AttachedCollisionObject` — vials never get picked up here.
- No perception-driven planning scene updates (covered with the
  depth-camera items 36-40).
- No `computeCartesianPath` for straight-line motion through the
  free space between obstacles — we use ordinary joint-space
  planning, which is enough to demonstrate routing around.
