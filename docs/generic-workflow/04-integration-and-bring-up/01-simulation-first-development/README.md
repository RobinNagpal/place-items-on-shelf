# 01 — Simulation-First Development

Before you touch real hardware, you build a virtual version of the
cell and make it run end-to-end. Every later step assumes this
worked.

Six steps, in order:

1. **[01-choose-and-install-simulator.md](01-choose-and-install-simulator.md)** —
   Pick a simulator (Gazebo / Isaac Sim / MuJoCo / PyBullet / Webots
   / CoppeliaSim / Drake / Genesis / Unity / Unreal) and confirm it
   launches.
2. **[02-build-the-virtual-cell.md](02-build-the-virtual-cell.md)** —
   Put your arm, your table, an object, and a camera into the sim.
3. **[03-bring-up-moveit-in-sim.md](03-bring-up-moveit-in-sim.md)** —
   Get a motion planner (MoveIt 2 or an alternative) talking to the
   simulator.
4. **[04-scripted-first-task.md](04-scripted-first-task.md)** —
   Write the simplest end-to-end pick-and-place script. Hard-coded
   poses, no perception.
5. **[05-fake-perception-in-sim.md](05-fake-perception-in-sim.md)** —
   Make the task read the object pose from a fake perception node,
   with realistic noise.
6. **[06-stress-test-in-sim.md](06-stress-test-in-sim.md)** —
   Break the task on purpose: vary object pose, noise, clutter,
   start state. Hit the acceptance bar (≥95% in sim).

You leave this workflow with a fully-validated **virtual** cell —
the launch pad for crossing into real hardware in
[`../02-sim-to-real-bridge/`](../02-sim-to-real-bridge/).

← Back to: [Layer 4 README](../README.md)
