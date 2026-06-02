# cobot280_moveit_task

Minimal custom MoveIt 2 task for the myCobot 280 arm. The task moves through:

1. Named SRDF pose `home` (all joints 0).
2. Named SRDF pose `ready` (elbow / wrist bent up).
3. Explicit joint goal `[0.5, -0.3, 0.8, -0.5, 0.0, 0.0]` rad.
4. Back to `home`.

Group names (`arm`) and named poses (`home`, `ready`) come from
[automaticaddison/mycobot_ros2 `mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf).
We talk to MoveIt 2 via `MoveGroupInterface` (C++), the same pattern
addison's `mycobot_moveit_demos/hello_moveit.cpp` uses — so this is the
"custom code + reuse from upstream" path requested.

## Build

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash   # or humble
colcon build --packages-select cobot280_moveit_task
source install/setup.bash
```

## Test it out (3 terminals)

```bash
# Terminal A — Gazebo + ros2_control + RViz + robot_state_publisher (Step 2)
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py

# Terminal B — MoveIt move_group action server (Step 3)
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_moveit_config move_group.launch.py

# Terminal C — our task
source ~/ros2_ws/install/setup.bash
ros2 launch cobot280_moveit_task move_to_named_pose.launch.py
```

You should see the Gazebo arm move: `home` -> `ready` -> joint goal -> `home`,
each transition preceded by an OMPL plan in the Terminal C logs
(`Planning to named target: home` -> `Plan ok, executing.` -> ...).

## Verify without Gazebo

If you want to validate the planning path only (no physics), swap Terminal A
for RViz-only mode and skip Terminal B's controllers:

```bash
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py use_gazebo:=false
ros2 launch mycobot_moveit_config move_group.launch.py
ros2 launch cobot280_moveit_task move_to_named_pose.launch.py
```

The RViz ghost arm will trace each trajectory; nothing will move in physics,
which is the correct behaviour for `use_gazebo:=false`.

## Troubleshooting

- **`MoveGroupInterface: No such group 'arm'`** — addison's
  `mycobot_moveit_config` isn't sourced or move_group isn't running. Check
  `ros2 node list | grep move_group`.
- **Plan succeeds in RViz but arm doesn't move in Gazebo** — JTC controller
  isn't active. `ros2 control list_controllers` should show
  `arm_controller` active.
- **`Planning to 'home' failed (code -1)`** — current joint state likely
  outside SRDF assumptions. Re-launch Gazebo so the arm spawns at the zero
  pose.
