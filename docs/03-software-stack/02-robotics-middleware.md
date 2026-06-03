# Robotics Middleware

A robot is many small programs running at once: the arm driver, the
camera driver, the planner, the gripper, a dashboard. They all need to
**find each other and exchange messages** — without you hand-wiring
every connection.

The software that handles "send a message to whoever cares" is called
**middleware**. Think of it as the post office between the programs on
your robot.

Pick it early — every other library you choose later (perception,
planning, simulation) already assumes one.

## What you check first

- **What does your arm vendor support?** Cobot vendors almost always
  ship a ROS 2 driver. The big-four industrial brands (FANUC, ABB,
  KUKA, Yaskawa) have community ROS 2 drivers plus their own native
  SDKs.
- **What do your other libraries assume?** MoveIt, most camera
  drivers, and most planners are ROS 2 packages.
- **Real-time?** ROS 2 is *not* hard real-time end-to-end. The
  µs-precise motion loop lives below it, in the vendor driver.
- **Team experience.** Moving from ROS 1 to ROS 2 is real but bounded
  work. Writing your own middleware is bottomless work.

## The main options

### ROS 2 — the default

The dominant open robotics middleware in 2025–2026. You publish on
**topics**, call **services** for request/response, run **actions**
for long jobs, and read **parameters** for config. C++ and Python are
first-class.

Pick a distro:

| Distro | Status | When to pick |
|--------|--------|--------------|
| **ROS 2 Jazzy** | LTS on Ubuntu 24.04, support to 2029 | Fresh project. Default. |
| **ROS 2 Humble** | LTS on Ubuntu 22.04, support to 2027 | Existing project already on Humble. |
| **ROS 2 Kilted** | Non-LTS | Only if you need a specific new feature. |
| **ROS 2 Rolling** | Dev branch | Package authors only, never production. |

### ROS 1 — legacy

ROS 1 Noetic went end-of-life in **May 2025**. Keep maintaining old
projects on it, but **don't start new ones on ROS 1**.

### Vendor PLC stack (in factories)

In a factory, the robot may not be on ROS 2 at all. The "middleware"
is the **fieldbus** (EtherCAT, PROFINET, EtherNet/IP) and the **PLC
program** on top — usually **Siemens TIA Portal**, **Rockwell
Studio 5000**, or **Beckhoff TwinCAT**.

ROS 2 is often a *side* IPC for vision; the PLC runs the motion
sequence.

### Cloud message brokers (alongside ROS 2)

Not robotics middleware on their own — use them to ship data **off**
the robot. **MQTT** (Mosquitto, EMQX) for fleet telemetry; **Kafka**
or **AWS IoT / Azure IoT** for heavier logs.

**Never** use them inside the robot's own control loop.

## DDS — a ROS 2 footnote you'll hit

ROS 2 sends messages over **DDS**, a publish/subscribe protocol.
Every distro ships at least two DDS implementations:

- **Fast DDS** — the default. Works for most cases.
- **Cyclone DDS** — switch to it if discovery is flaky or topics are
  high-throughput.
- **RTI Connext** — commercial; some industrial cells.

When two ROS 2 nodes don't see each other, the cause is almost always
DDS: wrong implementation, wrong domain ID, multicast blocked, or a
firewall. Learn `ros2 doctor` and `ros2 topic list` early.

## How to pick

1. **New project, modern hardware?** → ROS 2 Jazzy.
2. **Existing ROS 2 codebase on Humble?** → Stay on Humble.
3. **Stuck on ROS 1 Noetic?** → Migrate to ROS 2; new code targets it.
4. **Factory cell with PLC primary?** → PLC stack + ROS 2 as a side
   IPC for vision.
5. **Fleet of robots reporting upstream?** → ROS 2 *on* each robot,
   MQTT *between* robot and cloud.

## Output of this file — your middleware plan

```
Primary middleware:        ROS 2 Jazzy / Humble / vendor PLC / ___
ROS 2 DDS:                 Fast DDS (default) / Cyclone DDS / RTI Connext
Domain ID:                 ___ (single-digit, isolates fleets on one network)
Cloud / fleet middleware:  none / MQTT (broker: ___) / Kafka / AWS IoT
Real-time path:            arm vendor driver / EtherCAT master / ROS 2 only
Bridge to PLC?:            none / OPC UA / Modbus / EtherNet/IP
```

## Common mistakes

1. **Picking ROS 1 in 2026.** Ecosystem is gone.
2. **Mixing Humble and Jazzy on one network.** Cross-version DDS
   sometimes negotiates, sometimes doesn't. Pin one distro per fleet.
3. **Multicast disabled on the corporate network.** DDS discovery
   silently fails. Use a unicast peer list or a dedicated subnet.
4. **One giant ROS 2 node doing everything.** Defeats the point. Split
   into focused nodes.
5. **MQTT on the control loop.** It's not designed for it.

## What's next

You have a middleware. Now: how does it actually talk to the **arm**
on your table?

→ Next: [03-vendor-sdks-and-drivers.md](03-vendor-sdks-and-drivers.md)
