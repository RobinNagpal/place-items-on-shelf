# Robotics Middleware

A robot is many small programs running at once: the arm driver, the
camera driver, the planner, the gripper controller, a status dashboard.
They have to **find each other and exchange messages** without you
hand-wiring every connection.

The software layer that handles "publish a message", "call a service",
"find the other process running on the same robot" is called
**middleware**. Pick it early — every later library you choose
(perception, planning, simulation) assumes one.

This file is just about which middleware to use.

## What you check, before anything else

- **What ecosystem does your arm vendor support?** Most cobot vendors
  ship an official ROS 2 driver. Industrial big-four (FANUC, ABB, KUKA,
  Yaskawa) have community ROS 2 drivers of varying quality plus their
  own native SDKs.
- **What ecosystem do your perception and planning libraries assume?**
  MoveIt is a ROS 2 package. Most camera SDKs publish to ROS 2 out of
  the box.
- **Real-time requirements** — ROS 2 is *not* hard real-time end-to-end.
  For tight motion loops, the real-time bit usually lives below the
  middleware, in a vendor driver.
- **Team experience** — if the team already knows ROS 1, the transition
  cost to ROS 2 is real but bounded. The transition cost to "build my
  own middleware" is unbounded.

## The main options

### ROS 2 — the default

The dominant open robotics middleware in 2025–2026. Built on **DDS**
(Data Distribution Service) for discovery and transport. Topics
(broadcast streams), services (request/response), actions (long-running
goals), and parameters (per-node config). Multi-language: C++ and Python
are first-class; Rust, Go, and JavaScript bindings exist.

Pick a current ROS 2 distro:

- **ROS 2 Humble (LTS, Ubuntu 22.04, support to 2027)** — the safe
  production pick today. Most third-party packages target it.
- **ROS 2 Jazzy (LTS, Ubuntu 24.04, support to 2029)** — the new
  starting point. Pick this for a fresh project.
- **ROS 2 Kilted (non-LTS)** — bleeding-edge, short support window.
  Only if you need a specific new feature.
- **ROS 2 Rolling** — continuous development branch. Not for
  production; use only to develop packages you'll backport.

**Best for:** essentially every research and most production cells.
Default unless one of the alternatives below applies.

### ROS 1 — legacy

ROS 1 (Noetic, the last release) is **end-of-life as of May 2025**. The
ecosystem is migrating to ROS 2.

- **Best for:** maintaining existing systems while you plan migration.
- **Avoid for:** new projects. Every month, more packages drop ROS 1.

### Vendor middleware (in industrial cells)

In a factory, the robot may not be on ROS 2 at all. The middleware is
the **fieldbus** — EtherCAT, PROFINET, EtherNet/IP — and the high-level
glue is the **PLC program** plus an HMI / SCADA stack.

- **Siemens TIA Portal** — Siemens-native PLC + HMI development.
- **Rockwell Studio 5000 + FactoryTalk** — Allen-Bradley's equivalent.
- **Beckhoff TwinCAT** — PC-based PLC + motion + middleware. Often
  used alongside ROS 2.

**Best for:** factory cells whose primary integrator is the PLC team,
not the robotics team. ROS 2 is sometimes a side IPC for vision; PLC
runs the motion sequence.

### MQTT / Kafka / cloud message brokers

Not robotics middleware on their own, but used **alongside** ROS 2 to
ship robot data to the cloud or to receive higher-level commands.

- **MQTT** — light, popular for "telemetry from many small robots."
  Brokers: Mosquitto, EMQX, HiveMQ.
- **Apache Kafka** — heavier, used in fleets that produce serious
  log volume.
- **AWS IoT Core, Azure IoT Hub, Google Cloud IoT** — managed
  brokers. Cheap until they're not.

**Best for:** fleet management, remote monitoring, "robot to dashboard."
Not for the robot's own control loop.

### LCM (Lightweight Communications and Marshalling)

Lightweight UDP-based message system from MIT. Used by Boston Dynamics
SDKs and some custom research stacks.

**Best for:** legacy MIT-spinout code, BD Spot SDK. Don't start a new
project on LCM unless you have a specific reason.

### Direct sockets / gRPC / ZeroMQ

Building robotics middleware yourself by writing TCP / UDP / gRPC
endpoints between processes.

**Best for:** when you have exactly two programs that need to talk, the
data is simple, and ROS 2 feels overkill. Also for the cloud-to-robot
edge.

**Avoid for:** the main robot graph. You'll re-implement discovery,
QoS, recording, and tooling, badly.

## DDS configuration (a ROS 2 footnote you will hit)

Every ROS 2 distro ships with at least two DDS implementations:

- **Fast DDS (default)** — open-source, made by eProsima.
- **Cyclone DDS** — open-source, often faster for high-throughput
  topics. Switch to it if Fast DDS gives you discovery problems.
- **Connext DDS (RTI)** — commercial, used in some industrial cells.

When two ROS 2 nodes don't see each other, the answer is almost always
DDS — wrong implementation, wrong domain ID, multicast blocked, or
firewall in the way. Learn `ros2 doctor`, `ros2 topic list`, and your
DDS-vendor diagnostic tool early.

## How to pick

1. **New robotics project, modern hardware?** → ROS 2 Jazzy.
2. **Existing ROS 2 codebase on Humble?** → Stay on Humble until next
   migration window.
3. **Stuck on ROS 1 Noetic?** → Plan a ROS 2 migration. New code
   targets ROS 2.
4. **Production factory with PLC primary?** → PLC vendor stack +
   ROS 2 as a side IPC if you need vision.
5. **Fleet of robots reporting to a backend?** → ROS 2 *on* each
   robot + MQTT *between* robot and cloud.

## Output of this file — your middleware plan

```
Primary middleware:        ROS 2 Jazzy / Humble / vendor PLC / ___
ROS 2 DDS:                 Fast DDS (default) / Cyclone DDS / RTI Connext
Domain ID:                 ___ (single-digit, isolates fleets sharing a network)
Cloud / fleet middleware:  none / MQTT (broker: ___) / Kafka / AWS IoT
Real-time path:            arm vendor driver direct / EtherCAT master / ROS 2 only
Bridge to PLC?:            none / OPC UA / Modbus / EtherNet/IP
```

## Common mistakes

1. **Picking ROS 1 in 2026.** Ecosystem is gone. Just don't.
2. **Mixing Humble and Jazzy on the same network.** Cross-version
   DDS can negotiate, but you'll see surprise interop bugs. Pin a
   distro per fleet.
3. **Multicast disabled on the corporate network.** DDS discovery
   silently fails. Use a unicast peer list or a dedicated robot
   subnet.
4. **One giant ROS 2 node doing everything.** You lose the whole
   point of the middleware. Split into focused nodes.
5. **Putting MQTT on the robot's control loop.** It's not designed
   for it. Use ROS 2 inside the robot, MQTT only for the cloud edge.

## What's next

You have a middleware. Now: how does the middleware actually talk to
the **arm** sitting on your table?

→ Next: [03-vendor-sdks-and-drivers.md](03-vendor-sdks-and-drivers.md)
