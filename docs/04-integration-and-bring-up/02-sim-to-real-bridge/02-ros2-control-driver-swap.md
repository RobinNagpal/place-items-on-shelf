# 02-b — `ros2_control` Driver Swap

You have one URDF, one MoveIt config, one task code base. The
*only* thing that should change when you go from sim to real is the
**hardware interface plugin** underneath `ros2_control`. Everything
above it stays the same.

This is the magic of `ros2_control`. Use it.

## What `ros2_control` actually is

A framework that splits "robot driver" into two parts:

- **Hardware interface plugin** — talks to the real (or simulated)
  motors. Provides "read joint state" and "write joint command"
  methods.
- **Controller** — converts a higher-level goal
  (`FollowJointTrajectory`, gripper close, velocity command) into
  the joint-level reads/writes the plugin handles.

MoveIt and your task code only ever talk to **controllers**. They
have no idea whether the hardware below is sim or real.

So the swap is: change the hardware-interface plugin, keep the
controller list identical.

## What you need before this step

- A shared URDF + frame setup from [step 1](01-shared-urdf-and-frames.md).
- A working sim cell using the sim hardware interface (e.g.
  `gz_ros2_control/GazeboSimSystem`).
- Real hardware physically powered, networked, and reachable.
- The vendor's `ros2_control` plugin or ROS 2 driver installed.

## The two configs

You keep two YAMLs in your bring-up package:

### `controllers_sim.yaml`

```yaml
controller_manager:
  ros__parameters:
    update_rate: 100  # Hz, sim can usually keep up easily

joint_trajectory_controller:
  type: joint_trajectory_controller/JointTrajectoryController
  ros__parameters:
    joints: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]
    command_interfaces: [position]
    state_interfaces: [position, velocity]

gripper_controller:
  type: position_controllers/GripperActionController
  ros__parameters:
    joint: gripper_joint
```

### `controllers_real.yaml`

```yaml
controller_manager:
  ros__parameters:
    update_rate: 500  # Hz, match the real driver's preferred rate

joint_trajectory_controller:
  type: joint_trajectory_controller/JointTrajectoryController
  ros__parameters:
    joints: [joint_1, joint_2, joint_3, joint_4, joint_5, joint_6]
    command_interfaces: [position]
    state_interfaces: [position, velocity, effort]   # real arms expose effort

gripper_controller:
  type: position_controllers/GripperActionController
  ros__parameters:
    joint: gripper_joint
```

The **controller names and types are identical.** The update rate and
the available state interfaces differ. That's enough for the rest of
the stack to be unaware.

## The hardware plugin choice

In the URDF (specifically inside the `<ros2_control>` block), you
declare which hardware plugin to use. Make this a xacro argument:

```xml
<ros2_control name="hw" type="system">
  <xacro:if value="$(arg sim)">
    <hardware>
      <plugin>gz_ros2_control/GazeboSimSystem</plugin>
    </hardware>
  </xacro:if>
  <xacro:unless value="$(arg sim)">
    <hardware>
      <plugin>ur_robot_driver/URPositionHardwareInterface</plugin>
      <param name="robot_ip">192.168.1.100</param>
    </hardware>
  </xacro:unless>
  <!-- joints -->
</ros2_control>
```

Pass `sim:=true` or `sim:=false` from your launch file. Same URDF,
same controllers, different plugin.

## Common vendor plugins

| Arm | Plugin / driver |
|-----|----------------|
| Universal Robots e-series | `ur_robot_driver` (official) |
| Franka FR3 | `franka_ros2` (official) |
| Kinova Gen3 | `ros2_kortex` (official) |
| Doosan / Aubo / JAKA / Techman | vendor-supplied ROS 2 driver |
| FANUC / ABB / KUKA / Yaskawa | community drivers, partial coverage |
| Elephant Robotics myCobot 280 Pi | `mycobot_ros2` |

If your arm isn't there, your driver wraps the vendor SDK in a
`ros2_control` `SystemInterface`. Read the
[`ros2_control` writing-a-hardware-component](https://control.ros.org/master/doc/ros2_control/hardware_interface/doc/writing_new_hardware_component.html)
guide and copy from `ur_robot_driver` as a template.

## Bring it up — the first time

1. **Power on** the arm. Confirm the controller / pendant says
   "ready / running."
2. **Ping the arm** from your IPC: `ping <robot_ip>` — must succeed.
3. **Launch with the real config:**
   ```
   ros2 launch <project>_bringup real.launch.py
   ```
4. **Watch the logs.** Driver should report "connected" and start
   publishing `/joint_states`.
5. `ros2 topic echo /joint_states` — confirm the joints update when
   you nudge the real arm by hand (with the brakes off, in teach
   mode).
6. `ros2 control list_controllers` — both controllers should be
   `active`.
7. **Drive the joints by hand from MoveIt's RViz panel** at a
   *very* slow speed first.

If steps 4–7 pass, the swap worked. Your existing task code can now
run against real, unchanged.

## Speed scaling for the first runs

Before letting your task code drive the real arm, **scale velocity**
in the controller config:

```yaml
joint_trajectory_controller:
  ros__parameters:
    constraints:
      stopped_velocity_tolerance: 0.05
      goal_time: 0.6
    speed_scaling: 0.25   # arm runs at 25% of trajectory speed
```

Run at 25% for the first day. Step up gradually. See
[step 4](04-shadow-mode-and-slow-speeds.md) for the full protocol.

## Output of this step

```
Sim plugin:                 gz_ros2_control / mujoco_ros2_control / ___
Real plugin:                ur_robot_driver / franka_ros2 / ___
Plugin version:             ___ (commit / apt version)
Controllers (sim, real):    JointTrajectoryController, GripperActionController
Controller update rate:     sim ___ Hz, real ___ Hz
Real arm IP:                ___
Connection verified:        yes / no
joint_states publishing on real: yes / no
list_controllers shows active: yes / no
RViz Plan + Execute on real:  yes / no — at speed scaling ___ %
```

## Common mistakes

1. **Different controller names in sim and real.** Then your code
   has to switch on environment. Don't — make them identical.
2. **Different joint *order* between URDF and driver.** The first
   trajectory sends `joint_2` value to `joint_1`. Wreck. Triple-
   check the joint order in URDF and in the controllers config.
3. **Missing effort state interface** when MoveIt expects it. The
   driver logs a warning and refuses to start. Add or remove from
   the controllers YAML to match the driver's actual capabilities.
4. **Forgetting to declare the hardware plugin in URDF.** The plugin
   loader silently fails. Check `ros2 control list_hardware_components`.
5. **Bringing up the driver before powering the arm.** The driver
   times out, retries, and sometimes leaves a half-loaded state that
   needs a full re-launch.
6. **Running at full speed on day one.** Use speed scaling. Once you
   trust it, ramp.

## What's next

The driver swap works mechanically. But sim and real disagree on
*physics* — the camera's exact mounting position, the friction of the
gripper, the latency of the network. The next step is to measure and
correct those.

→ Next: [03-hand-eye-and-base-calibration.md](03-hand-eye-and-base-calibration.md)
