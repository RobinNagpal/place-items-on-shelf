# 18 — Joint-space "hello world" with MoveIt

The smallest possible motion test for the autosampler cell: drive the
myCobot 280 through

```
home  ->  ready (our "park between trays" pose)  ->  home
```

using MoveIt 2's `MoveGroupInterface`. Implements checklist item
**18** (autosampler tie-in) from
[`../../docs/learning-checklist.md`](../../docs/learning-checklist.md).

The whole exercise is one ROS 2 package, `park_pose_demo/`, with
a single C++ node and a launch file.

## Why "ready" is the autosampler park pose

The scene this exercise targets is the world defined in
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf):

- Source rack at `(0.05, +0.12, 0.80) m`
- Destination tray at `(0.05, -0.12, 0.80) m`
- Arm base at `(-0.18, 0, 0.775) m`

The SRDF `ready` pose ([from upstream `mycobot_280.srdf`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf))
sets the joints to

| joint | value |
|---|---|
| `link1_to_link2` (base yaw) | 0 |
| `link2_to_link3` (shoulder) | 0 |
| `link3_to_link4` (elbow) | **1.5708 rad** (π/2) |
| `link4_to_link5` (wrist pitch) | **1.5708 rad** (π/2) |
| `link5_to_link6` (wrist yaw) | 0 |
| `link6_to_link6_flange` (roll) | 0 |

That folds the elbow and wrist up so the gripper sits **above and in
front of the shoulder**, clear of the bench plane. The horizontal
clearance over both peripherals at `y = ±0.12` is large — the gripper
is roughly above the arm's own footprint. So `ready` doubles cleanly
as the autosampler park-between-trays pose without us having to
define a new named target.

## The C++ task in one paragraph

`src/park_pose_demo.cpp` is ~70 lines including comments. It:

1. Builds a `MoveGroupInterface` for the `arm` planning group.
2. Picks the OMPL planner `RRTConnectkConfigDefault` and slow-ish
   velocity / acceleration scaling so a human can watch the motion.
3. Calls `go_to("home") -> go_to("ready") -> go_to("home")`, each
   step latching `setStartStateToCurrentState()` and
   `setNamedTarget(name)` against the SRDF, planning, and executing.

That's it.

## Run it (3 terminals)

The exercise does **not** redeclare the world. It runs against whichever
Gazebo world is already up. To reproduce the autosampler cell:

```bash
# Terminal A - Gazebo + ros2_control + RViz + robot_state_publisher
# Pass the autosampler world if the upstream launch supports it:
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
    world:=$(pwd)/exercises/01-custom-gazebo-world/worlds/autosampler_cell.sdf

# If the fork's launch ignores the world arg, see
# IMPLEMENTATION_NOTES.md for the standalone-Gazebo fallback.

# Terminal B - move_group action server
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C - this exercise
ros2 launch park_pose_demo park_pose_demo.launch.py
```

You should see the arm move `home -> ready -> home`, each transition
preceded by `Planning to '<name>'. Plan ok, executing.` in the
Terminal C log. The "Done when" check from the checklist:

> The arm reaches the goal in sim without warnings.

## Build it

```bash
cd ~/ros2_ws/src
ln -s /path/to/exercises/18-joint-space-hello-moveit/park_pose_demo
cd ~/ros2_ws
colcon build --packages-select park_pose_demo
source install/setup.bash
```

(Or copy the package in directly. The package name is `park_pose_demo`.)

## What's next

Exercise 19 (Cartesian pose goal) keeps the same launch flow but swaps
`setNamedTarget` for `setPoseTarget` — you hand MoveIt an
`(x, y, z, rpy)` and it solves the IK. After 19, exercise 20 adds the
rack and tray as MoveIt collision objects, and exercise 21 strings
everything together into the v1 hardcoded pick-and-place.
