# Architecture — 21 Hardcoded pick-and-place

## Folder tree

```
21-hardcoded-pick-and-place/
├── README.md                 # concept + workflow + 11-step table, then run / build
├── ARCHITECTURE.md           # this file
├── IMPLEMENTATION_NOTES.md   # engineering decisions
└── pick_and_place_demo/      # the ROS 2 / ament_cmake package
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── pick_and_place_demo.launch.py
    └── src/
        └── pick_and_place_demo.cpp
```

No new SDF world. We reuse exercise 1's
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf).

## Per-file responsibility

| File | Owns |
|---|---|
| `pick_and_place_demo/src/pick_and_place_demo.cpp` | The 11-step hardcoded sequence: collision-object setup, then `go_named` / `go_pose` calls in order. Two `MoveGroupInterface` handles (one for `arm`, one for `gripper`). |
| `pick_and_place_demo/launch/pick_and_place_demo.launch.py` | Same `MoveItConfigsBuilder` recipe as exercises 19 and 20. Pulls SRDF + kinematics + joint_limits + trajectory_execution from upstream `mycobot_moveit_config`. Does not pass `robot_description` (comes from `robot_state_publisher`). |
| `pick_and_place_demo/CMakeLists.txt` | ament_cmake build. Same dependency set as exercise 20 (`rclcpp`, `geometry_msgs`, `shape_msgs`, `moveit_msgs`, `tf2`, `moveit_ros_planning_interface`). |
| `pick_and_place_demo/package.xml` | Package manifest. `exec_depend` on `mycobot_moveit_config`, `mycobot_gazebo`, `mycobot_description`. |

## How the files interact at runtime

```
gazebo (Terminal A)  <- loads  ../01-custom-gazebo-world/worlds/autosampler_cell.sdf
   ▼
   spawns: bench, arm, rack, tray, three vials

move_group (Terminal B)
   ▼
   running MoveIt action server; planning scene starts empty

launch file (Terminal C)
   ▼
   loads upstream SRDF + kinematics + joint_limits + trajectory exec yaml
   starts our node with all of that as parameters

pick_and_place_demo (our node)
   ▼
   step 0: scene.applyCollisionObjects([bench, rack, tray, housing wall])
                -> move_group's planning scene now has the obstacles
   steps 1-11: alternate go_named / go_pose calls on
                MoveGroupInterface("arm") and MoveGroupInterface("gripper")
                -> each calls plan() then execute()
   exit 0 if every step succeeded
   ▼
arm_controller + gripper_controller (ros2_control) -> Gazebo -> joints move
   /joint_states published back to everyone
```

## The two MoveGroupInterface handles

```cpp
MoveGroupInterface arm(node,     "arm");      // 6 revolute joints
MoveGroupInterface gripper(node, "gripper");  // 1 gripper joint
```

Each is bound to its own SRDF group, and each plans / executes
through its own controller in ros2_control:

- `arm` group   -> `arm_controller`     (joint trajectory controller)
- `gripper` group -> `gripper_controller`

When we call `arm.setNamedTarget("home")`, the planner produces a
6-joint trajectory and the arm controller plays it. When we call
`gripper.setNamedTarget("closed")`, the planner produces a 1-joint
trajectory and the gripper controller plays it. They are independent
action calls; neither blocks the other's planner.

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/planning_scene` | topic | our node → `move_group` | the four collision-object adds |
| `/move_action` | action | our node → `move_group` | named OR Cartesian goals on either group |
| `/arm_controller/follow_joint_trajectory` | action | `move_group` → arm controller | the planned 6-joint trajectory |
| `/gripper_controller/follow_joint_trajectory` | action | `move_group` → gripper controller | the planned 1-joint trajectory |
| `/joint_states` | topic | Gazebo → everyone | current joint positions |
| `/tf`, `/tf_static` | topic | `robot_state_publisher` → everyone | live + fixed transforms |
| `/robot_description` | parameter | `robot_state_publisher` → everyone | URDF text |

## Names from upstream that this exercise depends on

- SRDF groups: `arm` and `gripper`.
- Tip / end-effector link: `link6_flange`.
- Planning frame: `base_link`.
- IK solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`.
- SRDF named states used: `arm/home`, `gripper/open`, `gripper/closed`.

If any of those change upstream, the C++ constants `kArmGroup`,
`kGripperGroup`, `kTipLink`, `kBaseLink` in `pick_and_place_demo.cpp`
must be updated to match.
