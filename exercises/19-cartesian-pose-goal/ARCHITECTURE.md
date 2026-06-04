# Architecture — 19 Cartesian pose goal

## Folder tree

```
19-cartesian-pose-goal/
├── README.md                 # concept + workflow, then technical detail
├── ARCHITECTURE.md           # this file
├── IMPLEMENTATION_NOTES.md   # engineering decisions
└── cartesian_pose_demo/      # the ROS 2 / ament_cmake package
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── cartesian_pose_demo.launch.py
    └── src/
        └── cartesian_pose_demo.cpp
```

## Per-file responsibility

| File | Owns |
|---|---|
| `cartesian_pose_demo/src/cartesian_pose_demo.cpp` | The four Cartesian targets, the `setPoseTarget` + `plan` + `execute` loop, and the post-move position / orientation error check against the 5 mm / 2° tolerance. |
| `cartesian_pose_demo/launch/cartesian_pose_demo.launch.py` | Pulls the SRDF, `kinematics.yaml`, `joint_limits.yaml` and `moveit_controllers.yaml` from upstream `mycobot_moveit_config` via `MoveItConfigsBuilder` and starts the node with `use_sim_time:=true`. Deliberately does **not** pass `robot_description` — it comes from `robot_state_publisher`. |
| `cartesian_pose_demo/CMakeLists.txt` | Standard ament_cmake. Depends on `rclcpp`, `geometry_msgs`, `tf2`, `moveit_ros_planning_interface`. |
| `cartesian_pose_demo/package.xml` | Package manifest. `exec_depend` on `mycobot_moveit_config`, `mycobot_gazebo`, `mycobot_description`. |

## How the files interact at runtime

```
launch file
  │  loads upstream SRDF + kinematics + joint_limits + trajectory exec yaml
  │  starts our node with all of that as parameters
  ▼
cartesian_pose_demo (our node)
  │  MoveGroupInterface("arm")
  │  for each PoseGoal:
  │    setPoseTarget(pose, "link6_flange")
  │    plan() / execute()
  │    getCurrentPose("link6_flange") -> error check
  ▼
move_group (Terminal B, upstream package)
  │  runs KDL IK to convert pose -> joints
  │  runs OMPL RRTConnect to plan the trajectory
  │  sends FollowJointTrajectory goal
  ▼
arm_controller (in ros2_control, brought up by mycobot_gazebo)
  │  streams per-tick joint positions
  ▼
Gazebo plugin -> simulated arm moves; /joint_states publishes back
```

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/move_action` | action | our node → `move_group` | Cartesian pose goal request |
| `/arm_controller/follow_joint_trajectory` | action | `move_group` → joint trajectory controller | the planned joint trajectory |
| `/joint_states` | topic | Gazebo → everyone | current joint positions |
| `/tf`, `/tf_static` | topic | `robot_state_publisher` → everyone | live + fixed transforms |
| `/robot_description` | parameter | `robot_state_publisher` → everyone | URDF text |

## Names from upstream that this exercise depends on

- Planning group: `arm` (defined in
  [`mycobot_280.srdf`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf)).
- Tip / end-effector link: `link6_flange`.
- Planning frame: `base_link`.
- IK solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`, configured in
  [`kinematics.yaml`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_moveit_config/config/mycobot_280/kinematics.yaml).

If any of those names change upstream, the C++ constants
`kArmGroup`, `kTipLink`, `kBaseLink` in `cartesian_pose_demo.cpp`
must be updated to match.
