# Vendor SDKs and Drivers

The vendor SDK and the ROS 2 driver are the **bridge between your code
and the actual arm.** Without them, you have a piece of metal that
doesn't move.

Every arm vendor ships at least one SDK. Most also have a ROS 2 driver
(official or community). You will use both: the SDK for low-level things
the driver doesn't expose, the driver for everything else.

This file is just about which interfaces exist and what each is good
for.

## What you check, before anything else

- **Does your arm have an official ROS 2 driver?** Yes → use it.
- **What's the driver's update cadence?** A driver that hasn't shipped
  in two years is a liability.
- **What does the driver expose?** Position control? Velocity control?
  Torque control? Force/torque feedback? Joint states only, or also
  end-effector wrench?
- **What's the latency?** From "command sent" to "motor moves" — under
  10 ms is usually fine; 100 ms is fine for top-level commands but kills
  force control.
- **Real-time guarantees?** Are commands ever dropped, late, or
  reordered? For force control, the answer must be "no, ever."

## The main options

Arms fall into three buckets by how mature their ROS 2 story is.

### Tier 1: official ROS 2 driver, real-time path

Vendor maintains the driver. You almost never need to touch the raw
SDK.

| Arm family | Native SDK | ROS 2 driver | Notes |
|------------|------------|--------------|-------|
| **Universal Robots** | URScript over TCP, RTDE for real-time, URCap on the controller | `Universal_Robots_ROS2_Driver` (official) | The gold-standard ROS 2 cobot driver. RTDE gives 500 Hz updates. |
| **Franka Robotics FR3** | Franka Control Interface (FCI), C++ / Python | `franka_ros2` (official) | 1 kHz real-time torque control. Needs `PREEMPT_RT` kernel. |
| **Kinova Gen3** | Kortex SDK (C++, Python) | `ros2_kortex` (official) | Solid driver, multiple control modes. |

**Best for:** Anything where you want to write ROS 2 / MoveIt code and
not learn vendor scripting.

### Tier 2: vendor SDK first, community ROS 2 wrapper

The vendor's primary product is their own SDK or scripting language.
ROS 2 drivers exist but are community-maintained.

| Arm family | Native SDK | ROS 2 driver | Notes |
|------------|------------|--------------|-------|
| **FANUC** | KAREL, Karel, Roboguide, PCDK (Windows) | `fanuc_driver_ros2` (community, partial) | Most integrators talk to FANUC over EtherNet/IP from a PLC, not ROS 2. |
| **ABB** | RAPID, RobotWare, Robot Web Services (REST) | `ros2_abb` and `abb_robot_driver` (community / partial) | Wider gap than UR or Franka. |
| **KUKA** | KRL, KUKA.Sim, RSI (Robot Sensor Interface) | `kuka_experimental` / `kuka_drivers` (community) | LBR iiwa has better ROS 2 support than KR series. |
| **Yaskawa Motoman** | INFORM, MotoPlus, MotoROS 2 | `motoros2` (vendor-blessed, community-maintained) | Improving fast. |
| **Doosan / Aubo / JAKA / Techman** | Vendor Python SDK + ROS 2 driver | Vendor-supplied ROS 2 driver | Quality varies. Test the driver before committing. |

**Best for:** integration into existing factories. Production
deployment still often goes through the vendor's native programming
language; ROS 2 is the side-channel for vision / AI / R&D.

### Tier 3: hobby and education arms

Lighter drivers, simpler protocols. Easier to read end-to-end.

| Arm | Native SDK | ROS 2 driver | Notes |
|-----|------------|--------------|-------|
| **Elephant Robotics myCobot 280 Pi** | `pymycobot`, MyStudio, M5Stack firmware | `mycobot_ros2` | What this repo uses. Serial-over-USB, ~30 Hz updates. |
| **Niryo Ned2** | Niryo Python SDK, NiryoStudio | `ned_ros` | School-friendly. |
| **Annin AR4 / AR5** | Custom firmware + Python | community ROS 2 examples | DIY, expect to read code. |
| **Dobot Magician / MG400** | Dobot SDK (Python, ROS) | `dobot_ros2` (community) | Simple, top-down only. |

**Best for:** learning ROS 2 + MoveIt without spending UR money. What
this project uses.

## What an SDK / driver typically exposes

A useful driver should give you at least:

- **Read joint state** at a defined rate (positions, velocities,
  torques where available).
- **Send joint position commands** — "go to these joint angles."
- **Send Cartesian commands** — "go to this end-effector pose."
- **Velocity / streaming control** — for visual servoing, dynamic
  re-planning.
- **Force / torque feedback** — only on torque-sensing arms (Franka,
  KUKA LBR iiwa, UR e-series F/T sensor).
- **Gripper control** — usually a separate driver, exposed through the
  same ROS 2 graph.
- **E-stop and safety state** — the driver must surface this. If it
  doesn't, do not use it for anything but demos.

## A note on industrial fieldbuses

In a factory, the "driver" often isn't a ROS 2 package — it's an
**EtherNet/IP** or **PROFINET** connection from a PLC to the arm
controller. The PLC writes a status word, the controller acts on it,
the arm moves. ROS 2 enters only for vision and AI on a side IPC.

This is fine. You don't always need ROS 2 in the loop. But know which
world you're in before debugging "why doesn't my topic show up."

## How to pick

1. **Are you using one of UR, Franka, Kinova?** → Use the official
   ROS 2 driver. Done.
2. **Are you using an industrial big-four (FANUC, ABB, KUKA, Yaskawa)?**
   → Run the vendor SDK on a controller and add ROS 2 only for vision.
3. **Are you in research and need 1 kHz torque control?** → Franka FR3
   + FCI. Almost nothing else gets you there.
4. **Are you learning?** → myCobot 280 Pi + `mycobot_ros2` works and
   costs under $1000.
5. **Custom or DIY arm?** → You're writing your own driver. Look at
   `ros2_control` as the framework.

## ros2_control — the standardised way to write a driver

Most modern ROS 2 drivers are built on **`ros2_control`**: a framework
for plugging hardware interfaces (read joint state, write joint
command) into controllers (position, velocity, effort, JointTrajectory)
in a consistent way.

If you're writing a new driver, start with `ros2_control`. It saves
you from re-inventing controller switching, lifecycle management, and
URDF-based hardware introspection.

## Output of this file — your driver plan

```
Arm:                    UR5e / Franka FR3 / myCobot 280 Pi / FANUC LR Mate / ...
Native SDK:              URScript+RTDE / FCI / pymycobot / KAREL / ...
ROS 2 driver:            (package name) — version: ___
Control modes used:      position / velocity / torque / trajectory
Real-time required?:     yes / no
Gripper driver:          (separate package: ___ )
Force/torque feedback?:  built-in / via add-on F/T sensor / none
Safety reporting:        e-stop state surfaced via topic / service / never
Update rate:             ___ Hz read, ___ Hz write
```

## Common mistakes

1. **Picking an arm before checking driver health.** Some arms have
   abandoned ROS 2 drivers. Check the repo's last commit date.
2. **Using only the ROS 2 driver, ignoring the vendor SDK.** The
   driver exposes 80% of features. The other 20% (force-mode tuning,
   firmware update, calibration files) needs the vendor tools.
3. **Force control through a non-realtime kernel.** Works in demo,
   oscillates in production.
4. **Not version-pinning the driver.** Drivers break compatibility
   between minor versions. Pin in your `package.xml` and `colcon` build.
5. **Trusting the simulator-only driver.** Some "ROS 2 drivers" are
   really only the URDF + simulation glue, not real hardware
   integration.

## What's next

The driver gives you "move the arm to these joint angles." But you
usually want to say "put the end effector at this pose, without hitting
anything." That's the job of the motion planner.

→ Next: [04-motion-planning.md](04-motion-planning.md)
