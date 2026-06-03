# 02 — Sim-to-Real Bridge

You have a virtual cell that works end-to-end. Now you cross the gap
to real hardware *without* breaking anything.

The gap has five concrete steps:

1. **[01-shared-urdf-and-frames.md](01-shared-urdf-and-frames.md)** —
   One URDF and one set of frame conventions used by both sim and
   real. The bridge starts here.
2. **[02-ros2-control-driver-swap.md](02-ros2-control-driver-swap.md)** —
   Swap the simulator's hardware interface for the vendor driver,
   keeping the controllers identical.
3. **[03-hand-eye-and-base-calibration.md](03-hand-eye-and-base-calibration.md)** —
   Calibrate camera intrinsics, hand-eye transform, and base
   alignment. Without this, every pick is off.
4. **[04-shadow-mode-and-slow-speeds.md](04-shadow-mode-and-slow-speeds.md)** —
   Run the real arm in shadow / slow modes while you watch every
   trajectory.
5. **[05-phased-rollout.md](05-phased-rollout.md)** —
   Supervised → Attended → Periodic → Unattended phases, each with
   an explicit gate.

You leave this workflow with a real cell that's been brought up,
calibrated, and is producing reliable picks at slow speed. The next
step is the on-real system integration in
[`../03-system-integration-on-real.md`](../03-system-integration-on-real.md).

← Back to: [Layer 4 README](../README.md)
