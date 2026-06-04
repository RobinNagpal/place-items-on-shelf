# Architecture — 18 Joint-space hello world

## Folder tree

```
18-joint-space-hello-moveit/
├── README.md
├── ARCHITECTURE.md
├── IMPLEMENTATION_NOTES.md
└── park_pose_demo/                 # ament_cmake ROS 2 package
    ├── package.xml
    ├── CMakeLists.txt
    ├── src/
    │   └── park_pose_demo.cpp      # the C++ task
    └── launch/
        └── park_pose_demo.launch.py
```

## File responsibilities

### `park_pose_demo/src/park_pose_demo.cpp`

The only file with real logic. Builds a `MoveGroupInterface` for the
`arm` planning group, sends three named goals (`home -> ready -> home`)
sequentially, returns 0 on success.

- **Why it exists:** the exercise's "Done when" check is a successful
  motion sequence. This file *is* that sequence.
- **What it owns:** the planner choice (OMPL `RRTConnectkConfigDefault`),
  the velocity / acceleration scaling, the actual sequence of named
  targets, and the success / failure reporting.
- **What depends on it:** nothing in this exercise; later exercises
  (19, 20, 21) copy this pattern and extend it.

### `park_pose_demo/launch/park_pose_demo.launch.py`

Wires the runtime parameters that `MoveGroupInterface` needs
(`robot_description_semantic`, `kinematics`, `joint_limits`,
`trajectory_execution`, `planning_pipelines`) onto our node.

- **Why it exists:** without these parameters, MoveGroupInterface has
  no SRDF / IK solver / controller mapping to use, and `setNamedTarget`
  fails.
- **What it owns:** the call to `MoveItConfigsBuilder` that pulls the
  configs out of upstream `mycobot_moveit_config`.
- **What it does NOT own:** the URDF (`robot_description`). That is
  published on a topic by `robot_state_publisher` inside the
  `mycobot_gazebo` launch — we deliberately do not duplicate it.

### `park_pose_demo/package.xml` and `CMakeLists.txt`

Standard ROS 2 ament_cmake boilerplate. Declares the build deps
(`rclcpp`, `moveit_ros_planning_interface`) and the runtime deps
(`mycobot_moveit_config`, `mycobot_gazebo`, `mycobot_description`).

### `README.md`, `ARCHITECTURE.md`, `IMPLEMENTATION_NOTES.md`

Human-readable docs. No software depends on them.

## How the pieces interact at run time

```
[Terminal A]  mycobot_gazebo
                ├── Gazebo (uses ../01-custom-gazebo-world/worlds/autosampler_cell.sdf
                │           when the launch's world arg is set)
                ├── ros2_control + joint trajectory controller (loaded by the URDF's
                │           ros2_control xacro - the arm controller "arm_controller"
                │           is the executor for MoveIt's planned trajectory)
                ├── robot_state_publisher (publishes /robot_description, /tf,
                │           /tf_static, /joint_states)
                └── RViz (optional, for visualisation)

[Terminal B]  mycobot_moveit_config
                └── move_group (the MoveIt 2 action server -
                              subscribes to /robot_description, exposes the
                              MoveGroup action and the planning_scene service)

[Terminal C]  park_pose_demo (this exercise)
                └── park_pose_demo node
                      ├── MoveGroupInterface  ---> sends MoveGroup goals
                      │                              to move_group (Terminal B)
                      └── reads SRDF, kinematics.yaml, joint_limits.yaml,
                          moveit_controllers.yaml from launch parameters
```

The exercise's contribution to that picture is Terminal C only.

## Dependency relationships

```
park_pose_demo (build):
  ├── rclcpp                          (ROS 2 client library)
  └── moveit_ros_planning_interface   (MoveGroupInterface header)

park_pose_demo (runtime):
  ├── mycobot_gazebo                  (provides Terminal A)
  ├── mycobot_moveit_config           (provides Terminal B + the configs
  │                                    that launch_py loads as params)
  └── mycobot_description             (URDF + meshes; pulled in via
                                       mycobot_gazebo)
```

The exercise's only first-party dependency is the existing repo's
[`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf)
(referenced in the launch flow as the world argument). All MoveIt and
arm machinery comes from upstream.
