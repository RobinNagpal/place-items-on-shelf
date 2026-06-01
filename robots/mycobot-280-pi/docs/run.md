# Run — myCobot 280 Pi viewer

This builds only the one package we need (`mycobot_description`) and launches a no-hardware RViz session where you can drag joint sliders to move the arm.

## Assumed layout

You have cloned this repo into a ROS 2 workspace, like the example you mentioned:

```
~/ros2_ws/
├── src/
│   └── place-items-on-shelf/          <- this repo
│       └── robots/
│           └── mycobot-280-pi/
│               ├── launch/view_in_rviz.launch.py
│               ├── rviz/view.rviz
│               └── src/mycobot_ros2/  <- git submodule
```

If you cloned it somewhere else, replace `~/ros2_ws` with your actual workspace path everywhere below.

## 1. First-time only — initialise the submodule

If you cloned the repo with `git clone --recurse-submodules`, skip to step 2.

Otherwise, from the repo root:

```bash
cd ~/ros2_ws/src/place-items-on-shelf
git submodule update --init --recursive
```

Confirm it worked:

```bash
ls robots/mycobot-280-pi/src/mycobot_ros2/mycobot_description/urdf/mycobot_280_pi/mycobot_280_pi.urdf
# Expected: the path is printed back.
```

## 2. Build `mycobot_description`

From the workspace root (not the repo root):

```bash
cd ~/ros2_ws
source /opt/ros/humble/setup.bash
colcon build --packages-select mycobot_description --symlink-install
```

`--symlink-install` means edits to URDFs / meshes show up without a rebuild. `--packages-select mycobot_description` keeps the build focused — we are **not** building MoveIt, Gazebo, the hardware driver, etc. for this step.

If the build finishes with `Summary: 1 package finished`, you are good.

## 3. Source the workspace

```bash
source ~/ros2_ws/install/setup.bash
```

You need to do this in every fresh terminal where you want to run the launch file. (Or add it to `~/.bashrc`.)

## 4. Launch the viewer

```bash
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/view_in_rviz.launch.py
```

Two windows open:

1. **RViz** showing the myCobot 280 Pi at exact hardware scale. Fixed frame is `g_base` (the arm's base flange). The grid is 50 mm cells so you can eyeball the 280 mm reach.
2. **joint_state_publisher_gui** with six sliders, one per joint. Drag a slider — the arm moves in RViz in real time.

Use the sliders to sanity-check:

- The arm reaches roughly 280 mm at full extension (matches Elephant Robotics' spec sheet).
- Joints stop at roughly ±165° on joints 1–5 and ±175° on joint 6.
- Meshes load — you should see the grey/silver myCobot links, not just bounding boxes.

## 5. Stopping it

`Ctrl-C` in the terminal kills RViz, the slider GUI, and the publisher in one shot.

## Common issues

- **"Fixed Frame [g_base] does not exist"** in RViz — `robot_state_publisher` hasn't published the URDF yet. Wait a second; if it persists, check the terminal for a URDF parse error.
- **Meshes appear as untextured grey shapes** — that's fine. The `.dae` files don't have textures.
- **No arm appears, just empty space** — almost always means the workspace wasn't sourced. Re-run `source ~/ros2_ws/install/setup.bash` in *this* terminal and re-launch.
- **`Package 'mycobot_description' not found`** — the `colcon build` step was skipped or failed. Re-run step 2.

## What this does NOT do

- No physics — RViz is a viewer, not a simulator. Gravity, collisions, contact don't apply. That's the next PR (Gazebo).
- No motion planning — no MoveIt yet.
- No real arm — no serial port, no `pymycobot`. This is purely a visualization smoke test.
