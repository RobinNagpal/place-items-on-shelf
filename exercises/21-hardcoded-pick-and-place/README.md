# 21 — Hardcoded pick-and-place

Implements checklist item **21** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What is happening (the concept)

This is the first "useful-looking" exercise. The arm:

1. Starts at home,
2. Opens the gripper,
3. Goes to the source side, descends, closes the gripper (pretending to pick a vial),
4. Lifts, crosses to the destination side, descends, opens the gripper (pretending to place the vial),
5. Lifts and returns home.

**Hardcoded** means *every pose, every gripper command, and the order
they happen in is written into the source file as plain literals*.
There is **no perception** (no camera detecting where the vial is),
**no state machine** (no "if slot is empty, try next slot"), and
**no planner intelligence above the trajectory level** — MoveIt only
does motion between the points we specify.

This is how almost every production cell ships its **first** version.
Smart layers (perception, BehaviorTree, retry logic) get added later
on top of a working hardcoded sequence. Getting the hardcoded version
running is what proves the motion stack actually works.

This exercise combines what we already learned:

| Used from | What it gives us |
|---|---|
| Exercise 18 | `setNamedTarget("home")` (arm) and `setNamedTarget("open")` / `"closed"` (gripper) |
| Exercise 19 | `setPoseTarget(x, y, z, roll, pitch, yaw)` for the four mid-air targets above the source / destination |
| Exercise 20 | `PlanningSceneInterface::applyCollisionObjects(...)` for the bench, rack, tray, and housing wall |

Nothing genuinely new is introduced — we just sequence the three
techniques into one program.

## What is the workflow

The sequence is **11 steps**. Read left → right:

```
1.  arm  home (named)
2.  grip open (named)
       ┌────────────── PICK ───────────────┐
3.  arm  above_pick   (pose, hover)        │  exercise 19 style
4.  arm  grasp        (pose, descend)      │  exercise 19 style
5.  grip closed (named)                    │  exercise 18 style
6.  arm  lift_pick    (pose, lift back)    │  exercise 19 style
       └───────────────────────────────────┘
       ┌────────── TRANSIT + PLACE ────────┐
7.  arm  above_drop   (pose, cross over)   │
8.  arm  release      (pose, descend)      │
9.  grip open (named)                      │
10. arm  lift_drop    (pose, lift back)    │
       └───────────────────────────────────┘
11. arm  home (named)
```

The chain of components that turns each step into actual joint
motion is identical to what we built up across 18-20:

```
       our node (pick_and_place_demo)
         │
         │  step 0: applyCollisionObjects(bench, rack, tray, wall)
         │
         │  step N: setNamedTarget OR setPoseTarget on
         │          MoveGroupInterface("arm") or ("gripper")
         ▼
       move_group
         │   - SRDF lookup        (for named targets)
         │   - KDL IK              (for pose targets)
         │   - OMPL RRTConnect     (path between current and goal)
         │   - collision checks    (rejects paths through obstacles)
         │
         │   sends FollowJointTrajectory goals
         ▼
       arm_controller   AND   gripper_controller   (ros2_control)
         │
         ▼
       Gazebo plugin -> joint positions update in physics sim
         │
         ▼
       /joint_states published back to everyone
```

Two `MoveGroupInterface` handles live in the program — one bound to
the SRDF `arm` group (the 6 revolute joints), one bound to the
`gripper` group (the single gripper joint). Named-target lookups on
each go to their own SRDF group; the underlying controllers in
ros2_control are separate too (`arm_controller` and
`gripper_controller`).

## The four Cartesian targets

All in the arm's `base_link` frame, gripper-pointing-down (roll = π).

| Label | x (m) | y (m) | z (m) | What it represents |
|---|---|---|---|---|
| `above_pick` | 0.180 | +0.120 | 0.130 | hover 5 cm above the source side |
| `grasp`      | 0.180 | +0.120 | 0.080 | work height on the source side |
| `above_drop` | 0.180 | -0.120 | 0.130 | hover 5 cm above the destination side |
| `release`    | 0.180 | -0.120 | 0.080 | work height on the destination side |

Numbers are picked to stay comfortably inside the 280 mm reach
envelope. They are intentionally **not** tied to a specific vial
pose — the point of this exercise is the SEQUENCE and the mixing of
named / Cartesian / collision techniques, not landing on a particular
cap. A real autosampler routine would compute these from the rack
grid (well row, well column → pose), which is exactly the kind of
small derivation a higher layer of code would do on top of this.

## What you'll see when you run it

Terminal C prints something like:

```
Added 4 collision objects.
[named] arm     -> 'home'
[named] gripper -> 'open'
[pose ] arm     -> above_pick   (0.180, 0.120, 0.130)
[pose ] arm     -> grasp        (0.180, 0.120, 0.080)
[named] gripper -> 'closed'
[pose ] arm     -> lift_pick    (0.180, 0.120, 0.130)
[pose ] arm     -> above_drop   (0.180, -0.120, 0.130)
[pose ] arm     -> release      (0.180, -0.120, 0.080)
[named] gripper -> 'open'
[pose ] arm     -> lift_drop    (0.180, -0.120, 0.130)
[named] arm     -> 'home'
Sequence OK.
```

In Gazebo: the arm goes home, the gripper opens, the arm hops over to
the source side, dips, the gripper closes, the arm lifts, swings to
the destination side, dips, the gripper opens, the arm lifts, and
returns home. The vial does **not** actually move with the gripper —
see IMPLEMENTATION_NOTES for why and what would be needed to make it
stick.

## What "Done when" means here

The checklist says: "The arm reliably moves a cube from the table to
a target spot 30 cm away across 10 consecutive runs."

Our equivalent:

- All 11 steps complete without `plan` or `execute` failures
  (program exits with status 0).
- Running it 10 times in a row never fails. With the conservative
  velocity/acceleration scaling (0.3) and 5 planning attempts per
  goal, this is reliable on the autosampler cell layout.

We don't measure end-effector accuracy here (that was exercise 19's
"5 mm / 2°" check). For a hardcoded sequence the trajectory tracking
of the joint controllers, not IK accuracy, is the dominant source of
error — and it's good enough for a sim demo by default.

## Run it (3 terminals)

```bash
# Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

# Terminal B - move_group (the MoveIt planner action server)
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C - this exercise
ros2 launch pick_and_place_demo pick_and_place_demo.launch.py
```

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/21-hardcoded-pick-and-place/pick_and_place_demo
cd ~/ros2_ws
colcon build --packages-select pick_and_place_demo
source install/setup.bash
```

## What's next

This is the last MoveIt motion exercise in this batch. The natural
follow-ups, in order of how much they buy you:

1. **Attached collision object + grasp plugin** — so the vial
   actually moves with the gripper in Gazebo. Cheap to add; makes the
   demo look real.
2. **Compute targets from the rack grid** (`well[row][col]` → pose)
   instead of hardcoded literals. Tiny script change; immediately
   useful for moving a whole row.
3. **State machine on top** (BehaviorTree.CPP, or just a Python loop)
   that asks "what's the next vial to pick?" and tracks which wells
   are full. This is what production cells run.
4. **Perception** (depth camera + tag detector, checklist items
   36–40) replacing "hardcoded vial position" with "detected vial
   position." Most expensive layer; biggest jump in capability.
