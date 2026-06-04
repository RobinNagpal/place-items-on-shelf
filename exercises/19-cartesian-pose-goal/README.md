# 19 — Cartesian pose goal (MoveIt as the IK solver)

Implements checklist item **19** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What is happening (the concept)

In exercise 18 we picked the **pose by name** ("go to `home`") and
MoveIt looked the joint angles up in the SRDF.

In this exercise we pick the pose by **(x, y, z, roll, pitch, yaw)** —
we describe where we want the *tool tip* to end up in 3D space, and
MoveIt figures out the joint angles for us. The "figure out the joint
angles from a tool-tip pose" step is called **inverse kinematics
(IK)**. We never compute the IK ourselves; MoveIt runs it internally
using the KDL solver listed in addison's `kinematics.yaml`.

So:

| Exercise 18 (joint-space) | Exercise 19 (Cartesian, this one) |
|---|---|
| input: a name ("home", "ready") | input: a 6-DoF pose (x, y, z, roll, pitch, yaw) |
| MoveIt looks the joints up in the SRDF | MoveIt **solves IK** to find the joints |
| no math involved | KDL solves the inverse-kinematics equations |

This is the standard way to drive real cells. Almost every higher-level
behaviour (pick, place, scan, dispense) becomes a short sequence of
Cartesian pose goals.

## What is the workflow

We send four targets in a row, mimicking the inner loop of an
autosampler vial transfer:

```
above_source   ->   descend_source   ->   lift_source   ->   above_tray
   (hover)            (down to grasp)        (back up)         (over tray)
```

The chain of components that turns one `setPoseTarget()` call into a
moving arm:

```
       our node (cartesian_pose_demo)
         │   setPoseTarget(x, y, z, roll, pitch, yaw, "link6_flange")
         ▼
       move_group
         │
         │  internal: KDL inverse-kinematics
         │      pose  ->  joint angles
         │
         │  internal: OMPL planner connects current joints to IK answer
         │
         │   sends FollowJointTrajectory goal
         ▼
       joint trajectory controller (in ros2_control)
         │   streams per-timestep joint commands
         ▼
       Gazebo plugin
         │   sets joint positions in the physics sim
         ▼
       arm moves; /joint_states is published back

       AFTER move:
       our node reads arm.getCurrentPose("link6_flange")
       and logs position error (m) + orientation error (deg).
```

So the **new** step compared to exercise 18 is the **IK box** inside
`move_group`. Everything downstream of it is identical.

## The four targets

All targets are in the **arm's `base_link` frame** (origin at the arm's
mounting plate). Roll = π means the gripper points straight down.

| Step | x (m) | y (m) | z (m) | roll | What it represents |
|---|---|---|---|---|---|
| `above_source`   | 0.185 | +0.030 | 0.090 | π | hover 5 cm above the source-rack corner closest to the arm |
| `descend_source` | 0.185 | +0.030 | 0.045 | π | drop down to grasp height (2 cm above rack top) |
| `lift_source`    | 0.185 | +0.030 | 0.090 | π | lift back up |
| `above_tray`     | 0.185 | -0.030 | 0.090 | π | cross over to the destination tray |

Why corners and not centres? Centres of the rack and tray sit close to
the 280 mm reach limit. Corners keep KDL inside a comfortable IK
region so the demo doesn't fight reachability.

How world ↔ base_link coordinates relate: the arm base is at world
`(-0.18, 0, 0.775)` per
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).
So `world_to_base = (world_x + 0.18, world_y, world_z − 0.775)`.

## Common beginner questions

**Are the four targets points in mid-air? Are they "on top of the vials"?**

Each target is just an `(x, y, z, roll, pitch, yaw)` — a coordinate in
space, not an object. Yes, the `above_*` targets are points hanging in
mid-air: 5 cm above the corner of the rack / tray. We picked the
**corner** of the rack, not the centre of a specific vial, because
corners stay comfortably inside the 280 mm reach envelope and the
demo's purpose is to show the *IK loop*, not to grasp anything.

**Do we need to know the exact pose of a vial to do real picks?**

Yes — eventually. For a real pick you have two options:

1. **Hardcoded grid.** The SDF puts the rack at a known pose and the
   wells are on a known 9-mm pitch grid, so vial `A1` is at
   `rack_pose + (0, 0, 0)`, `A2` at `rack_pose + (0.009, 0, 0)` and so
   on. No perception needed; you just compute.
2. **Perception.** A camera detects the vial pose at runtime
   (covered later in the checklist, items 36-40 — depth camera + tag
   detection).

Exercise 21 (full hardcoded pick-and-place) uses option 1.

**What if I run the code twice and the vial moved between runs?**

This exercise never grasps anything, so the world doesn't change.
But the question matters once you add a gripper (exercise 17 + 21).

The target poses are **fixed coordinates in space** — `setPoseTarget`
doesn't know what is or isn't at that pose. On the second run the arm
will happily descend onto an empty spot and close the gripper on air.

The fix is **state tracking** outside of MoveIt: a small piece of
logic that remembers which wells are full and which are empty, and
picks the next target accordingly. Production cells do this with a
state machine (typically in a BehaviorTree or just a script).
Exercise 20 adds another piece of the same puzzle — telling MoveIt
"don't go into a slot that already has a vial in it" via collision
objects.

## What "Done when" means here

The checklist says **end-effector arrives within 5 mm and 2°**. After
every `execute()` the node reads `arm.getCurrentPose("link6_flange")`,
compares it to the requested pose, and logs:

```
'above_source' reached: pos_err=0.0012 m, ori_err=0.42 deg.
```

If any goal is outside tolerance, the program exits with status 1.

## Run it (3 terminals)

```bash
# Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

# Terminal B - move_group (the MoveIt planner action server)
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C - this exercise
ros2 launch cartesian_pose_demo cartesian_pose_demo.launch.py
```

In Terminal C you should see:

```
Planning to 'above_source' (0.185, 0.030, 0.090).   'above_source' reached: pos_err=0.0011 m, ori_err=0.38 deg.
Planning to 'descend_source' (0.185, 0.030, 0.045). 'descend_source' reached: pos_err=0.0009 m, ori_err=0.41 deg.
Planning to 'lift_source' (0.185, 0.030, 0.090).    'lift_source' reached: pos_err=0.0010 m, ori_err=0.39 deg.
Planning to 'above_tray' (0.185, -0.030, 0.090).    'above_tray' reached: pos_err=0.0013 m, ori_err=0.42 deg.
Sequence OK (all goals within tol).
```

In Gazebo the arm visibly hops over the corner of the rack, dips,
lifts, swings over to the tray, and stops.

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/19-cartesian-pose-goal/cartesian_pose_demo
cd ~/ros2_ws
colcon build --packages-select cartesian_pose_demo
source install/setup.bash
```

## What's next

- Exercise 20 adds the rack and tray as MoveIt **collision objects**
  so the planner refuses paths that go through them.
- Exercise 21 strings exercise 17 (gripper) + this Cartesian-goal
  pattern + exercise 20 collisions into the first end-to-end
  pick-and-place.
