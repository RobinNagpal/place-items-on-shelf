# 03 — System Integration on Real Hardware

Sim is done. The driver works. The arm moves. This chapter covers the
**one-time physical bring-up** of the real cell — the unglamorous
"it boots, it talks, it's safe to leave overnight" work that has to
happen before any production thinking.

Sim doesn't catch any of this. You only find these issues when the
hardware actually exists in the room.

## What you need before this step

- Hardware: arm, gripper, sensors, mounting, power, cables, safety
  equipment — everything from Layer 2 in the room and on the table.
- Layer 3 software installed on the IPC / edge box.
- A working bring-up checklist of your own (see also
  [05-bring-up-checklist.md](05-bring-up-checklist.md) for a generic
  one).
- Time. A full bring-up day for a small cell is realistic; longer
  for cells with PLCs, light curtains, or vision pipelines.

## What "system integration" actually covers

Five concrete things:

1. **Physical assembly** — the arm is bolted to the table, cables are
   routed, sensors are mounted, the cabinet has airflow.
2. **Power-on and electrical safety** — circuits energise without
   tripping a breaker, ground is intact, e-stop kills power as
   expected.
3. **Network and discovery** — every box on the cell can see every
   other one over the right protocol.
4. **First boot of the software stack** — every service from Layer 3
   comes up cleanly in the right order.
5. **The collision world** — the planning scene has every real
   obstacle the arm could hit.

We'll walk each one.

## 1. Physical assembly

Things to verify before you turn on power:

- **Mount torque.** Use a torque wrench on the arm's base bolts. A
  cobot's mounting torque is in its installation guide.
- **Cable strain relief.** Every cable has a strain relief or P-clip
  near a connector. No cable hangs loose.
- **Drag chains** sized so they don't bind across the arm's worst-
  case pose. Run the arm through `home` → `tuck` → `reach` by hand
  (brakes off) and check for snags.
- **Safety devices physically mounted.** E-stop on the operator side,
  light curtains aligned, scanners powered.
- **Air, water, vacuum lines** routed and pressure-tested if your
  gripper uses any.

Take photos at this stage. They become the "as-built" reference.

## 2. Power-on and electrical safety

Order matters:

1. **Mains breaker** — flip it on. No smoke is a passing test.
2. **Arm controller** — power up via the keyswitch / power button.
3. **IPC and edge box** — boot to OS.
4. **Camera and other sensors** — power, confirm LEDs / firmware.
5. **PLC, if any** — power up and confirm it runs its program.

Then test each safety device:

- **E-stop:** with the arm in a non-powered idle, press the e-stop;
  arm should be unable to enable. Reset, confirm normal startup.
- **E-stop during motion:** while the arm jogs slowly, press the
  e-stop. Arm must stop within the manufacturer-specified time
  (usually under 500 ms).
- **Light curtain / safety scanner:** with motion enabled, break the
  curtain — arm must stop.
- **Door interlocks:** open the door — arm must stop.

Each of these is a separate, recorded test. Write down the time-to-
stop and any unexpected behaviour.

## 3. Network and discovery

For a typical ROS 2 cell:

- **Wired Ethernet** between IPC, arm controller, switches, camera,
  PLC.
- **A dedicated subnet** for the robotics traffic (don't share with
  corporate IT).
- **DDS configured** for a fixed domain ID and ideally a unicast peer
  list, not multicast (most corporate networks block multicast).
- **NTP / PTP** clock sync.

Verify:

```
ping <arm_ip>
ping <camera_ip>
ros2 doctor                  # surfaces DDS / discovery problems
ros2 topic list              # all expected topics present
chronyc tracking             # if using NTP
```

Document the cell's network topology (a Visio / draw.io PNG counts).
The next engineer to touch this cell will thank you.

## 4. First boot of the software stack

Bring up services in dependency order:

1. **OS-level systemd services** — chrony, network, etc.
2. **The arm driver** (`ur_robot_driver`, `franka_ros2`, …).
3. **The camera driver** (`realsense2_camera`, etc.).
4. **`ros2_control` controllers** (`controller_manager` + your
   `JointTrajectoryController`).
5. **MoveIt 2** (`move_group`).
6. **Perception nodes.**
7. **Orchestrator** (your BT / FSM / task code).

Test each one individually with `ros2 topic echo` /
`ros2 node info` before moving up the stack. A pyramid that
collapses at the bottom is hard to diagnose.

Then encode the launch order in a single project bring-up launch
file or a `systemd` unit so daily operators don't have to remember.

## 5. The collision world

The MoveIt planning scene from sim doesn't know about real
obstacles. Add them now:

- **The table.** As a `Box` collision object, with the real height
  and footprint.
- **Walls / fixtures.** Anything within the arm's reach must be
  modelled. Plastic shrouds, fences, the operator's monitor stand.
- **The camera mount.** Yes — the arm can hit its own camera mount
  in some poses.
- **Cables and air lines** that take up space.

You can build this scene either:

- **Hand-coded** in a YAML loaded at launch — fastest for static
  cells.
- **From a CAD export** — accurate but more work.
- **From a depth scan** — fancy but rarely worth it.

After loading, run the [01-simulation-first-development/04](01-simulation-first-development/04-scripted-first-task.md) scripted
task once more on **real** with the slow-speed settings from
[02-sim-to-real-bridge/04](02-sim-to-real-bridge/04-shadow-mode-and-slow-speeds.md). The planner should now
route around the real obstacles.

## Output of this step

```
Mount torque applied:           yes — value: ___ Nm
Cable strain relief in place:    yes / no
Drag chains tested:              yes / no — snag found: ___
E-stop tested (idle):            yes / no
E-stop time-to-stop (motion):    ___ ms
Light curtain stop confirmed:    yes / no / N/A
Door interlock stop confirmed:   yes / no / N/A
Network subnet:                  ___
DDS implementation + domain ID:  ___
NTP / PTP source:                ___
ros2 doctor warnings:            ___
Bring-up launch file path:       ___
Boot order systemd-managed?:     yes / no
Planning scene collision objects: table, walls, ___ (count: ___ )
As-built photos archived to:     ___
```

## Common mistakes

1. **Power-on before testing e-stop.** Always know how to kill power
   before you give it.
2. **No torque wrench on mount bolts.** They loosen over months and
   the arm starts drifting. Use the wrench, log the value.
3. **Multicast-only DDS on a corporate network.** Half the topics
   appear, half don't, intermittently. Switch to a unicast peer
   list.
4. **Bringing up the orchestrator before the driver.** The
   orchestrator times out, retries, occupies the port, blocks the
   driver. Strict launch order.
5. **No real-obstacle collision model.** Sim worked; real arm
   crashes into the camera mount on first plan. Always model the
   real workspace.
6. **No "as-built" record.** Six months later, nobody knows what's
   actually mounted where.

## What's next

Cell is physically up, software booted, calibrated, supervised. Now —
*optionally* — you teach it a skill by demonstration.

If you're not using imitation learning, skip ahead to
[05-bring-up-checklist.md](05-bring-up-checklist.md).

→ Optional next (only if using IL):
[04-imitation-learning-workflow/01-pick-teleop-hardware.md](04-imitation-learning-workflow/01-pick-teleop-hardware.md)
