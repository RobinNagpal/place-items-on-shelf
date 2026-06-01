# Run — Step 2: myCobot 280 Pi in Gazebo Sim

This launches Gazebo Harmonic, spawns the arm at the origin, and starts a `joint_trajectory_controller` so you can command joint positions and watch the arm move in physics-aware simulation.

> Prerequisite: Step 1 already works (`view_in_rviz.launch.py` opens an RViz with the arm). If Step 1 doesn't work yet, fix that first — see [`run.md`](run.md).

> Distro: this folder targets ROS 2 Jazzy + Gazebo Harmonic on Ubuntu 24.04. The Humble path (Ubuntu 22.04) would use Gazebo Fortress and `ign_ros2_control` instead — not covered here yet.

## 1. Install the Gazebo + ros2_control bits

```bash
DISTRO=jazzy
sudo apt update
sudo apt install -y \
  ros-${DISTRO}-ros-gz \
  ros-${DISTRO}-gz-ros2-control \
  ros-${DISTRO}-ros2-control \
  ros-${DISTRO}-ros2-controllers \
  ros-${DISTRO}-joint-state-broadcaster \
  ros-${DISTRO}-joint-trajectory-controller \
  gz-harmonic
```

Confirm Gazebo Harmonic is on PATH:

```bash
gz sim --version
# Expected: Gazebo Sim, version 8.x.x   (Harmonic)
```

If `gz sim` is not found, the `gz-harmonic` package didn't install — check the apt output and the Ubuntu version (`lsb_release -a` should say 24.04).

## 2. Rebuild

You already have `mycobot_description` built from Step 1. No new packages to build for Step 2 — the simulation files live outside any colcon package and are loaded by path at launch time. But re-source the workspace in any fresh terminal:

```bash
cd ~/ros2_ws
source /opt/ros/jazzy/setup.bash
source install/setup.bash
```

## 3. Launch

```bash
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/sim_in_gazebo.launch.py
```

What should happen:

1. A Gazebo Sim window opens with a grey ground plane.
2. The myCobot 280 Pi appears 5 cm above the ground, in its zero-joint pose.
3. The terminal prints `Loaded joint_state_broadcaster` and then `Loaded arm_controller`.
4. `ros2 topic list` (in a second terminal) should show `/joint_states`, `/robot_description`, `/arm_controller/...`, etc.

If any of those don't happen, see "Common issues" below.

## 4. Send a test trajectory (in a second terminal)

Source the workspace in the new terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
```

Send a single goal that moves all six joints to ~0.3 rad and back:

```bash
ros2 action send_goal /arm_controller/follow_joint_trajectory \
  control_msgs/action/FollowJointTrajectory -f \
  "{
    trajectory: {
      joint_names: [joint2_to_joint1, joint3_to_joint2, joint4_to_joint3, joint5_to_joint4, joint6_to_joint5, joint6output_to_joint6],
      points: [
        { positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 1 } },
        { positions: [0.3, 0.3, 0.3, 0.3, 0.3, 0.3], time_from_start: { sec: 3 } },
        { positions: [0.0, 0.0, 0.0, 0.0, 0.0, 0.0], time_from_start: { sec: 5 } }
      ]
    }
  }"
```

The arm in Gazebo should swing to the second pose, hold, then return. The `-f` flag tells the CLI to suppress the goal feedback flood.

## 5. Open RViz alongside (optional)

In a third terminal:

```bash
source /opt/ros/jazzy/setup.bash
source ~/ros2_ws/install/setup.bash
ros2 launch ~/ros2_ws/src/place-items-on-shelf/robots/mycobot-280-pi/launch/view_in_rviz.launch.py
```

Note: this will spawn its own `joint_state_publisher_gui`, which **publishes joint commands of its own** and will fight the simulation. Close that GUI window if you want RViz to mirror the sim — `/joint_states` from the sim will still reach RViz via `robot_state_publisher`.

## 6. Stopping it

`Ctrl-C` in the launch terminal kills Gazebo, the controllers, and the publisher together.

## Common issues

- **`Failed to load plugin gz_ros2_control-system`** — `ros-jazzy-gz-ros2-control` isn't installed or your `LD_LIBRARY_PATH` is wrong. Re-run the apt install in step 1 and open a fresh shell.
- **`Could not find the parameter file ...controllers.yaml`** — the xacro arg substitution didn't run, usually because the launch is being run on a path where the file moved. The launch resolves the path from `__file__`; symlinks are fine.
- **Arm appears in Gazebo but does not respond to trajectory goals** — the `gz_ros2_control` plugin probably failed silently. Check the Gazebo terminal output for plugin errors. Confirm `/controller_manager/list_controllers` reports both controllers as `active`.
- **Arm spawns and immediately falls through the floor / wobbles** — gravity is still on. Check `worlds/empty.sdf` has `<gravity>0 0 0</gravity>` (it should — that's the point of this step).
- **`ros2 action send_goal` complains about an unknown action type** — `control_msgs` is missing. `sudo apt install -y ros-jazzy-control-msgs`.
- **Gazebo window is black or empty** — usually a WSLg / GPU drivers issue, not us. Try `LIBGL_ALWAYS_SOFTWARE=1 ros2 launch ...` to force software rendering.

## What this does NOT do (intentionally — those are Steps 3+)

- No MoveIt — trajectories must be hand-authored or scripted; no collision-aware planning yet.
- No gripper actuation — gripper joints aren't in the controller config.
- No scene objects — empty ground plane only. The HPLC autosampler tray and vial racks come in Step 4.
- No camera / vision — Step 5.
- No real hardware bridge — Step 7.

## What gravity-off costs us

Disabling gravity is a deliberate workaround for the vendor URDF having no `<inertial>` tags. It means:

- The arm cannot fall, droop, or feel the weight of an object — useful for visualizing motion, useless for grasp force feedback.
- Self-collisions and contact dynamics are still simulated by the physics engine, just without gravitational loading.
- "Pick" and "place" against passive objects won't be physically meaningful until inertials land.

The follow-up to this step is "add inertials, flip gravity back on" — not a separate Step 3, just a refinement of Step 2.
