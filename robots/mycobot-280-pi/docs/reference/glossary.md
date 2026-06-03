# Glossary

Short definitions of every acronym and term you'll bump into while reading these docs
or the addison upstream repo. Roughly grouped by topic.

## ROS 2 fundamentals

- **ROS 2** — Robot Operating System (version 2). Not really an operating system; a
  framework of libraries + a message-passing system that lets multiple programs talk to
  each other on a robot.
- **Node** — one running program in the ROS 2 graph. Each terminal in our setup runs
  one (or sometimes a few) nodes.
- **Topic** — a named channel for one-way data flow. Like a radio frequency: many nodes
  can publish, many can subscribe. Example: `/joint_states`.
- **Service** — a request/response call between nodes, like calling a function over the
  network. Example: `/get_planning_scene` returns the current world model.
- **Action** — a long-running call with progress feedback and cancellation, like a
  service but for things that take more than a few milliseconds. Example: `/move_action`.
- **Frame (TF frame)** — a named coordinate system. The robot has dozens of them
  (one per joint). The world has one too. **TF** (or tf2) is the system that tracks
  the relationships between them so any node can ask "where is frame A relative to
  frame B right now?".
- **URDF** — Unified Robot Description Format. An XML file that describes the robot:
  links, joints, meshes, masses, collision shapes. The single source of truth for the
  robot's geometry.
- **SRDF** — Semantic Robot Description Format. A complementary XML file with the
  "human" information: which joints belong together as a "group" (e.g. "the arm"),
  named poses ("home", "ready"), self-collision pairs to ignore.
- **`.launch.py`** — A Python script (in ROS 2) that starts one or more nodes with
  specific parameters. Equivalent to a startup script.
- **colcon** — The build tool for ROS 2 packages. `colcon build` compiles everything;
  `--symlink-install` makes the installed copies symlinks back to source files so you
  don't have to rebuild after editing YAML/launch files.

## Simulation

- **Gazebo (Gazebo Sim / Gazebo Harmonic / Gazebo Garden)** — the 3D physics simulator.
  The newer versions are called "Gazebo Sim" (formerly "Ignition Gazebo"). Confusingly,
  there's also "Gazebo Classic" which is the old, deprecated one.
- **gz-sim** — short name / command for the new Gazebo. You'll see things like
  `gz-sim-physics-system` in world plugins.
- **SDF** — Simulation Description Format. XML files that describe worlds and models
  for Gazebo. Similar to URDF but with more sim-specific options.
- **World file** — an SDF file with a complete scene: ground, lighting, physics
  plugins, includes of models.
- **Model** — a single object (robot, table, can, anything). One SDF file per model.
- **Plugin** — Gazebo runtime extension. Physics, sensors, user commands, scene
  broadcasting — all plugins.

## Control

- **ros2_control** — the framework that connects high-level commands (like "move joint
  1 to angle X") to actual hardware drivers (or to Gazebo joint actuators in our case).
- **Controller** — a ros2_control component that owns one or more joints and accepts
  commands for them. Examples below.
- **Joint Trajectory Controller (JTC)** — accepts time-parametrised sequences of joint
  positions ("at t=0 be at angle A, at t=1.5 be at angle B"). The arm uses this.
- **`arm_controller`** — the JTC for the 6 arm joints in our setup.
- **`gripper_action_controller`** — a simple action-based controller for the gripper
  (open/close commands).
- **`joint_state_broadcaster`** — publishes `/joint_states` so the rest of the system
  knows the current joint angles.

## Motion planning (MoveIt)

- **MoveIt 2** — the motion-planning framework for ROS 2. Plans collision-free
  trajectories.
- **`move_group`** — the central MoveIt node. The one program you must always run.
- **Planning scene** — MoveIt's internal world model: the robot + everything around it
  that the arm should avoid hitting.
- **Collision object** — a single obstacle (or graspable item) in the planning scene,
  represented as a primitive shape (box, cylinder, sphere) or a mesh.
- **Attached object** — a collision object that's currently "attached" to the gripper.
  Treated as part of the arm for collision-checking purposes (so e.g. carrying a
  cylinder doesn't make the planner think the cylinder is colliding with the gripper).
- **OMPL** — Open Motion Planning Library. The default motion planner backend. Tries
  many randomized paths until one works.
- **RRTConnect** — a specific planning algorithm inside OMPL. Common default for
  manipulation arms. Fast and almost always finds a path if one exists.
- **Pilz** — an alternative planner for industrial-style motions (point-to-point, line,
  circle). Comes bundled but we don't use it.
- **STOMP** — another alternative planner that optimises a noisy initial trajectory.
  Comes bundled but we don't use it.
- **IK (Inverse Kinematics)** — "given that I want the gripper at this pose, what joint
  angles get me there?". MoveIt uses KDL by default.
- **FK (Forward Kinematics)** — the opposite: "given these joint angles, where is the
  gripper?".

## MoveIt Task Constructor

- **MTC** — short for MoveIt Task Constructor.
- **Task** — a graph of stages that together do something complex like "pick this up
  and put it over there".
- **Stage** — one node in the task graph. Examples: "open gripper", "approach object",
  "lift". Each stage has its own planning configuration.
- **Generator stage** — produces many candidate solutions (e.g. all viable grasp poses
  around an object). MTC picks the one that lets the rest of the task succeed.
- **Connecting stage** — plans a free-space move between two stages that don't
  individually constrain the path.
- **`ExecuteTaskSolutionCapability`** — a move_group plugin that MTC needs in order to
  push its planned trajectories through move_group for execution. Installed via apt.

## Perception

- **RGBD camera** — a camera that gives you color (R, G, B) plus depth (D) for each
  pixel. Real ones use IR pattern projection or time-of-flight; in simulation, Gazebo
  just renders depth perfectly from the scene geometry.
- **Point cloud** — a set of 3D points, usually one per pixel of a depth camera.
  Published as the topic `/camera_head/depth/color/points`.
- **PCL** — Point Cloud Library. A C++ library for processing point clouds (filtering,
  segmenting, clustering, shape fitting). Used by addison's perception node.
- **RANSAC** — RANdom SAmple Consensus. An algorithm for fitting a model (e.g. a plane,
  a cylinder) to noisy data by repeatedly trying random subsets and picking the model
  with the most inlier points.
- **Plane segmentation** — finding the dominant flat plane in a point cloud (used to
  identify the table).
- **Euclidean clustering** — grouping nearby points into clusters; once the table
  plane is removed, each remaining cluster is treated as one object.
- **Normal vector** — for each point in the cloud, the direction the local surface
  faces. Helps distinguish horizontal surfaces (normal pointing up) from vertical ones.

## Project-specific

- **addison's repo** — `automaticaddison/mycobot_ros2`. The simulation-focused upstream
  we use as a submodule.
- **elephantrobotics's repo** — `elephantrobotics/mycobot_ros2`. The manufacturer's
  upstream, focused on real hardware. Not yet integrated.
- **YCB** — Yale-CMU-Berkeley Object Set. A collection of standard household objects
  (cracker boxes, mustard bottles, coffee cans, etc.) used as benchmarks across
  robotics research. Our demo uses several.
- **`mycobot_280`** — the specific model name for the 6-DOF myCobot 280 arm (also
  called `mycobot_280pi` for the Raspberry-Pi-controlled version).
- **`cobot280_moveit_task`** — our custom minimal-MoveIt-task package. Lives at
  `robots/mycobot-280-pi/cobot280_moveit_task/`. Demonstrates the
  `MoveGroupInterface` path (the simpler alternative to MTC).
- **`mycobot_mtc_pick_place_demo`** — addison's MTC pick-and-place package. The full
  demo we're running, with all the fixes applied.

## Common acronyms list

| Acronym | Meaning                                       |
|---------|-----------------------------------------------|
| ROS     | Robot Operating System                        |
| RViz    | ROS Visualization                             |
| URDF    | Unified Robot Description Format              |
| SRDF    | Semantic Robot Description Format             |
| SDF     | Simulation Description Format                 |
| TF      | TransForms (the coordinate-frame system)      |
| OMPL    | Open Motion Planning Library                  |
| MTC     | MoveIt Task Constructor                       |
| IK      | Inverse Kinematics                            |
| FK      | Forward Kinematics                            |
| JTC     | Joint Trajectory Controller                   |
| DOF     | Degree(s) Of Freedom                          |
| PCL     | Point Cloud Library                           |
| RANSAC  | RANdom SAmple Consensus                       |
| RGBD    | Red Green Blue + Depth                        |
| YCB     | Yale-CMU-Berkeley (object set)                |
| KDL     | Kinematics and Dynamics Library               |
| Pi      | (in "myCobot 280 Pi") Raspberry Pi controller |
