# 07 — Viewing the Camera Output

Two short recipes for "I just want to see what the camera is seeing". Both work with
only **Terminal 1 (Gazebo)** running — you don't need MoveIt or the task to be up.

## Approach 1 — RViz (the standard way)

This is the option most ROS projects use because RViz is the standard visualization
tool. Once set up, you can keep the same window open and add more displays later
(point cloud, robot, planned trajectory, etc.) without restarting anything.

### Steps

1. Open a new terminal and launch RViz:
   ```bash
   source /opt/ros/jazzy/setup.bash
   source ~/ros2_ws/install/setup.bash
   ros2 run rviz2 rviz2
   ```
2. In the **Displays** panel (left side) → **Global Options** → change **Fixed Frame**
   from `map` to **`base_link`**. The red "Frame [map] does not exist" error
   disappears once you do this.
3. Click **Add** (bottom-left of the panel) → **By topic** tab → scroll to
   **`/camera_head/color/image_raw`** → expand it → pick **Image** → **OK**.
4. A floating Image panel opens showing the live camera feed.

### Save your setup so you don't repeat steps 2–3 every time

- Menu bar: **File → Save Config As...** → save somewhere convenient, e.g.
  `~/mycobot_camera_view.rviz`.
- Next time launch with that config preloaded:
  ```bash
  ros2 run rviz2 rviz2 -d ~/mycobot_camera_view.rviz
  ```
  RViz reopens exactly the way you left it.

## Approach 2 — Gazebo's built-in Image Display plugin

Gazebo Sim can show you what any camera in the scene is rendering, right inside the
Gazebo window. Doesn't use ROS topics at all (reads from Gazebo's internal sensor
sim), so it's a quick way to confirm "is the camera even rendering anything?".

### Steps

1. In the Gazebo window, click the **three vertical dots** at the **top-right** to
   open the plugin/component menu.
2. Scroll down the list, find **Image Display** (sometimes called Camera Display) →
   click it. A new panel appears in the Gazebo sidebar.
3. In that panel, pick the camera's gz-side topic from the dropdown (the only one for
   our setup).
4. The live camera view appears inside Gazebo.

### When to use which

- **RViz** — when you want to view the camera *plus* see other things alongside it
  (point cloud, robot model, planning scene, etc.). Standard practice; what you'll
  reach for most of the time.
- **Gazebo's Image Display** — when you just want a quick "is the simulated camera
  rendering?" check without opening a second window. Useful for early troubleshooting.

Both are non-disruptive — you can have both open at once, neither affects the running
simulation.
