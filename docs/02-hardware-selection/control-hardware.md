# Control Hardware

The control hardware is the **computer (or box) that actually runs the
robot.** It takes the high-level plan ("move to X"), turns it into joint
commands, sends those to the motors, and reads back what the sensors are
seeing.

Most cobots ship with a controller. You don't pick it separately — it's
in the box. But for many real systems, you also need **a second
computer** to handle perception, AI, networking, or higher-level task
logic. That second box is what most of this file is about.

## The four levels of "the computer that runs the robot"

1. **The robot controller** — comes inside the arm's controller box. Runs
   the low-level motion. Sealed firmware. You don't program it directly;
   you talk to it through a SDK.
2. **A PLC (programmable logic controller)** — an industrial computer
   designed for reliable, repeatable, sequential control. Used in
   factories for decades.
3. **An IPC (industrial PC)** — a rugged general-purpose computer that
   runs your perception, AI, or task code. Often runs Linux + ROS 2.
4. **An edge AI box** — a small computer with a GPU or AI accelerator,
   for running vision and machine-learning models.

A simple cell may have just option 1 (the cobot controller). A research
cell often has 1 + 3 (controller + Linux PC). A production cell may have
1 + 2 + 3 (controller + PLC + IPC for AI).

## Robot controllers (inside the arm)

Comes with the arm. Briefly:

- **UR Controller (CB3, e-series)** — runs PolyScope (the teach pendant
  software). Talks to outside world over Ethernet (URCap, RTDE, ROS 2
  driver).
- **FANUC R-30iB Plus** — yellow box. Industrial standard. KAREL and
  TPP programming.
- **ABB IRC5 / OmniCore** — ABB's industrial controller. RAPID language.
- **KUKA KR C4 / KR C5** — KUKA's industrial controller. KRL language.
- **Yaskawa YRC1000** — Yaskawa's industrial controller. INFORM language.
- **Franka Control Interface (FCI)** — Franka FR3's controller. Native
  C++ / Python API. Real-time-friendly.

You don't *pick* these — they come with the arm. But you do read their
**SDK / API** docs to know how to talk to the arm from your other
computer.

## PLCs (programmable logic controllers)

A PLC is an industrial computer that runs **ladder logic** or
**structured text** programs. Very reliable. Very predictable. Boring on
purpose.

Use a PLC when:

- The cell has lots of non-robot machinery (conveyors, sensors, lights).
- You're integrating into a factory that already uses PLCs everywhere.
- You need to certify the system to a safety standard (some safety
  functions require a PLC).

Common brands:

- **Siemens SIMATIC S7** — the European industrial standard.
- **Allen-Bradley (Rockwell) ControlLogix / CompactLogix** — the
  American industrial standard.
- **Beckhoff TwinCAT** — runs on a PC, very popular for EtherCAT-based
  systems. Hybrid PLC/PC.
- **Mitsubishi MELSEC** — strong in Asia.
- **Omron, Schneider** — alternatives.

**Best for what:**

- Siemens — European factories.
- Allen-Bradley — American factories.
- Beckhoff — high-performance motion control, EtherCAT-heavy systems.

## Industrial PCs (IPCs)

A "PC in a box" rated for industrial environments — wider temperature,
shock-resistant, no fans (or filtered fans), DIN-rail mountable.

Use an IPC when:

- You're running ROS 2, OpenCV, MoveIt, or any AI code.
- You need a Linux machine that doesn't crash from dust or vibration.

Common brands:

- **Beckhoff** — premium, often paired with TwinCAT PLC.
- **Siemens SIMATIC IPC** — Siemens's IPC line.
- **B&R Industrial PCs** — European industrial.
- **Advantech, Kontron, Aaeon** — Taiwanese / German mid-range IPCs.
- **Logic Supply / OnLogic** — fanless mini-PCs popular for ROS.
- **Dell, HP industrial workstations** — when you need GPU horsepower
  and an industrial cabinet is overkill.

**Best for what:**

- Beckhoff / Siemens — production cells that combine PLC + IPC.
- Advantech / OnLogic — research and prototype systems running ROS 2.
- Dell workstation — heavy AI training or GPU inference.

## Edge AI computers

A small computer with a GPU or AI accelerator. Used for running camera
inference (object detection, pose estimation) close to the robot.

- **NVIDIA Jetson Orin Nano / Orin NX / Orin AGX** — the most popular
  edge AI platform in robotics. Runs CUDA-accelerated models.
- **Intel NUC + small GPU** — flexible. Less integrated than Jetson.
- **Google Coral** — TPU-based. Lightweight, low-power. Limited to
  TensorFlow Lite models.
- **AMD Ryzen embedded boards** — alternative to Intel NUC.

**Best for what:**

- Jetson Orin — running YOLO / segmentation / VLA models on a moving
  robot.
- Coral — low-power binary detection ("is something there?").
- Intel NUC + GPU — when you want a desktop-class GPU in a small box.

## Hobby computers (under $200)

For learning and prototypes:

- **Raspberry Pi 5 (8 GB)** — runs Ubuntu and ROS 2 fine for light tasks.
  myCobot 280 Pi uses one inside.
- **NVIDIA Jetson Nano** — older Jetson, still works for basic vision.
- **BeagleBone Black** — for real-time control experiments.
- **Mini-ITX desktop PC** — cheap, more power than a Pi.

**Best for what:**

- Pi 5 — the default cheap ROS 2 host for a hobby arm.
- Jetson Nano — same but with light GPU inference.

## How to pick

Run through this list in order:

1. **Does the arm already come with a controller?** (Yes for any cobot
   or industrial arm.) → That handles the motion. Move on.
2. **Is the cell purely the arm and one camera?** (Hobby / research.) →
   One IPC or even a Raspberry Pi is enough.
3. **Are there conveyors, light curtains, lots of digital I/O?** → Add
   a PLC.
4. **Are you running vision AI on a moving budget?** → Add a Jetson Orin
   or equivalent.
5. **Production, factory, lots of certification needs?** → Likely
   PLC + IPC combination (Beckhoff or Siemens).

## Output of this file — your control hardware list

```
Robot controller:        comes with arm (model: ___ )
PLC?:                    none / Siemens ___ / AB ___ / Beckhoff ___
IPC?:                    none / Advantech ___ / OnLogic ___ / Dell ___
Edge AI?:                none / Jetson ___ / NUC + GPU ___
Hobby compute?:          none / Pi ___ / Jetson Nano ___
Operating system:        Linux / Windows / vendor RTOS
Software stack:          ROS 2 / vendor SDK / TwinCAT / Step 7 / ...
```

## Common mistakes

1. **Running ROS 2 on a laptop on the floor.** Works for a demo. Fails
   in production because the laptop battery dies, the lid closes, or
   the WiFi disconnects.
2. **Skipping the PLC in a factory.** Robots without PLC integration
   are islands. Factory IT will refuse to deploy them.
3. **Wrong Jetson for the model.** A Jetson Nano cannot run a large YOLO.
   Read the model's memory requirements before buying the cheapest box.
4. **No real-time guarantees.** ROS 2 on Ubuntu is *not* hard real-time.
   For safety-critical or high-speed motion, use a real-time kernel or
   a vendor-real-time stack like TwinCAT.
5. **Buying compute without thinking about cooling.** Fanless boxes
   throttle. Boxes with fans suck in dust. Plan ventilation.

## What's next

You have a controller, maybe an IPC, maybe a Jetson. Now: how do they
all **talk to each other and to the arm**?

→ Next: [communication-and-networking.md](communication-and-networking.md)
