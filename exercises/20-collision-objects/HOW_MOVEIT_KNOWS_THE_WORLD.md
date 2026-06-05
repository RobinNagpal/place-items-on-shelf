# How does MoveIt know what's in the world?

A beginner-friendly explainer that sits next to this exercise. The
[`README.md`](README.md), [`ARCHITECTURE.md`](ARCHITECTURE.md), and
[`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md) tell you **what
the code does**. This file tells you **what's actually going on
underneath**, so the same lessons carry over from simulation into a
real lab cell.

Two questions get answered:

1. How does MoveIt know about every object so it can avoid collisions?
2. In a real cell there is no SDF / Gazebo config. So how does MoveIt
   know about the bench, the rack, the tray, the vials, etc.?

---

## Q1 — How does MoveIt know about all the objects in the world?

**Short answer.** MoveIt keeps its own private list of obstacles
called the **planning scene**. The arm itself comes from the URDF;
every *other* object — bench, rack, tray, walls, no-fly zones — has
to be **explicitly added** to the planning scene by code at runtime.
If you don't add it, the planner has no idea it exists, and it will
happily plan a path straight through a wall.

There are three separate things MoveIt knows about, and they come
from three different places:

| What | Where it comes from | When it's loaded |
|---|---|---|
| The **arm's own geometry** (every link's collision mesh) | the URDF (`mycobot_280.urdf`) | once, at startup, when `robot_state_publisher` publishes `/robot_description` |
| Which arm links are **allowed to touch each other** (the "allowed collision matrix") | the SRDF (`mycobot_280.srdf`) | once, at startup, via `move_group`'s launch |
| **Everything else in the cell** (bench, rack, tray, housing wall, no-fly zone) | runtime API calls to `PlanningSceneInterface` | every time your node starts, you push them in |

The third row is the whole point of exercise 20. Look at
[`collision_demo/src/collision_demo.cpp:216-248`](collision_demo/src/collision_demo.cpp):

```cpp
PlanningSceneInterface scene;
std::vector<moveit_msgs::msg::CollisionObject> obstacles;

obstacles.push_back(make_box("bench_top",                0.18,  0.00, -0.030, 0.60, 0.40, 0.005));
obstacles.push_back(make_box("source_rack",              0.23,  0.12,  0.050, 0.09, 0.18, 0.05));
obstacles.push_back(make_box("tray_block",               0.23, -0.12,  0.020, 0.16, 0.16, 0.03));
obstacles.push_back(make_box("autosampler_housing_wall", 0.18,  0.23,  0.20,  0.60, 0.02, 0.40));
obstacles.push_back(make_cylinder("no_fly_a1",           0.162, 0.160, 0.130, 0.02, 0.10));

scene.applyCollisionObjects(obstacles);
```

That single `applyCollisionObjects` call is how MoveIt finds out
about the bench, the rack, the tray, the housing wall, and the
no-fly zone. **Before that call the planning scene is empty.**

The [`README.md`](README.md#what-is-happening-the-concept) phrases
the same idea in plain English:

> The "planning scene" is just an in-memory list of shapes that
> `move_group` consults during every collision check. It is *not*
> the SDF / Gazebo world — Gazebo and MoveIt's planning scene are
> two parallel mental models that we keep in sync by hand.

And the [`ARCHITECTURE.md`](ARCHITECTURE.md#two-parallel-models-of-the-world)
draws it explicitly:

```
        Gazebo                     MoveIt planning scene
        ------                     ---------------------
   what we SEE / SIMULATE          what the PLANNER reasons about
   loaded from .sdf                loaded from runtime API calls
   has physics                     has collision geometry only
```

**The big takeaway.** The SDF world (Gazebo) and the planning scene
(MoveIt) are two parallel models of the same room, and **nothing
automatically links them**. You either tell MoveIt about each
obstacle by hand (this exercise), or you hook up a perception
pipeline that does it for you (Q2 below).

---

## Q2 — In the real world there is no SDF / config. How does MoveIt know what's there?

**Short answer.** Exactly the same way as in simulation — you call
`PlanningSceneInterface::applyCollisionObjects`. The API does not
change. What changes is **where the obstacle list comes from**.

Three options, used together in any real cell:

### Option A — Static config

For things that **don't move** — the bench, the housing walls,
mounting brackets, the cabinet — you measure them once with a tape
measure or take them from a CAD model, write them down (a YAML file
or a small Python script), and a startup node pushes them into the
planning scene.

Same `applyCollisionObjects` call as in exercise 20. The only
difference is the *source* of the values: a config file on disk
instead of inline C++ literals.

[`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md#why-we-duplicated-the-v1-sdf-instead-of-including-it)
even calls this out:

> A production cell would generate both the SDF and the
> `CollisionObject` list from a single config (one source of truth);
> see the ARCHITECTURE note on the "two parallel models" problem.

In real life there is no SDF — only the `CollisionObject` half. The
cell builder commits a `cell_geometry.yaml` to the robot's config
repo, a launch-time node parses it, and the planning scene is
populated before the arm is asked to move.

This is **most of what's in a real cell.** Benches and walls never
move, so static config covers them forever.

### Option B — Perception

For things that **do move or change** — vials being placed and
removed, racks getting bumped slightly, a tech leaving a tool on
the bench — you bolt a depth camera (or RGB-D / LIDAR) above the
workspace. A perception node:

1. Reads the depth image every frame.
2. Detects obstacles (or "free slots") using the YOLO / segmentation
   / point-cloud pipeline from exercises 3 – 8.
3. Calls `applyCollisionObjects` to add or remove planning-scene
   shapes as the world changes.

The [`README.md`](README.md#whats-next) flags this explicitly:

> Later exercises (36-40) replace the hardcoded `no_fly_a1` shape
> with a list driven by a depth camera that detects which slots are
> occupied.

And the [`ARCHITECTURE.md`](ARCHITECTURE.md#two-parallel-models-of-the-world)
gives the production rule of thumb:

> Most teams either:
> - Generate both from a single source of truth (e.g. a Python
>   script that emits SDF and `CollisionObject` messages from one
>   config), **or**
> - Detect obstacles from sensors (camera + tag detection) and push
>   the results into the planning scene at runtime. The no-fly marker
>   becomes data, not config.

So in a real autosampler cell, the no-fly cylinders over
already-loaded slots are **not hard-coded**. A depth camera looking
down sees vials present in slots 3, 7, 11, … and the perception
node publishes the matching `CollisionObject`s before the next
pick-and-place cycle.

### Option C — Attached collision objects (a special case)

When the arm **grasps** a vial, the vial moves with the gripper. If
it stays as a static `CollisionObject` at its original pose, two
things go wrong:

- The planner still thinks the original spot is blocked, so it
  refuses paths around the now-empty rack hole.
- It does not realise the gripper is now carrying something that
  could collide with the rack rim, the housing roof, etc.

The fix is to remove the world object and re-attach it to the
end-effector link as an `AttachedCollisionObject`. From then on the
planner treats it as part of the robot — it moves with the arm and
it's part of every collision check.

[`IMPLEMENTATION_NOTES.md`](IMPLEMENTATION_NOTES.md#why-we-dont-add-the-vials-themselves-as-collision-objects)
already flags this as out-of-scope for exercise 20 but in-scope for
exercise 21:

> The correct handling is to use **attached collision objects**
> (`AttachedCollisionObject`) once a vial is grasped, and to update
> the planning scene from a perception layer that tracks where each
> vial actually is. Both are out of scope for this exercise; they
> belong with exercise 21 (pick-and-place) and the later perception
> items.

---

## Putting it together

In **both** simulation and real cells, the API MoveIt uses to learn
about obstacles is the same: `applyCollisionObjects`. What differs
is the source of the data.

| | Sim (this exercise) | Real life |
|---|---|---|
| Static stuff (bench, walls) | hard-coded C++ literals | parsed from a YAML / CAD config |
| Movable stuff (vials, racks) | not modelled — out of scope here | depth-camera perception (items 36-40) |
| Carried stuff (grasped vial) | not modelled — out of scope here | `AttachedCollisionObject` (item 21) |
| Arm's own collision geometry | URDF (same as sim) | URDF (same as sim) |

In short: **simulation is a strict subset of the real-world case.**
This exercise hard-codes obstacles on purpose, so the lesson can
stay focused on "how does MoveIt know". Once you understand the
planning-scene API, swapping the source from C++ literals to a YAML
loader (option A) or a depth camera (option B) is mechanical —
same API call, different inputs.

## Mental model in one line

> The URDF tells MoveIt about the **arm**. The planning scene tells
> MoveIt about **everything else**. In sim you hand-feed the
> planning scene; in real life a config file and a depth camera
> feed it for you.
