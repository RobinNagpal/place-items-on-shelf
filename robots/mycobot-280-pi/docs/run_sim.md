# Run — Step 2: myCobot 280 Pi in Gazebo Sim

This step launches Gazebo Harmonic with the arm spawned, ros2_control controllers loaded, the ROS↔Gazebo bridge running, and RViz attached. The launch file we use is **shipped by addison's `mycobot_gazebo` package** — we don't author our own.

> Prerequisite: Step 1 already works ([`run.md`](run.md)). If `ros2 launch mycobot_description robot_state_publisher.launch.py` doesn't open RViz, fix that first.

> Distro: addison's stack targets ROS 2 Jazzy + Gazebo Harmonic on Ubuntu 24.04 (Humble is also supported in the same repo). The instructions below assume Jazzy.

## 1. Make sure Gazebo + addison's deps are installed

If you ran `rosdep install --from-paths src --ignore-src -r -y --rosdistro jazzy` from [`install.md`](install.md) step 4, you're already done. If not, run that now. Confirm:

```bash
gz sim --version
# Expected: Gazebo Sim, version 8.x.x  (Harmonic)
```

## 2. Build the rest of addison's packages

For Step 2 you need `mycobot_gazebo` plus its dependencies. The simplest path is to build everything addison ships:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
colcon build --symlink-install
```

This takes a few minutes the first time (MoveIt is heavy). If you want to keep it tight to just what Step 2 needs:

```bash
colcon build --packages-up-to mycobot_gazebo --symlink-install
```

## 3. Source the workspace

```bash
source ~/ros2_ws/install/setup.bash
```

In every fresh terminal where you want to interact with the sim.

## 4. Launch

```bash
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py
```

What should happen:

1. A Gazebo Sim window opens with the `pick_and_place_demo.world` scene (a table, some objects).
2. The myCobot 280 with adaptive gripper appears, in its zero-joint pose.
3. RViz opens alongside, showing the same arm with the planning scene.
4. The terminal prints `Loaded joint_state_broadcaster` and `Loaded arm_controller`.

Useful launch arguments (all default to sensible values — only override when you want to):

```bash
# Start in an empty world instead of the pick-and-place scene
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py world_file:=empty.world

# Skip RViz (just Gazebo)
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py use_rviz:=false

# Skip Gazebo (RViz only, kinematic — useful for MoveIt planning testing without physics)
ros2 launch mycobot_gazebo mycobot.gazebo.launch.py use_gazebo:=false
```

## 5. Sanity-check the controllers (in a second terminal)

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 control list_controllers
# Expected: joint_state_broadcaster  active
#           arm_controller            active   (or whatever name addison uses)
```

## 6. Stopping it

`Ctrl-C` in the launch terminal kills Gazebo, RViz, the controllers, and the bridge together.

## Common issues

- **Gazebo opens but the arm is missing or sunk into the floor** — the spawn-entity ran before the world was ready. Stop everything, `Ctrl-C`, and re-launch. If it persists, check the launch terminal output for plugin load errors.
- **`Failed to load plugin gz_ros2_control-system`** — `gz_ros2_control` apt package isn't installed. Rerun `rosdep install ...` from [`install.md`](install.md).
- **Gazebo window is black or empty** — WSLg / GPU drivers issue, not addison's. Try `LIBGL_ALWAYS_SOFTWARE=1 ros2 launch mycobot_gazebo mycobot.gazebo.launch.py` to force software rendering.
- **MoveIt RViz panel shows red "no robot model"** — addison's RViz config expects the robot description to be on `/robot_description`. Confirm `ros2 topic echo /robot_description --once` returns XML. If it doesn't, robot_state_publisher didn't come up.

## What this gets you

After Step 2, you have a controllable arm in physics-aware simulation:

- The arm holds its pose against gravity.
- You can send `FollowJointTrajectory` goals via `/arm_controller/follow_joint_trajectory` and watch it move.
- The MoveIt 2 planning scene is wired up (proceed to Step 3 to actually plan + execute through MoveIt).
- The Gazebo↔ROS bridge is forwarding sim topics (clock, camera, etc.) into ROS.

## What's next

- **Step 3 (MoveIt 2)** — addison ships demos in `mycobot_moveit_demos`. Try `ros2 launch mycobot_moveit_demos <one of their demo launches>` once Step 2 is up.
- **Step 4 (HPLC scene)** — this is the project-specific bit *we* still have to author. Fork `mycobot_gazebo/worlds/pick_and_place_demo.world` into `worlds/hplc_autosampler.world` with a tray + vial rack, then point `world_file:=` at it.
- **Step 6 (pick-and-place)** — addison's `mycobot_mtc_pick_place_demo` is the template. Retarget the pick/place poses to vial-rack → tray-slot.
