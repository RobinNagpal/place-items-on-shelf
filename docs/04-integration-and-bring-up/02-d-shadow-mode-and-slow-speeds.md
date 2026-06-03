# 02-d — Shadow Mode and Slow Speeds

The arm is calibrated. The driver responds. The code that worked in
sim is ready to run on real.

**Do not let it run at full speed yet.** First it runs *without
moving*, then it runs *slowly*, then it runs at normal speed. Each
phase is a filter for a different class of bug.

This file is the protocol for the first day or two on real hardware.

## What you need before this step

- Real arm running through `ros2_control` from
  [02-b](02-b-ros2-control-driver-swap.md).
- Camera + hand-eye calibration done in
  [02-c](02-c-hand-eye-and-base-calibration.md).
- Your sim-validated task code from
  [01-d](01-d-scripted-first-task.md) /
  [01-e](01-e-fake-perception-in-sim.md), ready to point at real.
- **A hand on the e-stop.** Always. Until the cell is signed off.

## The three phases

| Phase | Code runs | Arm moves | Operator |
|-------|-----------|-----------|----------|
| **Shadow** | yes | no | hand on e-stop |
| **Slow** | yes | yes — at ≤ 25% | hand on e-stop |
| **Normal** | yes | yes — at full speed | nearby, alert |

You move from one phase to the next only when the previous succeeds
**three times in a row**.

## Shadow mode — "what would it have done?"

The arm is connected. The task code runs. Perception runs. The
planner plans. But the **trajectory is not executed.**

How you do it:

- In MoveIt, set `execute=false` (or use the "Plan" button without
  "Execute" in RViz).
- In code, call the planner and **log** the resulting trajectory to a
  rosbag without sending it.
- Confirm:
  - Each plan succeeds.
  - The first joint angle of each trajectory matches the current
    joint state (otherwise the arm would jerk).
  - The trajectory stays inside joint limits and avoids known
    collision objects.
  - The final pose lands near the expected target (use a virtual
    "ghost" arm in RViz).

What you're filtering out here: code that uses **wrong frames**, a
**stale calibration**, or perception that returns garbage.

Run **20 shadow runs** with the object in different positions.
Inspect the trajectory logs. Fix any plan that looks weird.

## Slow speeds — "now move it, but slowly"

You're confident the plans are sane. Time to actually execute.

Turn velocity scaling down:

- **`speed_scaling: 0.25`** in `controllers_real.yaml` from
  [02-b](02-b-ros2-control-driver-swap.md).
- Or use `MoveItCpp::set_max_velocity_scaling_factor(0.25)` /
  `arm.set_max_velocity_scaling_factor(0.25)` in `moveit_py`.
- **Acceleration scaling** to 0.25 as well.

What you watch for:

- **Self-collision** — RViz refused but real arm collided? Joint
  limits in URDF probably don't match real.
- **Table collision** — the arm reaches under or through the table.
  Add the table as a collision object.
- **Cable snag** — first run usually finds the one cable you didn't
  route well.
- **Gripper timing** — closes too late, drops the object, or closes
  too early on the way down. Adjust the `gripper_close` delay.
- **Pose offset** — the gripper tip lands 8 mm to the left of the
  object. Your hand-eye calibration is off. Go back to
  [02-c](02-c-hand-eye-and-base-calibration.md).

Run **20 slow-speed pick attempts** with the object in different
positions. Compute success rate.

If success rate is below ~80%, you have a sim-to-real gap to fix.
The most common are calibration error, gripper timing, and missing
collision objects in the planning scene.

## Ramp the speed

Once you've passed the 20-pick test at 25%, ramp speed:

- 25% → 50% (run 10 picks)
- 50% → 75% (run 10 picks)
- 75% → 100% (run 20 picks)

At each step, watch for new failure modes — sometimes a higher
velocity exposes a planning issue (waypoints too sparse, gripper
inertia at the end of a fast move).

## Operator behaviour during these phases

For shadow and slow phases, the human:

- Stands **outside** the arm's swept volume, with a clear line of
  sight.
- Keeps **a hand on the e-stop button** for every motion.
- Has the **vendor pendant powered on** with "emergency stop" path
  active.
- Does not allow **bystanders** in the cell.

For normal-speed runs:

- Operator is **nearby** and alert.
- E-stop is **reachable** within one step.
- Other humans are outside the safety perimeter.

This is *informal* safety. The proper safety case is
[08-safety-validation.md](08-safety-validation.md) — but the rules
above are the floor for any first-time bring-up.

## Watch the logs continuously

- `ros2 topic echo /joint_states` — confirms the arm is reporting.
- `/controller_manager/diagnostics` or `/diagnostics` — surfaces
  driver issues early.
- Vendor pendant log — sometimes the only place a fault is reported.

If anything looks unusual, **e-stop**, investigate, fix, restart from
the previous phase. No "let's see if it recovers."

## Output of this step

```
Shadow-run plan success rate:    ___ / 20
Trajectory log path:             ___
Calibration touch test re-passes: yes / no
Slow-speed pick success rate:    ___ / 20 at 25%
Failure modes seen:              ___
Speed ramp results:              25%, 50%, 75%, 100% — pass rates: ___
Self-collision count:            ___
Table-collision count:           ___
E-stop tested before phase 1?:    yes / no
Operator training done?:          yes (who: ___ ) / no
```

## Common mistakes

1. **Skipping shadow mode.** "I'll just go slow." Skip a phase, find
   a bug at speed, expensive lesson.
2. **No e-stop check before the first motion.** Press the e-stop *now*
   and confirm the arm stops. Don't wait for an emergency.
3. **Velocity scaling forgotten on a redeploy.** A new launch file
   defaults to 100% and surprises everyone. Lock it in code.
4. **First motion to a far-away pose.** Always plan-to-`HOME` first
   so the first move is short and predictable.
5. **Single operator, no second person.** Bring a buddy. They watch,
   you operate.
6. **Treating "it picked once" as success.** Twenty runs. Compute the
   rate.

## What's next

The cell runs reliably at normal speed under supervision. Time to
ramp toward unattended operation — the **phased rollout** plan.

→ Next: [02-e-phased-rollout.md](02-e-phased-rollout.md)
