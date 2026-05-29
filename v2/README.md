# v2 — backroom map

Second iteration of the place-items-on-shelf project. Unlike `v1_simple_pick/`,
which executes a hardcoded scripted sequence, v2 is being built up as a proper
implementation. The first step is the environment itself — a Gazebo Harmonic
world modelling the backroom/storeroom of a grocery store (not the customer-
facing shop floor).

## What this world represents

A small backroom where bulk overstock is kept on pallet racking. The robot
will start at a marked home position, drive to a shelf, retrieve a product,
return to a marked drop station near the door, and come back to home. This
file only defines the **environment**; the robot, sensing, planning, and
control are deliberately not part of this commit.

No products are placed on the shelves yet, and there are no obstacles in
the aisle.

## Room layout

Floor origin is at the centre of the room. X is right, Y is forward
(towards the back wall), Z is up.

```
 y = +4 ┌───────────────────────────────────────────┐
        │ ▓ rack_left  ▓  rack_center  ▓ rack_right ▓│  (north wall)
        │                                            │
        │                                            │
 x=-5   │                  (aisle)                   │  x=+5
        │                                            │
        │                                            │
        │  ◯ robot_home          ▣ drop_station      │
 y = -4 └─────────────────┐  door  ┌─────────────────┘
                          │ 1.8m  │
                       (south wall)
```

| Element                | Position (x, y, z) | Size (x × y × z) | Notes                              |
| ---------------------- | ------------------ | ---------------- | ---------------------------------- |
| Room (internal)        | centre 0, 0, 1.5   | 10.0 × 8.0 × 3.0 | Walls 0.2 m thick                  |
| Door opening           | x ∈ [-0.9, +0.9]   | 1.8 × — × 2.4    | South wall, ground to lintel       |
| Rack left              | -3.5, +3.2, 1.2    | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Rack center            | 0.0, +3.2, 1.2     | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Rack right             | +3.5, +3.2, 1.2    | 2.5 × 0.8 × 2.4  | 3 horizontal decks                 |
| Robot home marker      | -3.0, -3.0, 0      | 1.0 × 1.0 × —    | Yellow floor decal                 |
| Drop station           | +2.5, -3.0, 0.25   | 1.0 × 0.8 × 0.5  | Green-topped packing table         |

The three pallet racks each have four steel uprights at the corners
(0.08 × 0.08 m square posts) and three horizontal decks at z = 0.10, 1.10,
and 2.10 m — typical low / mid / top tiers for storing bulk product cases.

## The robot

`pos_v2_description/` defines a small differential-drive AGV that spawns
at the yellow home marker, facing the racks. It carries a 2D lidar and an
IMU — enough sensing for SLAM and Nav2 in the next iteration. No arm yet;
placement on the shelf will be modelled as a payload-drop interaction.

| Spec               | Value                                  |
| ------------------ | -------------------------------------- |
| Base                | 0.40 × 0.40 × 0.20 m, ~5 kg            |
| Drive               | Two-wheel differential + front caster  |
| Wheel radius        | 0.08 m                                 |
| Wheel separation    | 0.44 m                                 |
| Lidar               | 360° 2D, 12 m range, 10 Hz (`gpu_lidar`) |
| IMU                 | 100 Hz                                 |
| Sim plugin          | `gz::sim::systems::DiffDrive`          |
| Control interface   | `geometry_msgs/Twist` on `/cmd_vel`    |

Topics bridged to ROS 2 (see `pos_v2_description/config/bridge.yaml`):
`/cmd_vel` (in), `/odom`, `/scan`, `/imu`, `/joint_states`, `/tf`,
`/clock`.

## SLAM (map-building)

`pos_v2_navigation/` adds `slam_toolbox` (online async mode) so we can
build a 2D occupancy grid of the backroom by driving the robot around
with teleop. The map produced here is the input for the Nav2 PR that
comes next.

| File                                              | Purpose                                                       |
| ------------------------------------------------- | ------------------------------------------------------------- |
| `pos_v2_navigation/launch/slam.launch.py`         | World + robot + `slam_toolbox` + RViz preset (one launch).    |
| `pos_v2_navigation/config/slam_toolbox_async.yaml`| `slam_toolbox` tuning (frames, scan topic, loop closure).     |
| `pos_v2_navigation/config/slam.rviz`              | RViz preset with Map, LaserScan, TF, RobotModel pre-added.    |
| `pos_v2_navigation/maps/README.md`                | How to save the built map to disk for Nav2 to consume later.  |

## Files

- `pos_v2_bringup/worlds/backroom.sdf` — the world definition.
- `pos_v2_bringup/launch/backroom.launch.py` — launches Gazebo Harmonic
  with the world only.
- `pos_v2_description/urdf/robot.urdf.xacro` — the v2 robot URDF/xacro.
- `pos_v2_description/config/bridge.yaml` — `ros_gz_bridge` topic map.
- `pos_v2_description/launch/spawn_robot.launch.py` — launches the world
  + spawns the robot + starts `robot_state_publisher` and the bridge.
- `pos_v2_navigation/launch/slam.launch.py` — world + robot + SLAM + RViz.
- `pos_v2_navigation/config/slam_toolbox_async.yaml` — SLAM parameters.
- `pos_v2_navigation/config/slam.rviz` — RViz preset for SLAM.
- `pos_v2_bringup/package.xml`, `CMakeLists.txt` — ament_cmake metadata.
- `pos_v2_description/package.xml`, `CMakeLists.txt` — ament_cmake
  metadata for the robot package.
- `pos_v2_navigation/package.xml`, `CMakeLists.txt` — ament_cmake
  metadata for the navigation package.

## How to view it

After `colcon build --symlink-install` from the workspace root and
sourcing the install:

```bash
# World only (no robot):
ros2 launch pos_v2_bringup backroom.launch.py

# World + robot + bridge:
ros2 launch pos_v2_description spawn_robot.launch.py

# World + robot + SLAM (build a map):
ros2 launch pos_v2_navigation slam.launch.py
```

To drive the robot, from a second sourced terminal:

```bash
ros2 run teleop_twist_keyboard teleop_twist_keyboard
# (or, lower-level: ros2 topic pub /cmd_vel geometry_msgs/Twist ...)
```

When the map in RViz looks complete, save it:

```bash
cd ~/ros2_ws/src/place-items-on-shelf/v2/pos_v2_navigation/maps
ros2 run nav2_map_server map_saver_cli -f backroom
```

## Next steps (not in this commit)

1. Run SLAM, drive around, save `maps/backroom.pgm` + `backroom.yaml`.
2. Add Nav2: `nav2_params.yaml`, `nav2.launch.py` that loads the saved
   map and brings up AMCL + planners + costmaps + behavior tree.
3. Add a tiny `nav_client` Python node + a `locations.yaml` so we can
   call `nav_to("rack_center")` instead of typing raw goal poses.
4. Add `pos_v2_task/` — a behaviour-tree task that drives home → shelf
   → drop → home as closed-loop ROS 2 actions.
5. Decide on a manipulator style (lift mast vs articulated arm vs
   attach plugin) and add it.
6. Populate the shelves with parameterised product models.
