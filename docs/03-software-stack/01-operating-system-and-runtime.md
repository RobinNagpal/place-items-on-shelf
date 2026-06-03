# Operating System and Runtime

The operating system is the **base layer of software** that sits directly
on your control hardware. Everything else — middleware, motion planner,
perception, AI — runs on top of it.

For a robotics project today, "operating system" almost always means
**Linux**, and usually a specific Ubuntu LTS release. But there are real
reasons to pick something else, so the choice is worth making
deliberately.

This file is just about that choice.

## What you check, before anything else

Your Layer-2 hardware list already constrains you. Some questions to
answer first:

- **What does your control hardware support?** A FANUC controller runs
  the vendor RTOS — you don't get to swap it. A PLC runs the PLC firmware.
  Only on the IPC and edge AI box do you actually pick an OS.
- **What does your middleware require?** ROS 2 currently targets
  specific Ubuntu LTS releases. Pick the OS to match the middleware, not
  the other way around.
- **How real-time does your control loop need to be?** Hard real-time
  (sub-millisecond, guaranteed) needs a real-time kernel or a real-time
  OS. Soft real-time (best-effort, usually under 10 ms) runs on plain
  Linux fine.
- **Will an IT department touch this machine?** If yes, you may be
  forced onto Windows or a managed Linux. If no, you pick.

## The main options

### Linux (Ubuntu LTS)

The default for any robotics project that uses ROS 2, MoveIt, OpenCV, or
PyTorch. Free, well-supported, mature.

- **Ubuntu 22.04 LTS** — pairs with ROS 2 Humble (LTS until 2027).
  The current safe pick.
- **Ubuntu 24.04 LTS** — pairs with ROS 2 Jazzy (LTS until 2029) and
  is the target for ROS 2 Kilted. Pick this for new projects starting
  fresh.
- **Older Ubuntu (20.04, 18.04)** — only if you're stuck on ROS 2 Foxy
  or ROS 1 Noetic. Both are end-of-life; plan to migrate.

**Best for:** every research, hobby, and most production robotics
projects. The default unless someone forces another choice.

### Other Linux distributions

You'll see these in production cells:

- **Debian** — what Ubuntu is built on. Use it when you want a smaller
  base and don't need Ubuntu's extra polish.
- **Red Hat Enterprise Linux (RHEL) / Rocky / AlmaLinux** — preferred
  in heavily regulated factories. Slower release cycle, longer support.
- **Yocto / buildroot custom Linux** — for embedded boards where you
  trim the OS down to just what the robot needs.

**Best for:** RHEL — factories that already standardise on it. Yocto —
custom embedded hardware (a robot you ship, not one you operate).

### Real-time Linux

Plain Linux's kernel is *not* hard real-time. If you need guaranteed
sub-millisecond response (for high-speed motion control, EtherCAT
masters, custom torque control), use one of:

- **PREEMPT_RT patched kernel** — turns Linux into a soft/firm real-time
  OS. Built into recent mainline kernels as `PREEMPT_RT`. Works with
  Ubuntu.
- **Xenomai** — a real-time co-kernel sitting alongside Linux. Used by
  some industrial systems.

**Best for:** motion control loops on top of EtherCAT, force control on
Franka FR3, anything where a 5 ms hiccup is unacceptable.

### Windows

You'll meet Windows in two places:

- **The engineer's laptop** for vendor configuration tools (UR's
  PolyScope offline simulator, ABB RobotStudio, FANUC ROBOGUIDE,
  KUKA.Sim, Beckhoff TwinCAT XAE).
- **An HMI panel** running a Windows-based SCADA / HMI package.

You almost never run the robot's main control software on Windows
itself — too much of the open ecosystem assumes Linux.

**Best for:** vendor-specific design tools and HMI panels.

### Vendor RTOS

The arm controllers (UR, FANUC, ABB, KUKA, Yaskawa) run their own
real-time OS. You don't pick it. You don't see it. You only interact
with it through the vendor SDK.

The "PC inside the cobot" (myCobot 280 Pi's Raspberry Pi, Franka's
control PC) runs Linux — that you do choose.

### macOS

For developer laptops only. Don't run a robot from a Mac. ROS 2 has
limited macOS support and it's not where the community ships fixes
first.

## How to pick

1. **Are you running ROS 2?** → Match the Ubuntu LTS to the ROS 2
   distro (22.04 + Humble, or 24.04 + Jazzy/Kilted).
2. **Hard real-time control loop on Linux?** → Add a `PREEMPT_RT`
   kernel on top.
3. **Factory wants RHEL?** → Use RHEL-derived distro, accept slower
   community libraries.
4. **Building an embedded product to ship?** → Use Yocto + a custom
   image.
5. **Anything else?** → Ubuntu LTS, latest stable.

## Output of this file — your OS plan

```
IPC OS:                    Ubuntu 24.04 LTS / 22.04 LTS / RHEL ___ / Yocto
ROS 2 distro it pairs with: Humble / Jazzy / Kilted / Rolling
Real-time kernel?:         no / PREEMPT_RT / Xenomai
Other machines:            engineer laptop (Linux / Mac / Win), HMI (Win / Linux)
Vendor OS on arm controller: (model: ___ ) — opaque, configured via SDK
Time sync source:          NTP server (chrony) / PTP / vendor master clock
Disk image format:         raw / OS image / container base
```

## Common mistakes

1. **Mixing Ubuntu versions across the team.** One person on 22.04,
   one on 24.04 — packages don't match, fixes don't reproduce. Pin
   the LTS for the whole team.
2. **Skipping the real-time kernel "until later."** "Later" never
   happens, and you'll spend a week chasing a missed deadline that's
   really a jitter problem.
3. **Auto-updating in production.** A surprise kernel update at 3 a.m.
   restarts the IPC and stops the line. Pin packages, disable
   `unattended-upgrades`.
4. **No NTP / PTP.** Robots without synchronised clocks log events
   out of order, and TLS certificates randomly fail.
5. **Running ROS 2 inside WSL or a Mac VM in production.** Fine for
   reading docs. Not fine for actually controlling an arm.

## What's next

You have a base OS picked. Now: how do all the programs that run on top
of it find and talk to each other?

→ Next: [02-robotics-middleware.md](02-robotics-middleware.md)
