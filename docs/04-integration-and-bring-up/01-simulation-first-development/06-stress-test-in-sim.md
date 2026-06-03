# 01-f — Stress Test in Sim

The happy path works. Time to break it on purpose, in sim, where
breaking it is free.

The point of this step is to **find every failure your code has**
before real hardware finds them for you. Real hardware finds them at
3 a.m., during a demo, when the customer is in the room.

## What you need before this step

- The full simulation-first workflow working through
  [step 5](05-fake-perception-in-sim.md):
  task code consuming (noisy, possibly dropped) perception, executing
  a pick-and-place against a virtual cell.
- A way to run the task **many times in a row** without manual reset.

## The five stress dimensions

Vary one at a time. Note which makes the task fail, in what way.

### 1. Object pose

- Sweep the object across the workspace in a grid (e.g., 5 × 5 over
  the table).
- Rotate it through 0°, 45°, 90°, 135°, 180° about Z.
- Place it near the edge of reach.
- Place it just out of reach (your code should fail *cleanly*, not
  hang).

Target: at least **90% pick success** on the inside-reach grid before
moving on.

### 2. Perception noise

Crank up the noise added by your fake node from [step 5](05-fake-perception-in-sim.md):

- Translation noise: 5 → 10 → 20 → 50 mm.
- Rotation noise: 5° → 15° → 45°.
- Drop rate: 0% → 5% → 25%.
- Latency: 100 ms → 500 ms.

Note the noise level at which success drops below 50%. That's your
real-world budget — if real perception's error exceeds it, you have
work to do before deploying.

### 3. Scene clutter

Add obstacles the planner must avoid:

- A second object next to the target.
- A wall behind the target.
- A bowl the target sits inside.

The planner should either route around them or refuse to plan — never
crash through them.

### 4. Robot state on startup

Run the task from non-`HOME` start states:

- Mid-air poses.
- Near joint limits.
- After a previous failed run.

The first action must always be **plan-to-HOME** and recover.

### 5. Simulator quirks

Test what happens when the sim itself misbehaves:

- Pause / unpause the sim mid-task.
- Drop the camera topic for 1 second.
- Make the gripper finger collide with the object before grasp.

Your code shouldn't lock up. It should log the failure and return to
HOME.

## A run-many-times harness

Don't run these by hand. Build a tiny harness:

- A Python script that:
  - Resets the sim to a known scene (model spawning / repositioning).
  - Randomly samples object pose + noise level + clutter.
  - Launches the task.
  - Records success / failure + timing + which stage failed.
- A CSV / SQLite output.

After 100 runs, look at:

- **Success rate.** Target: 95% on the easy cases.
- **Failure mode distribution.** Plan failures vs. perception
  dropouts vs. wrong grasp.
- **Time per run.** Outliers tell you what's slow.

This harness becomes your **regression test**. Run it on every code
change.

## A reasonable acceptance bar before moving to real

You don't move to real hardware until, in sim, you have:

- **≥ 95% pick success** with realistic noise (e.g. 5 mm, 5°, 2%
  drop).
- **0 collisions** with table, clutter, or itself across 200 runs.
- **Graceful recovery** when perception goes silent or the planner
  fails — no hangs.
- **Reproducible results** — same seed → same outcome.

If you're below the bar, fix the failures in sim. Each one fixed here
saves you a day on real hardware.

## What stays in this file vs. what moves to 02

This file is about *bugs your code has* — fix those here. The next
chapter is about *physics differences between sim and real* (friction,
camera calibration, latency). Don't conflate them. A bug that's
"actually a sim-to-real issue" will *not* be exposed by the harness
above.

## Output of this step

```
Pick success rate (sim):        ___ / 200
Pose-grid coverage (% within reach): ___
Highest tolerated noise:         translation ___ mm, rotation ___ °
Highest tolerated perception drop: ___ %
Self-collision count:            ___
Table-collision count:           ___
Failure-mode breakdown:          plan: ___ , perception: ___ , timing: ___ , other: ___
Harness path:                    ___
Regression seed list:            ___
Acceptance bar met?:             yes / no
```

## Common mistakes

1. **One run, declared "it works".** Run 200.
2. **Same random seed every test.** Use a seed sweep so you find
   distribution edges.
3. **Ignoring the failure mode breakdown.** "50% success" with 49%
   being perception dropouts is very different from being plan
   failures. Diagnose by category.
4. **Adding new code without re-running the harness.** Every change
   regresses something eventually.
5. **Stopping at 95% in sim, assuming real will be similar.** Real
   is always worse. Aim higher in sim than you can tolerate in real.

## What's next

The sim version of your cell works reliably. Time to plug the *real*
arm in.

→ Next: [02-sim-to-real-bridge/01-shared-urdf-and-frames.md](../02-sim-to-real-bridge/01-shared-urdf-and-frames.md)
