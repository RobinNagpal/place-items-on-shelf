# Communication And Networking

The cell has many parts — arm, controller, IPC, cameras, sometimes a
PLC. They all have to talk.

## Two kinds of "talk"

1. **Control talk** — short messages, can't be late. "Joint 1, move to
   angle X in 2 ms." A late message = a crash.
2. **Data talk** — bigger messages, timing is loose. Camera frames,
   logs, dashboards. A few hundred ms of jitter is fine.

Most production cells run both — on separate networks, or with traffic
priority.

## The protocols you'll meet

| Protocol | Use it for | Used by |
|----------|------------|---------|
| **Ethernet (TCP/IP, UDP/IP)** | Anything non-real-time | ROS 2, most cameras, PLC outside-world links |
| **ROS 2 / DDS** | Talking between ROS nodes | Every ROS 2 system |
| **EtherCAT** | Hard real-time motion (µs cycles) | Beckhoff TwinCAT, industrial drives |
| **PROFINET** | Real-time on Siemens factories | Siemens-based plants |
| **EtherNet/IP** | Real-time on Allen-Bradley factories | Rockwell-based plants |
| **Modbus TCP / RTU** | Old simple sensors and PLCs | Legacy machinery |
| **CAN / CANopen** | Some servo drives, internal device buses | Franka internals, automotive |
| **USB 3 / USB-C** | Depth cameras, F/T sensors | Prototypes |
| **GigE Vision** | Industrial cameras over Ethernet | Basler, FLIR, IDS |
| **Serial (RS-232/485)** | One specific old device | Scales, barcode readers |
| **Wireless (WiFi, 5G)** | Data only, **never** control | Mobile robots, dashboards |

Rule of thumb: default to plain Ethernet. Use an industrial protocol
only when something forces it.

## Network design — two networks, not one

Most production cells have **two physical networks**:

1. **Control network** — deterministic. EtherCAT, PROFINET, or a
   dedicated Ethernet segment with PLC, drives, safety. Not on the
   internet.
2. **Information network** — IT. IPC, cameras (sometimes), dashboards,
   the factory uplink.

Keep them apart so:

- A noisy IT cable doesn't stall a control protocol.
- A security incident on IT can't reach motion control.

Hardware you'll need:

- **Industrial switches** — Hirschmann, Moxa, Cisco IE. Managed in
  production.
- **Cables** — Cat6 / Cat6a for Gigabit. Cat5e for EtherCAT.
- **Connectors** — RJ45 (office); **M12 / M8** (industrial, vibration-
  and water-resistant).
- **Time sync** — PTP if multiple systems must agree on "now"; NTP
  otherwise.

## What to check

| Check | Why |
|-------|-----|
| **Cable length** | Ethernet is 100 m max. Longer = repeaters or fibre. |
| **EMI environment** | Welders and VFDs need shielded cable and separation. |
| **IP rating of connectors** | M12 for wet/dirty environments. RJ45 plastic clips break. |
| **Managed switch?** | Production = yes. |
| **PoE?** | Powers small cameras and access points over the data cable. |
| **Network isolation** | Control physically or logically separate from IT. |

## Output of this file — your network plan

```
Control protocol:        EtherCAT / PROFINET / EtherNet/IP / TCP / ...
Control switch:          ___ (managed / unmanaged)
IT switch:               ___
Cable category:          Cat ___
Connectors:              RJ45 / M12 / M8 / mixed
Cable length budget:     ___ m
PoE used?:               yes / no
Wireless?:               yes / no — what for
Time sync:               none / NTP / PTP
Firewall between nets?:  yes / no
```

## Common mistakes

1. **One flat network for everything.** A camera bandwidth spike stalls
   the PLC heartbeat.
2. **WiFi for control.** It will drop out.
3. **Unmanaged switch in production.** No QoS, no VLAN, no diagnosis.
4. **No cable shielding near VFDs.** Ethernet turns to noise.
5. **Wrong protocol for the device.** Driving a PROFINET drive from a
   non-Siemens master = days of work.
6. **No IP-address documentation.** A year later, nobody knows what
   192.168.1.42 is.

## What's next

The network is planned. Now: how to run the cables on a moving arm
without breaking them.

→ Next: [08-cable-management.md](08-cable-management.md)
