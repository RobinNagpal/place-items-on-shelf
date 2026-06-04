# 18 — Joint-space "hello world" with MoveIt

A first motion test. We ask MoveIt to drive the arm through three
named positions, one after another:

```
home   ->   ready (our autosampler "park between trays" pose)   ->   home
```

Implements checklist item **18** from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

## What we are NOT doing

- We are **not** writing out joint angles for every step of the motion.
- We are **not** computing the path ourselves.
- We are **not** sending raw motor commands.

## What we ARE doing

1. We tell MoveIt the **target**: "go to the pose named `home`" or
   "go to the pose named `ready`". MoveIt knows what joint values
   those names mean because the SRDF lists them.
2. MoveIt's **planner** figures out a smooth path of joint angles
   that takes the arm from where it is now to where we asked.
3. MoveIt hands that path to the **joint trajectory controller**.
   The controller plays the path back, one timestep at a time, into
   Gazebo.
4. Gazebo moves the simulated arm.

So **MoveIt picks the angles**. We only pick the targets.

## What "home" and "ready" actually look like

Values from upstream
[`mycobot_280.srdf`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf):

| Pose | `link1_to_link2` | `link2_to_link3` | `link3_to_link4` | `link4_to_link5` | `link5_to_link6` | `link6_to_link6_flange` | Looks like |
|---|---|---|---|---|---|---|---|
| `home`  | 0 | 0 | 0      | 0      | 0 | 0 | arm straight up, all joints at zero |
| `ready` | 0 | 0 | 1.5708 | 1.5708 | 0 | 0 | elbow + wrist folded up, gripper above and in front of the shoulder |

`ready` doubles as the **park-between-trays** pose for the autosampler
cell — the folded-up posture keeps the gripper above the bench plane,
clear of the source rack (at `y = +0.12`) and the destination tray
(at `y = -0.12`) in [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).

## How one `setNamedTarget()` call becomes a moving arm

```
       our node (park_pose_demo)
         │   setNamedTarget("ready") + plan() + execute()
         ▼
       move_group  ◄────  reads SRDF, URDF, kinematics from parameters
         │
         │  internal: OMPL planner builds a joint-space trajectory
         │
         │   sends FollowJointTrajectory goal
         ▼
       joint trajectory controller (in ros2_control)
         │   streams per-timestep joint commands
         ▼
       Gazebo plugin
         │   sets joint positions in the physics sim
         ▼
       arm moves;
       /joint_states is published back to everyone
```

## Topics and actions involved

If you want to watch what's happening, open extra terminals and run
`ros2 topic echo <name>` or `ros2 action list`.

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/move_action` | action | our node → `move_group` | "go to named target X" |
| `/display_planned_path` | topic | `move_group` → RViz | a preview of the planned trajectory (purple "ghost" arm) |
| `/arm_controller/follow_joint_trajectory` | action | `move_group` → joint trajectory controller | the actual planned trajectory to play back |
| `/joint_states` | topic | Gazebo → everyone | the arm's current joint positions, every tick |
| `/tf`, `/tf_static` | topic | `robot_state_publisher` → everyone | live + fixed transforms between every link |
| `/robot_description` | parameter | `robot_state_publisher` → everyone who reads it | the URDF text |

## What OMPL and RRTConnect are (in 2–3 lines)

**OMPL = Open Motion Planning Library.** A toolbox of *sampling-based*
planners — they generate random in-between joint states, check each
one is collision-free and inside the joint limits, and connect the
good ones into a path from start to goal. We use **RRTConnect**, an
OMPL algorithm that grows two random trees of joint states (one from
the start, one from the goal) and stops when the trees meet.

We never call OMPL directly. We just hand `move_group` a goal; it
runs OMPL internally and returns the resulting trajectory.

## Run it (3 terminals)

The exercise does **not** redeclare the world. It runs against
whichever Gazebo world is already up. To get the autosampler cell:

```bash
# Terminal A — Gazebo + ros2_control + RViz + robot_state_publisher.
# Point Gazebo at the autosampler world if the upstream launch
# supports it; otherwise see IMPLEMENTATION_NOTES.md.
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

# Terminal B — move_group (the MoveIt planner action server).
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C — this exercise.
ros2 launch park_pose_demo park_pose_demo.launch.py
```

In Terminal C you should see:

```
Planning to 'home'.   Plan ok, executing.
Planning to 'ready'.  Plan ok, executing.
Planning to 'home'.   Plan ok, executing.
Sequence OK.
```

The arm in Gazebo moves: start → home (straight-up T-pose) → ready
(folded up) → home. The "Done when" check from the checklist is
"the arm reaches the goal in sim without warnings."

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/18-joint-space-hello-moveit/park_pose_demo
cd ~/ros2_ws
colcon build --packages-select park_pose_demo
source install/setup.bash
```

## What's next

Exercise 19 (Cartesian pose goal) keeps the same launch flow but
swaps `setNamedTarget` for `setPoseTarget` — you hand MoveIt an
`(x, y, z, roll, pitch, yaw)` and it uses an IK solver to find the
joint angles. After 19, exercise 20 adds the rack and tray as
MoveIt collision objects, and exercise 21 strings the whole thing
into the v1 hardcoded pick-and-place.
