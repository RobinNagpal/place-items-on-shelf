# Architecture — 22 Straight-line Cartesian path

## Folder tree

```
22-cartesian-path-following/
├── README.md                 # concept + workflow + 3-way contrast, then run / build
├── ARCHITECTURE.md           # this file
├── IMPLEMENTATION_NOTES.md   # engineering decisions
└── cartesian_path_demo/      # the ROS 2 / ament_cmake package
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── cartesian_path_demo.launch.py
    └── src/
        └── cartesian_path_demo.cpp
```

No new SDF world. We reuse exercise 1's
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).

## Per-file responsibility

| File | Owns |
|---|---|
| `cartesian_path_demo/src/cartesian_path_demo.cpp` | The whole demo. Three logical steps: (1) `go_pose(hover)` — joint-space plan, exercise-19 style, to reach the start of the line; (2) `go_cartesian(work)` — straight-line descend with `computeCartesianPath`; (3) `go_cartesian(hover)` — straight-line lift back. Also seeds the planning scene with the same four collision boxes used in exercises 20 / 21. |
| `cartesian_path_demo/launch/cartesian_path_demo.launch.py` | Same `MoveItConfigsBuilder` recipe as exercises 19-21. Pulls SRDF + kinematics + joint_limits + trajectory_execution from upstream `mycobot_moveit_config`. Does not pass `robot_description` (it comes from `robot_state_publisher`). |
| `cartesian_path_demo/CMakeLists.txt` | ament_cmake build. Same dependency set as exercise 20 (`rclcpp`, `geometry_msgs`, `shape_msgs`, `moveit_msgs`, `tf2`, `moveit_ros_planning_interface`). |
| `cartesian_path_demo/package.xml` | Package manifest. `exec_depend` on `mycobot_moveit_config`, `mycobot_gazebo`, `mycobot_description`. |

## How the files interact at runtime

```
gazebo (Terminal A)  <- loads  ../01-custom-gazebo-world/worlds/autosampler_cell.sdf
   ▼  spawns bench, arm, rack, tray, three vials

move_group (Terminal B)  <- MoveIt action server; planning scene starts empty

launch file (Terminal C)
   ▼  loads upstream SRDF + kinematics + joint_limits + trajectory exec yaml
   starts our node with all of that as parameters

cartesian_path_demo (our node)
   ▼
   step 0: scene.applyCollisionObjects([bench, rack, tray, housing wall])
   step 1: go_pose(hover)         -> joint-space plan via setPoseTarget
   step 2: go_cartesian(work)     -> computeCartesianPath -> execute
   step 3: go_cartesian(hover)    -> computeCartesianPath -> execute
   exit 0 if every step succeeded AND both Cartesian fractions == 1.00

arm_controller (ros2_control) -> Gazebo -> arm moves
                                /joint_states publishes back
```

## Two helper functions, two MoveIt techniques side by side

```cpp
go_pose(arm, hover_pose, logger);   // exercise 19 technique
   arm.setStartStateToCurrentState();
   arm.setPoseTarget(pose_stamped, "link6_flange");
   arm.plan(plan);     // OMPL RRTConnect
   arm.execute(plan);

go_cartesian(arm, "label", goal_pose, logger);   // NEW for exercise 22
   arm.setStartStateToCurrentState();
   std::vector<Pose> waypoints = { goal_pose };
   moveit_msgs::msg::RobotTrajectory trajectory;
   double fraction = arm.computeCartesianPath(
       waypoints,
       /*eef_step=*/0.005,                       // 5 mm between IK calls
       trajectory,
       /*avoid_collisions=*/true);
   // fraction == 1.0 means the full line was achievable
   arm.execute(trajectory);
```

The two helpers exist *together* in the same file so a reader can
compare them line-for-line. They use the **same** `MoveGroupInterface`
handle on the same `arm` SRDF group — only the call inside changes.

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/planning_scene` | topic | our node → `move_group` | the four collision-object adds |
| `/move_action` | action | our node → `move_group` | the **joint-space** plan request (Step 1 only) |
| `/compute_cartesian_path` | service | our node → `move_group` | the Cartesian path request (Steps 2 and 3) |
| `/arm_controller/follow_joint_trajectory` | action | our node → arm controller (we call `execute` directly with the trajectory message returned by `computeCartesianPath`) | the joint trajectory to play |
| `/joint_states` | topic | Gazebo → everyone | current joint positions |
| `/tf`, `/tf_static` | topic | `robot_state_publisher` → everyone | live + fixed transforms |
| `/robot_description` | parameter | `robot_state_publisher` → everyone | URDF text |

`/compute_cartesian_path` is the key new interface compared to
exercises 18-21. It's a ROS 2 service hosted by `move_group`;
`MoveGroupInterface::computeCartesianPath` calls it under the hood.

## Names from upstream that this exercise depends on

Same as exercises 19 / 20:

- SRDF group: `arm`.
- Tip / end-effector link: `link6_flange`.
- Planning frame: `base_link`.
- IK solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`.

If any of those change upstream, the C++ constants `kArmGroup`,
`kTipLink`, `kBaseLink` in `cartesian_path_demo.cpp` must be updated
to match.
