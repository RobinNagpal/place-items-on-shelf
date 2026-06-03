# 05 — Bring-up Checklist

A literal checklist for the **first day on real hardware** (or
re-bring-up after any major change). Print it, tick the boxes, sign
the bottom.

If you skip a box, your future self will pay for it. The boxes look
small until one of them isn't done.

## What you need before this step

- Real hardware brought up through
  [03](03-system-integration-on-real.md).
- Calibration done through
  [02-c](02-c-hand-eye-and-base-calibration.md).
- The slow-speed pick from
  [02-d](02-d-shadow-mode-and-slow-speeds.md) working.
- A camera, a notebook, and a pen.

## The checklist

### Pre-power

- [ ] Mounting bolts torqued to spec; values recorded.
- [ ] All cables strain-relieved; nothing hanging loose.
- [ ] Drag chain runs cleanly through `home` → `tuck` → `reach`
      poses (manual move, brakes off).
- [ ] No tools, no parts, no operator's hands inside the arm's
      swept volume.
- [ ] Pressure / vacuum / air lines connected and pressure-tested if
      applicable.
- [ ] E-stop button reachable, mushroom-out, ready to press.

### Power-on

- [ ] Mains breaker on. No smoke. No tripping.
- [ ] Arm controller booted. Pendant says "ready / running."
- [ ] IPC booted. SSH from operator workstation works.
- [ ] Edge AI box (Jetson, NUC) booted. GPU visible in `nvidia-smi`.
- [ ] Camera powered. `realsense-viewer` (or vendor tool) shows live
      image.
- [ ] PLC booted (if any). Running its program.
- [ ] All cooling fans on. Cabinet vents unobstructed.

### Safety verification

- [ ] E-stop tested with the arm idle. Arm cannot enable while pressed.
- [ ] E-stop tested with the arm in motion (slow). Time-to-stop:
      ____ ms. Below vendor spec.
- [ ] Light curtain breaks stop the arm. (If installed.)
- [ ] Safety scanner zones tested. (If installed.)
- [ ] Door interlock stops the arm. (If installed.)
- [ ] Operator pendant's enable switch tested.

### Network

- [ ] Each device pings.
- [ ] `ros2 doctor` clean (or known harmless warnings logged).
- [ ] `ros2 topic list` shows expected topics.
- [ ] NTP / PTP locked. Clocks within 10 ms across machines.
- [ ] Firewall rules confirmed for ROS 2 DDS ports.

### Software bring-up

- [ ] Driver launches and reports "connected."
- [ ] `/joint_states` publishes at expected rate.
- [ ] `ros2 control list_controllers` — all `active`.
- [ ] MoveIt launches without errors. `move_group` ready.
- [ ] Perception node launches. Detections publish on the expected
      topic.
- [ ] Orchestrator (BT / FSM / task code) launches and reaches an
      idle state cleanly.
- [ ] Logging captures: `/joint_states`, `/tf`, perception outputs,
      orchestrator decisions. Verified with `ros2 bag info`.

### Motion verification

- [ ] RViz Plan + Execute moves the arm to `HOME` at slow speed.
- [ ] Plan + Execute to each "reference pose" defined in MoveIt
      config.
- [ ] Each named pose verified visually — arm is where the URDF says
      it is.
- [ ] Slow-speed scripted pick from
      [01-d](01-d-scripted-first-task.md) runs 5 times in a row
      with no surprises.

### Calibration verification (re-check)

- [ ] Touch test: arm moves to a known-position object; gripper tip
      lands within 2 mm.
- [ ] Hand-eye reprojection error logged. Within
      [02-c](02-c-hand-eye-and-base-calibration.md) bar.
- [ ] Date and operator stamped on the calibration YAML.

### Operator handover

- [ ] Operator runbook ([09](09-runbooks-and-operator-training.md))
      printed and on the cell.
- [ ] Operator has run the bring-up sequence once with you watching.
- [ ] Emergency-stop and reset procedure verbally rehearsed.
- [ ] Contact path documented: who do they call when something
      breaks?

### Documentation

- [ ] "As-built" photos taken from at least four angles.
- [ ] Cell-specific configuration committed to git.
- [ ] Calibration YAML committed.
- [ ] Bring-up log saved (this checklist, completed, signed).

## Sign-off

```
Cell name / ID:               ___
Bring-up date:                ___
Operator(s) present:          ___
Robotics engineer:            ___
Safety reviewer:              ___
Issues found and resolved:    ___
Issues found and deferred:    ___
Cell status after bring-up:    ready for pilot / blocked on ___
```

## Common mistakes

1. **Skipping the e-stop motion test.** "It worked at idle." Idle and
   motion paths can be different.
2. **No torque values recorded.** Three months later, a bolt
   loosens and you can't tell if it was ever right.
3. **Operator wasn't there during bring-up.** First time they see
   the cell is when something's already wrong.
4. **No rosbag of the bring-up runs.** When someone asks "did it
   really work on day one?", you have no proof.
5. **Treating the checklist as paperwork.** Each line is there because
   someone got burnt. Take them seriously.

## What's next

Checklist signed. Pilot deployment.

→ Next: [06-pilot-deployment.md](06-pilot-deployment.md)
