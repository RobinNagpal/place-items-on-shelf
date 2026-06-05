# 20 — Collision objects in MoveIt's planning scene

Implements checklist item **20** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

> **New reader?** Start with
> [`HOW_MOVEIT_KNOWS_THE_WORLD.md`](HOW_MOVEIT_KNOWS_THE_WORLD.md) —
> a beginner explainer for "how does MoveIt know which objects to
> avoid?" in simulation **and** in a real cell. The rest of this
> file assumes you already get that mental model.

## What is happening (the concept)

In exercises 18 and 19 the planner only thought about the arm itself.
It had no idea the bench, the rack, the tray, or the autosampler
housing existed. If we had asked it to plan a path through a wall, it
would happily have done so — and the simulated arm would have driven
straight into the wall.

In this exercise we **tell MoveIt about the obstacles**. We push five
shapes into MoveIt's *planning scene* before any planning happens:

| Obstacle | Shape | What it represents |
|---|---|---|
| `bench_top` | thin box | the bench surface; stops the arm dipping below it |
| `source_rack` | box | the 5x10 vial rack |
| `tray_block` | box | the destination tray + alignment plate |
| `autosampler_housing_wall` | box | the back wall of the autosampler housing |
| `no_fly_a1` | cylinder | a vertical column above vial_a1's cap, marking the slot as "already loaded — do not descend" |

Once these objects are in the planning scene, the planner refuses any
trajectory that would pass a robot link through one of them. **No
extra code in our pose loop is needed** — collision avoidance is
something MoveIt does automatically as soon as obstacles exist.

So the only new step compared to exercise 19 is **adding obstacles**.
Everything downstream (IK, OMPL, joint trajectory controller, Gazebo)
is identical.

## What is the workflow

```
       our node (collision_demo)
         │
         │  step 1:  scene.applyCollisionObjects([...5 shapes...])
         │           -> bench, rack, tray, housing wall, no_fly_a1
         ▼
       move_group  (planning scene now knows about the obstacles)
         │
         │  step 2:  setPoseTarget(goal) + plan()
         │
         │  internal: OMPL only accepts joint configurations that
         │            DON'T put any robot link inside an obstacle
         │
         ▼
       joint trajectory controller -> Gazebo -> arm moves
                (or, for Goal B: plan() returns FAILURE and nothing moves)
```

The "planning scene" is just an in-memory list of shapes that
`move_group` consults during every collision check. It is *not* the
SDF / Gazebo world — Gazebo and MoveIt's planning scene are two
parallel mental models that we keep in sync by hand. Anything we add
to `../worlds/autosampler_cell_v2.sdf` is for Gazebo to render and
physically simulate; anything we add via `PlanningSceneInterface` is
for MoveIt to reason about.

## The two demo goals — the use cases

The node runs two pose goals back to back. Each one shows a different
way collision objects matter in production cells.

### Use case 1 — "smart routing"

**Goal A:** hover above `vial_a3` (the green-cap one in the middle of
the back row). The straight-line joint-space path between the arm's
current pose and this point would clip the back wall of the housing,
which we just added as `autosampler_housing_wall`.

**Expected behaviour:** plan **succeeds**, but the joint trajectory
visible in RViz's "Planned Path" view goes **around** the wall instead
of through it. The arm reaches the goal.

This is what most production autosampler / pipetting / etc. cells get
out of collision objects: the planner finds a longer-but-safe path
without anyone hand-coding waypoints.

### Use case 2 — "refuse the unsafe goal"

**Goal B:** descend onto `vial_a1` (the red-cap one, already loaded).
The goal pose sits 1 cm above the vial cap — but that point is
**inside** the `no_fly_a1` cylinder.

**Expected behaviour:** plan **fails**. The planner reports "no
solution" because the goal state itself is in collision.

This is the second thing collision objects buy you: safety against
**you giving the wrong goal**. If your higher-level state machine
slips up and asks the arm to lower onto an occupied slot, the
collision object catches it before the arm ever moves. In a real
HPLC autosampler this prevents crushed vials, broken needles, and
spilled samples.

## Reading the output

Run Terminal C and you should see something like:

```
Added 5 collision objects to the planning scene.
Trying goal 'above_vial_a3 (route around housing)' (0.180, 0.160, 0.120).
  Expected: success (path bends around obstacles).
  'above_vial_a3 (route around housing)' OK - arm moved.
Trying goal 'descend_onto_vial_a1 (into no_fly zone)' (0.162, 0.160, 0.090).
  Expected: REFUSED (goal inside an obstacle).
  'descend_onto_vial_a1 (into no_fly zone)' correctly REFUSED by planner.
Demo OK (Goal A succeeded, Goal B refused as expected).
```

Two ways to confirm the planner really is using the obstacles:

1. **Watch RViz.** Add a `PlanningScene` display under the "MoveIt"
   group. The five obstacle shapes appear as wireframes. The "Planned
   Path" view for Goal A visibly bends.
2. **Comment out `scene.applyCollisionObjects(obstacles)`** in
   `collision_demo.cpp` and re-run. Goal A's path becomes
   straight-line (it would actually clip the wall in real hardware)
   and Goal B succeeds (the arm tries to descend into vial_a1).

## Common beginner questions

**Which approach (exercise 18 or 19) does this exercise use to send
the goals?**

This exercise uses the **exercise-19 approach** — `setPoseTarget`
with arbitrary `(x, y, z, roll, pitch, yaw)` in the arm's `base_link`
frame. The single line that proves it is at
`collision_demo/src/collision_demo.cpp:151`:

```cpp
arm.setPoseTarget(target, kTipLink);
```

There is **no** `setNamedTarget("...")` call (the exercise-18 way)
anywhere in the file.

Why we picked the 19 approach over the 18 approach:

|  | Exercise 18 (`setNamedTarget`) | This exercise (`setPoseTarget`) |
|---|---|---|
| Input | a name like `"home"` or `"ready"` | arbitrary `(x, y, z, roll, pitch, yaw)` |
| Where targets come from | the SRDF (`mycobot_280.srdf`) | inline in our C++ |
| Can target arbitrary points? | No — only the SRDF's named poses | Yes — any point in space |
| Inverse kinematics | not needed (joints already in SRDF) | needed; `move_group` runs KDL |

The exercise-18 approach can only reach poses someone wrote into the
SRDF ahead of time. Upstream `mycobot_280.srdf` only defines two:
`home` and `ready`. Exercise 20 has to demonstrate:

- "**route around** the housing wall to reach above `vial_a3`" — an
  arbitrary point above the back row.
- "**refuse** a descent onto `vial_a1`" — an arbitrary point 1 cm
  above the red-cap vial.

Neither of those is in the SRDF. Adding them would require editing
the upstream SRDF (we don't fork it; see exercise 18's
IMPLEMENTATION_NOTES). So the natural way to write these goals is
`setPoseTarget` calls — the exercise-19 pattern.

**Short answer:** **Exercise 20 = exercise 19 + obstacles.** Pose
goals are sent the exercise-19 way; only the planning-scene setup
is new. Exercise 21 will mix BOTH approaches: named poses for
`home` / gripper open / close, plus Cartesian pose goals for the
above-vial / descend / lift / above-dest / release coordinates.

## What "Done when" means here

The checklist says: a goal under the table is rejected, and adding a
wall changes the planned path visibly. Both happen above:

- **Goal B is correctly rejected** because its target is inside an
  obstacle. The program exit code is `0` only if both goals behaved
  as expected.
- **Goal A's path bends.** RViz's "Planned Path" trace shows the
  detour. There is no numeric check for "did the path bend" — the
  before/after RViz comparison is the visual confirmation.

## Run it (3 terminals)

```bash
# Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher
# (point at the v2 world for the new housing wall + no-fly marker)
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/20-collision-objects/worlds/autosampler_cell_v2.sdf

# Terminal B - move_group (the MoveIt planner action server)
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C - this exercise
ros2 launch collision_demo collision_demo.launch.py
```

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/20-collision-objects/collision_demo
cd ~/ros2_ws
colcon build --packages-select collision_demo
source install/setup.bash
```

## What's next

- Exercise 21 strings the gripper (exercise 17), Cartesian pose goals
  (exercise 19) and these collision objects into the first end-to-end
  pick-and-place.
- Later exercises (36-40) replace the hardcoded `no_fly_a1` shape
  with a list driven by a depth camera that detects which slots are
  occupied.
