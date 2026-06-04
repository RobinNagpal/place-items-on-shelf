# Implementation notes — 18 Joint-space hello world

## Why C++ and not Python

The checklist allows either. We picked C++ because:

1. `cobot280_moveit_task` already uses the C++ `MoveGroupInterface`
   pattern, so the reader can compare two files in the same style.
2. The C++ MoveIt 2 API is more complete and better documented than
   `moveit_py`.
3. `moveit_ros_planning_interface` is part of the default `ros-${DISTRO}
   -moveit-*` install set; `moveit_py` needs `ros-${DISTRO}-moveit-py`,
   which is an extra dep.

The cost: ~70 lines including boilerplate, where a Python equivalent
might be ~25. The exercise still fits the checklist's "20-line script"
spirit because only ~15 lines are real logic — the rest is comments
and the ROS 2 node skeleton.

## Why we reuse `ready` instead of defining a "park" pose

The SRDF `ready` pose
([`mycobot_280.srdf` upstream](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf))
already sets joints 3 and 4 to π/2 each, which folds the elbow and
wrist up. The gripper ends above and in front of the shoulder — well
clear of both peripherals in the autosampler cell.

Defining a new `park` named state would mean editing the upstream
SRDF (which we cannot do without forking) or shipping a sibling SRDF
in this exercise (which would duplicate the rest of `mycobot_280.srdf`
for no benefit). Reusing `ready` is shorter and stays in sync if
upstream tweaks the pose.

If a future exercise needs a *different* park pose, the right move
is to bypass `setNamedTarget` and call `setJointValueTarget(joints)`
with the values inline — same pattern, no SRDF edits.

## Why we set planner / scaling / planning_time explicitly

The defaults are sensible but undocumented; setting them explicitly
makes the code self-explanatory:

- `setPlanningPipelineId("ompl")` — MoveIt 2 supports several
  pipelines (OMPL, CHOMP, STOMP, Pilz); OMPL is the default and the
  one the upstream config is tuned for.
- `setPlannerId("RRTConnectkConfigDefault")` — RRTConnect is a fast,
  well-tested OMPL sampling planner. Good for joint-space goals on
  arms with up to ~7 DoF.
- `setPlanningTime(2.0)` — 2 seconds is plenty for a single goal on
  a 6-DoF arm in an empty workspace. Bump to 5–10 s when collision
  objects are added in exercise 20.
- `setMaxVelocityScalingFactor(0.3)` and `setMaxAccelerationScalingFactor(0.3)` —
  scale the joint-limit-based timing down to 30 % so a human watching
  Gazebo can actually see the motion. For real hardware drop this
  further (start at 0.1, ramp up).

## Why a 2-second sleep after constructing `MoveGroupInterface`

`MoveGroupInterface` needs to subscribe to a few topics
(`/joint_states`, the MoveGroup action's feedback, `/tf`,
`/tf_static`) and connect to the MoveGroup action server before it
can plan. If we call `plan()` immediately, the first call sometimes
fails with "current state is not yet known".

Two seconds is a heuristic that works on a typical laptop. For
production code, replace the sleep with an explicit "wait for action
server + first joint state" loop. For a hello-world demo, a sleep is
fine.

## Why we load the SRDF + kinematics + joint_limits via launch
## parameters rather than reading them from disk in the node

Two reasons:

1. `MoveGroupInterface` expects them as ROS parameters
   (`robot_description_semantic`, `robot_description_kinematics`, ...)
   — passing them via the launch file is the canonical pattern.
2. Loading them as parameters means the same node binary works against
   any compatible robot config without recompiling.

The launch file's `MoveItConfigsBuilder` call is verbose because the
config is split across four YAML files plus the SRDF. We could
inline that in the node, but then editing a YAML would require a
rebuild — which the launch-file approach avoids.

## Why we do NOT pass `moveit_config.robot_description`

The URDF (`robot_description`) is published as a parameter by
`robot_state_publisher` inside the `mycobot_gazebo` launch. Passing
it again from our launch file would cause two competing publishers
and confuse anyone running RViz. So the launch comment notes:
"URDF is pulled from the running robot_state_publisher's
/robot_description topic, so we do NOT pass moveit_config.robot_description here."

## Launch-flow gotcha: world arg support

`mycobot_gazebo.mycobot.gazebo.launch.py` historically takes a
`world` arg, but forks vary. Two known cases:

1. **Fork accepts `world:=<path>`** — pass the absolute path to
   `autosampler_cell.sdf`. Everything works.
2. **Fork ignores `world`** — Gazebo loads the upstream default world.
   The arm still moves correctly but the rack / tray / vials are not
   in the scene. The exercise still passes its "Done when" check
   (arm reaches the goal without warnings), and the *autosampler
   tie-in* (proving `ready` clears the cell) becomes a paper check
   against the SDF rather than a visual one.

Fallback if the world arg is not accepted: launch Gazebo standalone
on the SDF (`gz sim path/to/autosampler_cell.sdf`), then spawn the
arm and start the controllers via the upstream's spawner launch
files. This is more invasive and is intentionally out of scope for
this exercise.

## Failure modes

- **`MoveGroupInterface: No such group 'arm'`** — `move_group` is
  not running (Terminal B is missing) or the SRDF was not loaded.
  Check `ros2 node list | grep move_group`.
- **`Planning to 'home' failed`** — current joint state is outside
  the planner's assumptions. Re-launch Gazebo so the arm spawns at
  zeros, or relax planning time to 5 s.
- **Plan succeeds in RViz but arm does not move in Gazebo** — the
  joint trajectory controller is not active. Check
  `ros2 control list_controllers`; `arm_controller` should be
  `active`.
- **First plan call fails right after start-up** — the 2 s sleep is
  too short on a slow machine. Bump it to 5 s.

## Things this exercise intentionally does not do

- Does NOT define new collision objects (that is exercise 20).
- Does NOT use IK / Cartesian goals (that is exercise 19).
- Does NOT touch the gripper (that is exercise 17 / the gripper
  group in the SRDF).
- Does NOT redeclare or modify the world SDF — the autosampler scene
  lives in `../01-custom-gazebo-world/worlds/autosampler_cell.sdf`
  and stays there.
