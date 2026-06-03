# Viewing the Camera Output

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

## Bonus — viewing the Planning Scene (the green object shapes)

This is the view that shows what **perception identified**: the table and each
detected object as a simple green shape (box or cylinder) overlaid in the world.
It's the most satisfying view because you can literally watch perception "see" each
object.

### Steps

1. Make sure you have **Terminals 1, 2, 3** running — Gazebo, MoveIt's `move_group`,
   and the perception server. (Terminal 4 is what *triggers* perception; you can use
   it, or trigger manually — both work.)
2. Open RViz in a separate terminal (`ros2 run rviz2 rviz2`).
3. Fixed Frame → `base_link` (same as Approach 1).
4. Click **Add** → **By display type** tab → expand
   **moveit_ros_visualization** → pick **PlanningScene** → **OK**.
5. In the Displays panel, find the new **PlanningScene** entry → expand **Scene
   Geometry** → set **Scene Alpha** to about `0.5` (makes the green shapes
   semi-transparent so they don't hide things underneath).
6. Run Terminal 4 as normal to execute the pick-and-place task. Within a couple of
   seconds you'll see in RViz:
   - A thin green slab where the table is.
   - Several green boxes for the YCB objects.
   - A tall thin green cylinder right where the red cylinder is.
   - The arm moving through the pick sequence as MTC executes.

The tall green cylinder appearing on top of the red cylinder is the visual proof of
"perception identified the cylinder". Toggle the PlanningScene display off and on to
see the green shapes appear and disappear.

### Save this layout too

Once you've got RViz set up with Image + PlanningScene + (optionally) RobotModel,
**File → Save Config As...** to e.g. `~/mycobot_full_view.rviz`. Re-open later with
`ros2 run rviz2 rviz2 -d ~/mycobot_full_view.rviz`.

→ For the explanation of *how* perception is producing those green shapes (without
any AI), see **[../deep-dives/how-perception-works.md](../deep-dives/how-perception-works.md)**.

→ Next: [../reference/glossary.md](../reference/glossary.md) — terms reference.
