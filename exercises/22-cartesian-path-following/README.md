# 22 — Straight-line Cartesian path (`computeCartesianPath`)

Implements checklist item **22** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What is happening (the concept)

So far we've told MoveIt **where to end up**:

- Exercise 18 said *"end up at the SRDF state `home`"*.
- Exercise 19 said *"end up at `(x, y, z, roll, pitch, yaw)`"*.

In both cases MoveIt picked the joint angles for the endpoint and
then planned a *joint-space* path between current and target. The
gripper's path **through 3D space** was undefined — it could curve,
swing, tilt — whatever the planner invented was fine.

In this exercise we tell MoveIt **the path itself**:

> *"Move the gripper FROM here TO there IN A STRAIGHT LINE."*

The function is **`computeCartesianPath`**. We hand it one or more
waypoints in end-effector space; it interpolates the straight line
between them at small steps (5 mm here), runs IK at every step, and
returns a joint trajectory that traces the line. If any IK step
fails or any step collides, the function returns early with a
`fraction < 1.0` telling us how much of the line was achievable.

This is the third (and last) of the three ways to ask MoveIt to move
the arm.

## What is the workflow

Two segments after we get into position:

```
              (start: arm at home)
                       │
                       │  exercise 19 style:
                       │  setPoseTarget(hover) -> joint-space plan
                       ▼
                  hover pose
                       │
                       │  computeCartesianPath([work])
                       │  -> interpolate 5 mm steps in EE space
                       │  -> IK at every step
                       │  -> trajectory traces a STRAIGHT LINE down
                       ▼
                  work pose (5 cm below hover)
                       │
                       │  computeCartesianPath([hover])
                       │  -> same idea in reverse
                       │  -> STRAIGHT LINE up
                       ▼
                  hover pose again
```

Inside MoveIt, the call chain for one Cartesian segment looks like:

```
       our node (cartesian_path_demo)
         │
         │  computeCartesianPath([goal_pose], 0.005, traj)
         ▼
       MoveGroupInterface
         │   builds a list of N intermediate poses by linearly
         │   interpolating between the current EE pose and goal_pose
         │   in steps of 0.005 m (5 mm).
         │
         │   for each intermediate pose:
         │     run KDL IK -> joint values for THAT exact pose
         │     check collisions vs the planning scene
         │     stitch the joint values into a trajectory
         │
         │   returns fraction = (steps completed) / N
         ▼
       trajectory (RobotTrajectory message)
         │
         │  execute(trajectory)
         ▼
       arm_controller -> Gazebo -> arm moves
```

Note what is **missing** compared to exercises 18 / 19: there is
**no OMPL** in this chain. RRTConnect is not invoked. The path is
not "sampled and connected" — it's just IK-stepped along a known
geometric line. That's why a straight Cartesian path looks so
different from a joint-space plan.

## How this differs from the two earlier approaches

| | 18 — `setNamedTarget` | 19 — `setPoseTarget` | 22 — `computeCartesianPath` (this one) |
|---|---|---|---|
| **Input** | a name like `"home"` | one pose `(x, y, z, roll, pitch, yaw)` | a list of pose waypoints |
| **Where the goal joint values come from** | SRDF lookup | KDL IK at the goal pose | KDL IK at *every* small step along the line |
| **Planner used** | OMPL RRTConnect | OMPL RRTConnect | none — just IK + stitch |
| **Cartesian path between start and goal** | undefined / curved | undefined / curved | **straight line by construction** |
| **What it returns** | `MoveItErrorCode` from `plan()` | same | a **`fraction`** in `[0, 1]` — how much of the line was achievable |
| **Failure mode** | "no plan found" | "no IK at goal" or "no plan found" | `fraction < 1.0` — line broke partway |

The first two control the **endpoints**. This one controls the
**whole path**.

### When the difference matters

- **Descending into a vial well.** Joint-space plan from hover to
  grasp can take a tilted approach: the wrist twists during the
  descent and the gripper grazes the rim. `computeCartesianPath`
  drops the gripper straight down — no tilt, no graze.
- **Pouring.** The container has to stay above the target with a
  controlled tilt during a horizontal move.
- **Drawer / cartridge insertion.** Alignment must hold from the
  moment of contact to the moment the part is seated.
- **A camera scan along a known geometric path** — straight or
  circular.

### When the difference does NOT matter

- **Free-space transit** between two points in the workspace where
  nothing is right next to either pose. Joint-space planning is
  often faster and produces a smoother joint trajectory.
- **Reaching a named SRDF state** — there is no Cartesian goal to
  trace, so `setNamedTarget` is the right tool.

So: **use 18 for named states, 19 for "go to this pose somehow",
22 for "the path itself matters".** Real cells mix all three.

## The two demo segments

Both segments are in the arm's `base_link` frame, gripper pointing
down (roll = π).

| Segment | Start | End | Distance | What it represents |
|---|---|---|---|---|
| Descend | `(0.180, +0.100, 0.130)` | `(0.180, +0.100, 0.080)` | 5 cm down | dropping straight onto a vial cap |
| Lift   | `(0.180, +0.100, 0.080)` | `(0.180, +0.100, 0.130)` | 5 cm up   | clearing the well |

Both are inside the 280 mm reach envelope. We don't pick the
*actual* vial pose because reach + gripper-down orientation is
borderline at the back row; the demo's point is the *path*, not
the location.

## What "Done when" means here

The checklist says: `fraction = 1.0` for a 5 cm vertical descent and
the end-effector trace in RViz is a vertical line.

- `fraction = 1.0` for both segments means IK succeeded at every
  5 mm step and nothing collided. The program exit code is 0 only
  in that case.
- In RViz's "Planned Path" view the EE trace looks like a vertical
  segment, not an arc.

To see the contrast with joint-space planning, comment out the
`go_cartesian` calls and replace them with `go_pose(arm, work, ...)`
and `go_pose(arm, hover, ...)`. The EE trace will arc instead of
going straight — exactly the difference this exercise demonstrates.

## Reading the output

Terminal C prints something like:

```
[pose ] joint-space plan to (0.180, 0.100, 0.130)
[cart ] computeCartesianPath -> descend (5 cm) (0.180, 0.100, 0.080)
  achieved fraction = 1.00 (1.00 = full path)
[cart ] computeCartesianPath -> lift (5 cm)    (0.180, 0.100, 0.130)
  achieved fraction = 1.00 (1.00 = full path)
Sequence OK.
```

## Run it (3 terminals)

```bash
# Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

# Terminal B - move_group (the MoveIt planner action server)
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C - this exercise
ros2 launch cartesian_path_demo cartesian_path_demo.launch.py
```

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/22-cartesian-path-following/cartesian_path_demo
cd ~/ros2_ws
colcon build --packages-select cartesian_path_demo
source install/setup.bash
```

## What's next

This is the **last MoveIt motion exercise**. Section D of the
learning checklist is now complete:

- 18 — joint-space hello world (`setNamedTarget`)
- 19 — Cartesian pose goal (`setPoseTarget` + IK)
- 20 — collision objects in the planning scene
- 21 — hardcoded pick-and-place stringing 18 + 19 + 20 together
- 22 — straight-line Cartesian path (`computeCartesianPath`) ← you are here

Natural follow-ups outside the current motion exercises (covered by
the doc `docs/03-software-stack/04-motion-planning.md` but not
exercised yet):

- Swap KDL → **TRAC-IK** in `kinematics.yaml`; re-run exercise 19
  at the reach edge to compare IK success rate.
- Try **STOMP** or **TrajOpt** for smoother joint-space paths;
  drop-in replacement at the planning-pipeline level.
- Try the **Pilz Industrial Motion Planner** (`PTP`, `LIN`, `CIRC`)
  for industrial-style move primitives.

The checklist itself jumps from here to learning (item 23+).
