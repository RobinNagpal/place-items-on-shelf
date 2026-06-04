# Architecture — 20 Collision objects

## Folder tree

```
20-collision-objects/
├── README.md                          # concept + workflow + use cases, then details
├── ARCHITECTURE.md                    # this file
├── IMPLEMENTATION_NOTES.md            # engineering decisions
├── worlds/
│   └── autosampler_cell_v2.sdf        # v1 world + housing back wall + no-fly visual marker
└── collision_demo/                    # the ROS 2 / ament_cmake package
    ├── CMakeLists.txt
    ├── package.xml
    ├── launch/
    │   └── collision_demo.launch.py
    └── src/
        └── collision_demo.cpp
```

## Per-file responsibility

| File | Owns |
|---|---|
| `worlds/autosampler_cell_v2.sdf` | A standalone copy of v1 plus two new objects: the autosampler housing back wall (physical) and a semi-transparent no-fly marker over `vial_a1` (visual only). Kept separate from v1 so a learner can diff the two files. |
| `collision_demo/src/collision_demo.cpp` | Builds the five `moveit_msgs::msg::CollisionObject` shapes (in `base_link` frame), pushes them via `PlanningSceneInterface::applyCollisionObjects`, then runs Goal A (expected success) and Goal B (expected refusal). Exit status reports whether both behaved as expected. |
| `collision_demo/launch/collision_demo.launch.py` | Same `MoveItConfigsBuilder` recipe as exercise 19 — pulls SRDF + kinematics + joint_limits + trajectory_execution from upstream `mycobot_moveit_config` and starts the node with `use_sim_time:=true`. Does not pass `robot_description` (comes from `robot_state_publisher`). |
| `collision_demo/CMakeLists.txt` | ament_cmake build. Depends on `rclcpp`, `geometry_msgs`, `shape_msgs`, `moveit_msgs`, `tf2`, `moveit_ros_planning_interface`. |
| `collision_demo/package.xml` | Package manifest. `exec_depend` on `mycobot_moveit_config`, `mycobot_gazebo`, `mycobot_description`. |

## How the files interact at runtime

```
gazebo (Terminal A)  <- loads  worlds/autosampler_cell_v2.sdf
   │   spawns: bench, arm, rack, tray, vials, housing wall,
   │           no-fly visual marker (the last one is visual-only)
   ▼
move_group (Terminal B)
   │   running MoveIt action server; planning scene starts empty

launch file (Terminal C)
   │   loads upstream SRDF + kinematics + joint_limits + trajectory exec yaml
   │   starts our node with all of that as parameters
   ▼
collision_demo (our node)
   │   step 1: scene.applyCollisionObjects([5 shapes])
   │             -> move_group's planning scene now has the obstacles
   │   step 2: setPoseTarget(Goal A) -> plan -> execute
   │             -> path bends around housing wall
   │   step 3: setPoseTarget(Goal B) -> plan
   │             -> planner reports FAILURE (goal inside no_fly_a1)
   │   exit 0 if both behaved as expected, 1 otherwise
   ▼
arm_controller -> Gazebo -> arm moves (only for Goal A)
```

## Two parallel models of the world

This is the conceptual point of the exercise. Gazebo and MoveIt do
**not** share their world model:

```
        Gazebo                     MoveIt planning scene
        ------                     ---------------------
   what we SEE / SIMULATE          what the PLANNER reasons about
   loaded from .sdf                loaded from runtime API calls
   has physics                     has collision geometry only
```

The autosampler housing wall is in **both** (we put it in the SDF for
visualization + physics, and our node pushes a matching box into the
planning scene).

The no-fly marker is **visual only in the SDF** (no `<collision>`
tag) — the corresponding cylinder lives only in the planning scene.
A real autosampler housing has no yellow cylinder hanging in mid-air;
it just has the rule "don't lower into an occupied slot." That rule
is a MoveIt construct, not a physical one.

Keeping these two models in sync by hand is a real maintenance burden
in production cells. Most teams either:

- Generate both from a single source of truth (e.g. a Python script
  that emits SDF and `CollisionObject` messages from one config), or
- Detect obstacles from sensors (camera + tag detection) and push the
  results into the planning scene at runtime. The no-fly marker
  becomes data, not config.

Both approaches are out of scope here; this exercise just makes the
two-model split explicit so the learner notices it.

## ROS interfaces touched

| Name | Type | Direction | Carries |
|---|---|---|---|
| `/planning_scene` | topic | our node → `move_group` | the five collision object adds |
| `/move_action` | action | our node → `move_group` | Cartesian pose goal request |
| `/arm_controller/follow_joint_trajectory` | action | `move_group` → joint trajectory controller | the planned joint trajectory (Goal A only) |
| `/joint_states` | topic | Gazebo → everyone | current joint positions |
| `/tf`, `/tf_static` | topic | `robot_state_publisher` → everyone | live + fixed transforms |
| `/robot_description` | parameter | `robot_state_publisher` → everyone | URDF text |

## Names from upstream that this exercise depends on

Same as exercise 19:

- Planning group: `arm`
- Tip / end-effector link: `link6_flange`
- Planning frame: `base_link`
- IK solver: `kdl_kinematics_plugin/KDLKinematicsPlugin`

Plus the planning scene topic / API:

- `PlanningSceneInterface::applyCollisionObjects` — from
  `moveit/planning_scene_interface/planning_scene_interface.hpp`.
- `moveit_msgs::msg::CollisionObject` — from `moveit_msgs`.
- `shape_msgs::msg::SolidPrimitive` — from `shape_msgs`.
