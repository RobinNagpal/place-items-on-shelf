# v1_simple_pick — first runnable scaffold

This is the **minimum** runnable demo of the place-items-on-shelf project. It proves the toolchain (ROS 2 Jazzy + Gazebo Harmonic + Python) is working end-to-end. Future versions live in sibling folders (`v2_*`, `v3_*`, …); we will not modify this one.

## What v1 does

A boxy mobile robot with a flat onboard tray spawns in a simple "store" world. The world contains a shelf with three red bottles on it. A Python task node drives the robot:

```
start → forward to shelf → "pick" (teleport bottle_1 onto tray) → backward to start (bottle tracks the tray) → "place" (drop bottle next to start) → done
```

There is **no real arm or gripper** in v1. The "pick" is faked by calling Gazebo's `/world/store/set_pose` service to teleport `bottle_1` (the middle shelf bottle) onto the robot's tray. While the robot drives back, the script re-snaps the bottle to the moving tray every 0.5 sim-seconds (using `/odom` for robot pose). The "place" is another teleport — the bottle is moved to a fixed spot next to the start and gravity drops it the last ~0.1 m. A real grasp (3-DOF arm + ros2_control + detachable joint) lands in v2/v3.

The goal here is only:

1. Verify Gazebo Harmonic launches a custom world.
2. Verify our URDF spawns and is driveable via `/cmd_vel`.
3. Verify a Python ROS 2 node can command the robot through a sequence **and** manipulate world entities via Gazebo's service interface.

If all three work, the scaffolding is correct and we have a foundation for v2.

## Packages

| Package | Role |
|---|---|
| `pos_v1_description` | Robot URDF (mobile base + tray + cosmetic arm) |
| `pos_v1_bringup` | Gazebo world, launch file, ROS↔Gazebo bridge config |
| `pos_v1_task` | Python node that runs the open-loop pick-and-place sequence |

## Build (on WSL2 Ubuntu 24.04 with ROS 2 Jazzy)

Assuming your workspace is `~/ros2_ws` and this repo is cloned at `~/ros2_ws/src/place-items-on-shelf/`:

```bash
# Symlink so colcon discovers the v1 packages
ln -s ~/ros2_ws/src/place-items-on-shelf/v1_simple_pick ~/ros2_ws/src/pos_v1

# Build only the v1 packages
cd ~/ros2_ws
rosdep install --from-paths src/pos_v1 --ignore-src -r -y
colcon build --packages-select pos_v1_description pos_v1_bringup pos_v1_task
source install/setup.bash
```

`colcon build` also works without the symlink — it scans recursively — but the symlink keeps the `--packages-select` line short.

## Run

In **terminal 1**:
```bash
source ~/ros2_ws/install/setup.bash
ros2 launch pos_v1_bringup sim.launch.py
```

This brings up Gazebo with the store world, spawns the robot, and starts the ROS↔Gazebo bridge. You should see a Gazebo window with a blue boxy robot, a brown shelf, and three red cylinders ("bottles") on the shelf.

In **terminal 2** (after Gazebo is fully loaded):
```bash
source ~/ros2_ws/install/setup.bash
ros2 run pos_v1_task pick_and_place
```

The robot drives forward ~1.5 m, the middle bottle teleports onto the tray, the robot drives back carrying the bottle, drops it next to the start, and prints `Done.`. Total runtime ~20 sim-seconds (wall-clock will be ~45 s on WSL/Iris Xe).

## Tunable knobs

Top of `pos_v1_task/pos_v1_task/pick_and_place.py`:

| Constant | Default | Meaning |
|---|---|---|
| `DRIVE_SPEED` | `0.2` | Linear m/s for forward/back motion |
| `DRIVE_TIME_S` | `7.5` | **Sim** seconds to drive forward (and back). At 0.2 m/s this is ~1.5 m. |
| `PICK_PAUSE_S` | `3.0` | **Sim** seconds to pause at shelf (during which bottle is re-snapped to tray) |
| `PLACE_PAUSE_S` | `1.5` | **Sim** seconds to wait after dropping the bottle |
| `STARTUP_DELAY_S` | `2.0` | **Sim** seconds to wait before commanding motion |
| `PICK_BOTTLE` | `bottle_1` | Which shelf bottle to "pick" (entity name from `store.sdf`) |
| `TRAY_Z_WORLD` | `0.285` | World-frame z to teleport bottle to (tray top + bottle half-length) |
| `PLACE_POSE_XY` | `(-0.5, 0.3)` | Where the bottle is "placed" relative to world origin |
| `CARRY_SYNC_PERIOD_S` | `0.5` | Re-teleport period while carrying (smaller = less visual lag, more subprocess overhead) |

All durations are in **simulated seconds**, not wall-clock — the task node runs with `use_sim_time=True` so its timing tracks Gazebo's `/clock`. On WSL2 + Iris Xe Gazebo typically runs at 40-60% real-time, so wall-clock timing would leave the robot short of the shelf.

## What we expect to break first time

Honest list — this scaffolding is unverified (written without a Gazebo Harmonic machine to test on). Likely issues you may hit:

1. **Caster scraping.** The caster is a fixed-joint sphere; depending on Gazebo friction defaults the robot may resist turning. If the diff-drive doesn't move smoothly, lower friction in the SDF or replace caster with a free ball-joint sphere.
2. **Topic naming mismatch.** Gazebo Harmonic's `DiffDrive` plugin defaults the cmd_vel topic to `/model/<model_name>/cmd_vel`. The bridge config assumes the model name is exactly `pos_robot` (matches the launch file's `-name` argument). If you rename the model, update `config/gz_bridge.yaml`.
3. **Sim time clock.** The task node sets `use_sim_time=True` and reads `/clock` from Gazebo via the bridge. If `/clock` is missing for some reason, the task will loop forever on the first `wait_sim_seconds` call. Verify with `ros2 topic hz /clock` — should be ~1000 Hz.
4. **`gz` vs `ign` commands.** All commands here assume Gazebo Harmonic (`gz` CLI). If you accidentally have Gazebo Fortress installed, swap to `ign`. The pick/place teleport calls `gz service` as a subprocess — if `gz` is not on PATH for the user running the task, the teleport silently no-ops and the bottle will stay on the shelf.
5. **Bottle teleport jitter.** The bottle is re-teleported via subprocess every 0.5 sim-seconds while carrying. Each `gz service` call blocks the spin loop for ~100-300 ms, so cmd_vel publishing slows briefly. DiffDrive holds the last command, so the robot still drives smoothly — but if you change `CARRY_SYNC_PERIOD_S` to something very low (e.g. 0.05) you'll see motion stutter.

Report any of these and we'll fix in a follow-up PR.

## Where we go next (proposed)

- **v2_arm_dynamics** — replace the cosmetic arm with a 3-DOF arm + gripper, driven via `ros2_control`. The task script moves arm joints during the "pick" pause instead of just sleeping.
- **v3_kinematic_grasp** — replace the `set_pose` teleport with Gazebo's detachable-joint plugin so the gripper actually "grasps" a bottle and physics carries it on the tray.
- **v4_nav2** — replace open-loop `cmd_vel` with Nav2 navigation to known shelf waypoints.
- **v5_perception** — replace Gazebo ground-truth pose with OpenCV HSV detection on an RGB-D camera.
- **v6_moveit** — replace hand-coded joint trajectories with MoveIt 2 motion planning.

Each is a separate sibling folder so this v1 stays stable as a "hello world" baseline.
