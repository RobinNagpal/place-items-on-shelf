# v1_simple_pick — mobile-manipulator pick-and-place (Tier 2)

End-to-end demo: a differential-drive mobile base with an attached 3-DOF
arm and parallel-jaw gripper drives to a shelf, picks up a real-sized
soda can with a friction grasp, drives back, and places it on its onboard
tray.

## Architecture (Tier 2 — switched off the gz-sim per-joint controllers)

```
       /cmd_vel                              ┌────────────────────┐
       ─────────►  ros_gz_bridge ────────────►  Gazebo Harmonic    │
       /odom                                 │   store.sdf world   │
       ◄─────────                            │   pos_robot (URDF)  │
                                             │                    │
       /arm_controller/joint_trajectory      │   ┌──────────────┐ │
       ──────────────────────────────────────┼──►│gz_ros2_control│ │
       /gripper_controller/joint_trajectory  │   │ (in-process   │ │
       ──────────────────────────────────────┼──►│ controller_mgr│ │
       /joint_states                         │   │ + JTC effort  │ │
       ◄────────────────────────────────────-┤   │ PID per joint)│ │
                                             │   └──────────────┘ │
                                             └────────────────────┘
```

| Subsystem | What changed in Tier 2 |
|---|---|
| Arm control | gz-sim per-joint `JointPositionController` plugins → ros2_control + `joint_trajectory_controller` (effort interface, PID gains) hosted in-process by `gz_ros2_control`. |
| Arm targets | Hand-tuned `POSE_*` joint angles → **3-DOF analytical IK** (`ik.py`) from world-frame Cartesian targets. |
| Grasp | `DetachableJoint` runtime attach/detach hack → **friction-based grasp**: fingers are commanded to overshoot inside the can (target 0.018 m vs can radius 0.033 m), so the JTC's saturated effort becomes a sustained squeeze. Mu = 2.0 on the finger pads, 1.2 on the can. |
| Joint states | `gz-sim-joint-state-publisher` → `joint_state_broadcaster` (covers wheels as state-only via ros2_control). |
| URDF | Plain URDF → xacro (so `$(find pos_v1_bringup)/config/controllers.yaml` can be resolved to an absolute path at launch time). |
| Base + column | Mass and inertia bumped (12 kg base, 2 kg column) so the cantilevered arm can't pitch the base forward. |

## Packages

| Package | Role |
|---|---|
| `pos_v1_description` | Robot URDF (xacro). Defines the diff-drive base, 3-DOF arm, parallel-jaw gripper, and the `<ros2_control>` hardware block. |
| `pos_v1_bringup` | Gazebo world (`store.sdf`), launch (`sim.launch.py`), bridge config (`gz_bridge.yaml`), controller config (`controllers.yaml`). |
| `pos_v1_task` | Python pick-and-place node (`pick_and_place.py`) and the IK helper (`ik.py`). |

## Install / build

On WSL2 Ubuntu 24.04 with ROS 2 Jazzy:

```bash
# install ros2_control + the Gazebo plugin (only required if you don't have them)
sudo apt update
sudo apt install \
  ros-jazzy-ros2-control \
  ros-jazzy-ros2-controllers \
  ros-jazzy-joint-trajectory-controller \
  ros-jazzy-joint-state-broadcaster \
  ros-jazzy-gz-ros2-control \
  ros-jazzy-xacro
```

Then in your workspace root:

```bash
cd ~/ros2_ws
rosdep install --from-paths src --ignore-src -r -y
colcon build --packages-select pos_v1_description pos_v1_bringup pos_v1_task
source install/setup.bash
```

**Always run `colcon build` from the workspace root (`~/ros2_ws`), not
from inside `src/...`.** Otherwise colcon creates a second install tree
that Gazebo won't see, and you'll be silently running the old URDF.

## Run

Terminal 1:
```bash
ros2 launch pos_v1_bringup sim.launch.py
```

You should see the spawners load in order: `joint_state_broadcaster
loaded` → `arm_controller loaded` → `gripper_controller loaded`. If any
spawner times out, the controllers.yaml or the gz_ros2_control plugin
isn't being picked up (see "What breaks first" below).

Terminal 2 (after Gazebo is fully up and all three spawners report
success):
```bash
ros2 run pos_v1_task pick_and_place
```

Stages (sim-time):

| Stage | What you should see |
|---|---|
| INIT (5 + 2.5 s) | Arm settles into the stow pose, gripper opens |
| 1 (7.5 s)        | Robot drives ~1.5 m forward to the shelf |
| 2 (3 s)          | IK extends arm above the can (gripper horizontal) |
| 3 (3 s)          | Arm lowers; gripper surrounds the can |
| 4 (1.5 s)        | Fingers close — squeeze force builds up against the can |
| 5 (3 s)          | Arm lifts the can clear of the shelf |
| 6 (3 s)          | Arm folds back, gripper stays horizontal over the tray |
| 7 (7.5 s)        | Robot drives back, can held in the gripper by friction |
| 8 (3 s)          | Arm lowers to just above the tray |
| 9 (~2 s)         | Gripper opens, can drops a few cm onto the tray |
| 10 (3 s)         | Arm stows |

Total ≈ 42 sim-s. Wall-clock ≈ 90 s on WSL/Iris Xe (RTF ~0.45).

## Tunable knobs

### Cartesian targets (`pos_v1_task/pos_v1_task/pick_and_place.py`)

| Constant | Default | Meaning |
|---|---|---|
| `CAN_X`, `CAN_Z` | `1.88`, `0.5865` | Can centre (world) — keep in sync with `store.sdf` |
| `PRE_GRASP_WORLD` z | `CAN_Z + 0.06` | Approach height above can |
| `LIFT_WORLD` z | `CAN_Z + 0.15` | Clearance height after grasp |
| `CARRY_ROBOT_XZ` | `(0.20, 0.30)` | Gripper position above tray during transport (robot frame) |
| `PLACE_ROBOT_XZ` | `(0.20, 0.23)` | Drop height — 4.5 cm above tray top |
| `GRIPPER_GRASP` | `0.018` | Finger target — must be < can radius (0.033) for the friction grasp to grip |

If a target is unreachable, `ik_solve` raises `IKError` and the script
logs which target failed. Move the target closer to the shoulder or
choose a different gripper orientation `phi`.

### Controller PID gains (`pos_v1_bringup/config/controllers.yaml`)

Per-joint `p`, `i`, `d`, `i_clamp` for the joint_trajectory_controller's
internal PID. Symptoms and which knob to turn:

- Arm sags under gravity → increase `i_clamp` on the affected joint.
- Arm overshoots and oscillates → reduce `p`, increase `d`.
- Gripper can't hold the can (it slips down during the drive back) →
  increase finger `p` so saturated effort is higher, or lower
  `GRIPPER_GRASP` (more overshoot → bigger steady-state error → more
  effort).
- Joint wobbles even at rest → increase joint `damping` in the URDF.

### Friction (URDF `<gazebo reference="...">`)

`mu1`/`mu2` on `left_finger`, `right_finger`, and the soda can's
collision in `store.sdf`. Higher is grippier; if the can keeps slipping
out of the gripper even with the squeeze force pinned, raise these.

## What still doesn't work / future versions

- **No sensors.** No camera, no IMU, no lidar. The can's pose is
  hard-coded.
- **No navigation.** Drive is open-loop `cmd_vel` for a fixed sim
  duration. Robot would happily plough through an obstacle.
- **No motion planning.** The arm follows a fixed 9-pose IK script. No
  obstacle avoidance; if you put the shelf 5 cm closer to the robot,
  the arm would collide with it on the way down.
- **No closed-loop grasp.** No force or tactile feedback — we just
  assume the can is gripped after the trajectory completes.

These are the deferred items in the original Tier 3+ list:
- **v2_*sensors*** — add camera/lidar/IMU to the URDF.
- **v3_nav2** — SLAM-toolbox + Nav2 driving the base.
- **v4_perception** — OpenCV HSV detection of the can on the camera.
- **v5_moveit** — MoveIt 2 motion planning instead of hand-stitched poses.

## What breaks first time

This Tier-2 rebuild has not been tested on a real Gazebo machine. Watch
for these failures:

1. **`gz_ros2_control` plugin not found.** Make sure
   `ros-jazzy-gz-ros2-control` is installed (`apt list --installed | grep
   gz-ros2-control`). The plugin filename in the URDF is
   `gz_ros2_control-system`; if your apt-installed name is different,
   the Gazebo console will say `Could not load plugin library`.
2. **Controllers fail to spawn.** Symptom: `arm_controller` spawner
   times out. Cause is usually one of:
     - `controllers.yaml` path didn't get resolved by xacro — check
       `ros2 param dump /controller_manager` and confirm that the
       joint and gain names you expect are listed.
     - PID gain key names don't match controllers.yaml schema (the
       schema is `gains.<joint_name>.{p,i,d,i_clamp,ff_velocity_scale}`).
3. **Arm sags during STOW.** PID integral hasn't built up yet. Increase
   `i_clamp` on the offending joint (in `controllers.yaml`) or wait
   longer in INIT.
4. **Gripper drops the can during the drive back.** Friction grasp is
   inherently fragile. First try: increase finger `p` to 600,
   `i_clamp` to 10. Second try: bump `mu1`/`mu2` on the fingers to 3.0.
   Third try: reduce `DRIVE_SPEED` so accelerations during start-of-drive
   are gentler.
5. **Arm IK fails on a target.** The Python log prints `IK failed:
   ...`. Either the target is out of reach (move it closer) or `phi`
   forces a wrist angle outside ±2.0 rad (try `phi=0` instead of
   `-pi/2`, or vice versa).
