# Communication And Networking

A robot cell has many pieces — the arm, the controller, a PLC, an IPC, a
camera or two, sometimes a Jetson, sometimes a network printer or a
warehouse system. They all need to talk to each other.

This file is about **how the pieces talk** — the protocols, the cables,
the switches, the network design.

## The two kinds of "talk"

Roughly speaking, communication in a robot cell splits into two worlds:

1. **Real-time / control talk** — short messages, very predictable
   timing, can't be late. Examples: "joint 1, go to angle 2.3 rad in
   2 ms." A late message here is a crash.
2. **Plain data talk** — bigger messages, timing not as strict. Examples:
   a camera frame to a vision PC, a log entry to a database, a status
   update to a dashboard. A few hundred ms of jitter is fine.

Different protocols are designed for one or the other. Most cells run
both, on either separate networks or with traffic prioritisation.

## Common protocols

### Standard Ethernet (TCP/IP, UDP/IP)

The same Ethernet your home WiFi runs on top of. Not real-time, but very
flexible.

**Used by:** ROS 2 (over DDS), most cameras (RTSP / GigE Vision), most
PLCs for "talk-to-the-outside-world" messages, web dashboards, file
transfers.

**Best for:** anything that doesn't need hard real-time. The default
choice unless something else forces you off it.

### ROS 2 / DDS

ROS 2 uses DDS (Data Distribution Service) on top of standard
Ethernet — a publish/subscribe layer with discovery, QoS, and partitioning.

**Used by:** every ROS 2 system. Default to talk between ROS nodes on
the same machine, on the same LAN, or across machines.

**Best for:** research, prototypes, and increasingly production. Good for
tying together perception, planning, and control on Linux.

### EtherCAT

Industrial Ethernet, real-time, deterministic. Master-slave architecture
where messages get processed "on the fly" as they pass each device.

**Used by:** Beckhoff TwinCAT systems, lots of industrial servo drives,
some force/torque sensors, some safety devices.

**Best for:** high-performance motion control. Cycle times in the µs.

### PROFINET

Industrial Ethernet, real-time, Siemens-led standard.

**Used by:** Siemens-based factories. Most German industrial integrations.

**Best for:** Siemens-heavy production lines.

### EtherNet/IP

Industrial Ethernet, Allen-Bradley/Rockwell-led standard. (Yes — confusing
name; it's not the same as Ethernet/IP-in-the-internet sense.)

**Used by:** Rockwell-based US factories.

**Best for:** American industrial plants standardised on Allen-Bradley.

### Modbus TCP and Modbus RTU

Old, simple, very widely supported. TCP version runs on Ethernet; RTU
runs on RS-485 serial.

**Used by:** legacy devices, simple sensors, low-end PLCs, building
automation.

**Best for:** talking to old machinery or cheap sensors.

### CAN bus / CANopen

A low-bandwidth bus designed for cars. Used in some servo drives, robot
arms (Franka talks CAN internally), and joysticks.

**Used by:** automotive, some robot internals, some legacy industrial.

**Best for:** internal device-to-device talk; rarely something you pick
yourself.

### USB 3 / USB-C

Generic USB. Used by most depth cameras (RealSense, Orbbec), some F/T
sensors, some controllers.

**Used by:** cameras and "developer-friendly" hardware.

**Best for:** quick prototyping. Less reliable than Ethernet in
production (cables wiggle out).

### GigE Vision

Camera-specific protocol on top of Gigabit Ethernet. Very common in
industrial vision.

**Used by:** Basler, FLIR, IDS, Allied Vision cameras.

**Best for:** industrial machine vision. Long cable runs (up to 100 m
with PoE).

### Serial (RS-232, RS-485)

Old. Slow. Still everywhere.

**Used by:** legacy sensors, weighing scales, barcode readers, RFID
readers.

**Best for:** talking to one specific old device. Convert to USB or
Ethernet if you can.

### Wireless (WiFi, Bluetooth, 5G)

For data, sometimes fine. For control, **no** — too much jitter, can
drop out.

**Used by:** mobile robots over WiFi, smartphone teach pendants, status
dashboards.

**Best for:** non-critical status and data. Not for control of motion.

## Network design

Most cells have at least **two networks**:

1. **Control network** — the deterministic one. EtherCAT, PROFINET, or a
   dedicated Ethernet segment with the PLC, drives, and safety devices.
   Not connected to the internet.
2. **Information network** — the IT one. The IPC, the cameras (sometimes),
   the dashboard PC, the connection to the rest of the factory or the
   cloud.

Keeping them separate matters because:

- A noisy IT network can stall a control protocol if they share wires.
- A security incident on the IT side shouldn't be able to reach the
  motion control.

Pieces you'll need:

- **Industrial Ethernet switches** — rugged, DIN-rail-mounted. Brands:
  **Hirschmann, Moxa, Cisco IE, N-Tron, Phoenix Contact**.
- **Cables rated for the protocol** — Cat6 or Cat6a for Gigabit. For
  EtherCAT, often Cat5e is enough.
- **Connectors** — RJ45 for office use; **M12 / M8** for industrial,
  vibration-resistant.
- **Cable runs through cable carriers** (the next file).

## How a typical small cell talks

A common small cell (cobot + vision PC + camera + safety scanner):

```
[Wall outlet] -- power --> [UR controller] -- Ethernet --> [Office switch]
                              |                                  |
                              |                                  |
                          Ethernet                          Ethernet
                              |                                  |
                              v                                  v
                          [Safety relay]                    [Linux IPC]
                                                           (ROS 2 + RealSense
                                                              over USB3)
                                                                  |
                                                              Ethernet
                                                                  |
                                                                  v
                                                          [Office / cloud]
```

A bigger production cell adds a PLC, a separate control switch, a
PROFINET or EtherCAT line to drives, and a clear firewall between the
two networks.

## What to check when designing the network

| Check | Why it matters |
|-------|---------------|
| **Cable length** | Ethernet is rated 100 m. Longer = repeaters or fibre. |
| **Cable category** (Cat5e / 6 / 6a) | Higher = more bandwidth, more EMI tolerance. |
| **EMI environment** | Welders, big motors, VFDs generate noise. Shielded cable, ferrites, separation. |
| **IP rating of connectors** | M12 connectors for wet / dirty environments. RJ45 plastic clips break. |
| **Switch managed or unmanaged?** | Managed = configurable, supports VLANs and QoS. Production = managed. |
| **Power over Ethernet (PoE)?** | Powers some cameras and access points over the data cable. Saves a separate PSU. |
| **Network isolation** | Control segment must be physically or logically separate from IT. |
| **Time sync** | If multiple systems must agree on "now" (data fusion, logging), use **PTP** (Precision Time Protocol) or at minimum NTP. |

## Output of this file — your network plan

```
Control protocol:        EtherCAT / PROFINET / Ethernet-IP / Modbus / TCP / ...
Control network switch:  ___ (managed / unmanaged)
IT network switch:       ___
Cable category:          Cat ___
Connector type:          RJ45 / M12 / M8 / mixed
Cable length budget:     ___ m
PoE used?:               yes / no
Wireless?:               yes / no (and for what)
Time sync:               none / NTP / PTP
Firewall between nets?:  yes / no
```

## Common mistakes

1. **One flat network for everything.** Then a camera's bandwidth spike
   stalls the PLC's heartbeat. Always separate control and information.
2. **WiFi for control.** It will drop out. Always.
3. **Unmanaged switch in production.** No QoS, no VLAN, no diagnosis when
   something goes wrong.
4. **Forgetting cable shielding.** A VFD next door turns your Ethernet
   into noise.
5. **Wrong protocol for the device.** Trying to drive a PROFINET drive
   from a non-Siemens master is a multi-day exercise.
6. **No documentation of IP addresses.** A year later, nobody knows what
   192.168.1.42 was.

## What's next

You've designed the network. Now you have to actually **run the cables**
through a moving system without breaking them.

→ Next: [cable-management.md](cable-management.md)
