# The Four Terminals: Reference

This is a flat cheat-sheet you can keep open while running the demo. Each section is
"what this terminal does", "the command", "what success looks like", "what to do if it
breaks".

## Terminal 1 — Gazebo + Robot + Camera + Controllers

**What it is:** The virtual world. Loads the world file with the table and YCB objects,
spawns the myCobot 280 arm, spawns the standalone overhead RGBD camera, starts
ros2_control with the arm and gripper controllers.

**Command:**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py \
  world_file:=pick_and_place_demo.world \
  use_camera:=true \
  use_rviz:=false
```

**Success looks like:**
- A Gazebo window opens with the table, 5 YCB objects, the arm, and a camera tripod.
- Terminal prints `Loaded arm_controller` and `Loaded joint_state_broadcaster`.
- No red `[ERROR]` lines.

**If it breaks:**
- No table visible → the table fix wasn't applied or `mycobot_gazebo` wasn't rebuilt.
- No camera tripod → `use_camera:=true` flag was missed.
- Controllers don't load → ros2_control config missing; check `mycobot_moveit_config`
  was built.

## Terminal 2 — MoveIt `move_group`

**What it is:** MoveIt's central planner. Knows about the robot, loads planners (OMPL,
Pilz, STOMP), advertises planning + execution services, hooks into the controllers from
Terminal 1.

**Command:**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_moveit_config move_group.launch.py use_rviz:=false
```

**Success looks like:**
- Long startup log loading planners and plugins.
- A capabilities block printed: `apply_planning_scene_service`,
  `execute_trajectory_action`, `move_action`, etc.
- The line `ExecuteTaskSolutionCapability` appears in the loaded plugins (only if
  you installed `ros-jazzy-moveit-task-constructor-capabilities`).
- Final line: `You can start planning now!`

**If it breaks:**
- `ExecuteTaskSolutionCapability does not exist` error → install
  `ros-jazzy-moveit-task-constructor-capabilities` via apt, restart this terminal.
- `No such group 'arm'` errors later → SRDF wasn't loaded. Check `mycobot_moveit_config`
  is sourced.

## Terminal 3 — Perception (`get_planning_scene_server`)

**What it is:** Subscribes to the camera's point cloud and RGB topics. When called via
a ROS 2 service, it segments the cloud into a table + a list of objects and returns them
as MoveIt collision objects.

**Command:**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_mtc_pick_place_demo get_planning_scene_server.launch.py
```

**Success looks like:**
- Subscribes to `/camera_head/depth/color/points` and `/camera_head/color/image_raw`.
- Prints: `Get planning scene service created and ready to serve requests.`
- Then sits silent until Terminal 4 calls it.

**If it breaks:**
- `service '/get_planning_scene' not advertised` → wait a few seconds, or check the
  camera topic is actually publishing (`ros2 topic hz /camera_head/depth/color/points`
  should show ~30 Hz).
- `No valid plane model found` → the world doesn't have a table at the right height.
  See [../concepts/04-pick-place-task.md](../concepts/04-pick-place-task.md) for the
  table fix.

## Terminal 4 — The MTC Pick-and-Place Task (`mtc_node`)

**What it is:** Builds the task graph (current state → open gripper → approach → grasp →
lift → carry → lower → release → retreat → home) and plans + executes it.

**Command:**
```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch mycobot_mtc_pick_place_demo pick_place_demo.launch.py
```

**Success looks like:**
- Calls `get_planning_scene` service, receives the table + 6 collision objects.
- Picks `cylinder_1` as the target (similarity ~1.00).
- Many `Calling Planner 'OMPL'` lines as it plans each task stage.
- Final lines: `Task planning succeeded` → `Executing task solution` → arm moves in
  Gazebo.

**If it breaks:**
- `Execution skipped as per configuration` → set `execute: true` in
  `mtc_node_params.yaml`.
- Plans but gripper doesn't close → controller-name typo. Set
  `gripper_action_controller` (not `grip_action_controller`) in `mtc_node_params.yaml`.
- Re-running does nothing → kill the previous `mtc_node` with Ctrl+C in this terminal
  first. If the cylinder fell off the table, restart Terminal 1 too.

## The launch order matters

Launch in **this exact order**, waiting for each terminal's "ready" message before
starting the next:

1. **Terminal 1 (Gazebo)** → wait for `Loaded arm_controller`.
2. **Terminal 2 (move_group)** → wait for `You can start planning now!`.
3. **Terminal 3 (perception)** → wait for `service created and ready to serve requests`.
4. **Terminal 4 (mtc_node)** → arm moves shortly after.

Launching out of order will give you confusing partial errors:

- `move_group` before Gazebo → it'll start but can't find joint_states; the
  controller-loading step will fail.
- `mtc_node` before move_group → it'll wait forever on `service '/get_planning_scene'
  not advertised yet`.
- Anything that uses the camera before Gazebo is fully up → empty point cloud, no
  segmentation possible.

## Optional 5th terminal — Camera view

In a 5th terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run rqt_image_view rqt_image_view
```

Pick `/camera_head/color/image_raw` to see what the overhead camera sees. Helpful for
debugging "perception said it didn't find the cylinder" — you can confirm visually that
the cylinder is in the camera's field of view.

## Optional 6th terminal — RViz with everything

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 run rviz2 rviz2
```

Add displays for:
- **RobotModel** (current arm pose)
- **PlanningScene** (table + detected objects)
- **MarkerArray** on `/visualization_marker_array` (planned trajectories ghost-arm)
- **PointCloud2** on `/camera_head/depth/color/points` (raw camera data)
- **Image** on `/camera_head/color/image_raw` (RGB feed)

This is the densest debugging view — useful when something planned but didn't execute,
or when perception is finding things in unexpected places.

## Killing and restarting

- **To re-run the task only** → Ctrl+C Terminal 4, re-launch.
- **To re-run with a fresh scene** → Ctrl+C Terminals 4, 3, 1 (in that order), then
  re-launch all four from the top. Terminal 2 (move_group) can usually stay running.
- **To stop everything** → Ctrl+C each terminal. Check `ros2 node list` is empty
  before re-launching, otherwise stale nodes will conflict with new ones.

→ Next: [viewing-camera-output.md](viewing-camera-output.md) — quick recipes for
viewing the camera feed (and the perception output) in RViz or Gazebo.
