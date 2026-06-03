# 04-f — Evaluate and Iterate

You have a trained policy. The question is **does it actually work**.
The honest answer almost always is "not yet, but here's how to get
there."

Evaluation is a two-step ritual: **sim first**, **real second**.
Iteration is **fail-then-add-50** — find what the policy can't do,
record more demos for exactly that, retrain, repeat.

## What you need before this step

- A trained policy from [step 5](05-pick-and-fine-tune-policy.md).
- The sim cell from [step 6 of 01-simulation-first-development](../01-simulation-first-development/06-stress-test-in-sim.md) still
  available.
- The real cell from [03](03-system-integration-on-real.md) ready.
- The eval split from [step 4](04-curate-and-clean-dataset.md).

## Step 1 — sim evaluation

Before risking real-hardware time, evaluate in sim. Load the
**same** URDF, the **same** controllers, the **same** camera setup;
swap in the policy as the action source.

How:

- Replace the `MoveIt` planner / scripted task with a node that:
  - Subscribes to camera + joint-state topics.
  - Feeds them into the policy.
  - Publishes the policy's action as a trajectory command.
- Use the sim harness from [step 6 of 01-simulation-first-development](../01-simulation-first-development/06-stress-test-in-sim.md) for
  the experimental scaffolding.

Run **100 episodes** in sim with varied object positions. Compute:

- **Pick success rate.**
- **Cycle time.**
- **Failure-mode breakdown** (didn't reach, missed grasp, dropped,
  hit table, etc.).

If sim success < 60%, something fundamental is off — the dataset, the
training, or the action / observation shape. Don't go to real yet.

## Step 2 — real evaluation (slow, supervised)

In real, repeat exactly what the bring-up protocol from
[step 4 of 02-sim-to-real-bridge](../02-sim-to-real-bridge/04-shadow-mode-and-slow-speeds.md) and
[step 5 of 02-sim-to-real-bridge](../02-sim-to-real-bridge/05-phased-rollout.md) demanded for scripted code:

- Start at **25% speed scaling**.
- Operator hand on e-stop.
- Run **20 episodes**. Note success / failure / what went wrong.

A policy that ran at 95% in sim usually starts at **50–70% on real**.
That gap is the sim-to-real distribution shift. Closing it is the
iteration work.

If real success < 30%, do **not** keep cranking speed or running more
episodes. Go back to the data — what's the policy not seeing during
training that real has?

## The fail-then-add-50 loop

The single most effective iteration discipline. Each cycle:

1. **Identify the worst failure mode.** Watch every failure carefully.
   Cluster them. ("Misses the object when it's at the back-right.")
2. **Record 50 new demos** that specifically cover that situation.
3. **Re-curate** to merge into your dataset, increment the version
   (`v2c`).
4. **Re-fine-tune** from the previous checkpoint (don't start from
   scratch).
5. **Re-evaluate** on the original eval split *plus* a new "regression"
   subset built from the failure mode.
6. **Repeat** until the failure rate on that mode drops below your
   target.

Three to six cycles is typical to go from "kind of works" to
"production-acceptable." Each cycle is one or two days of work.

## What to track between iterations

A small table you keep up to date:

| Version | Demos | Sim success | Real success | Notes |
|---------|-------|-------------|--------------|-------|
| v1c | 140 | 75% | 45% | Misses right-side objects |
| v2c | 190 | 88% | 71% | Better right side. Drops on shiny objects. |
| v3c | 245 | 92% | 86% | Stable across lighting |

Version the dataset, the trained policy, the eval results, **and the
commit hash** that ran the training. Without all four you can't
reproduce a result.

## Stop-loss criteria

Sometimes iteration plateaus and the policy still isn't good enough.
Know when to stop and try something else:

- After **5 cycles** with < 5% improvement → consider a different
  policy architecture (Diffusion Policy if you started with ACT, or
  vice versa).
- After **10 cycles** still under your target → consider a foundation-
  model fine-tune (OpenVLA, Pi-0) rather than from-scratch.
- If the failure mode is **information not available to the policy**
  (no depth camera, no force sensor) → add the sensor, recollect.
- If the failure mode is **physically impossible for the gripper** →
  the answer isn't more demos; it's hardware.

## When the policy is good enough

You're ready to move to operational phases (
[02-e — phased rollout](../02-sim-to-real-bridge/05-phased-rollout.md) and
[06](06-pilot-deployment.md)) when:

- Sim success ≥ 95%.
- Real success ≥ 90% on a held-out eval set.
- Failure modes are **understood** — no mysterious failures.
- Cycle time meets the Layer-1 spec.
- The policy runs at the target rate on the deployment hardware.

If those are true, the IL workflow is done.

## A practical merge-into-deployment

In production, you usually don't deploy the bare policy. You wrap it:

- **Sanity bounds** — if the predicted action would take the arm past
  a joint limit, clip or reject.
- **Speed scaling at deploy time** — start at 50%, ramp.
- **A fallback** — if the policy returns NaN, an out-of-distribution
  observation arrives, or the camera drops, fall back to a scripted
  "go-to-HOME" routine.
- **A confidence gate** — for VLAs that emit confidence; for ACT, use
  agreement across an action chunk as a proxy.

Don't let the policy run without these. AI fails silently; safety
nets fail loudly.

## Output of this step

```
Sim eval (100 ep):           ___ % success
Real eval (20 ep at 25%):    ___ % success
Iteration cycle count:        ___
Per-cycle success curve:      ___
Final dataset version:        ___
Final policy version:         ___
Failure modes remaining:      ___
Cycle time (mean / p95):      ___ s / ___ s
Deploys with which wrappers:  sanity bounds / fallback / confidence gate
Ready for phased rollout?:    yes / no — gating issue: ___
```

## Common mistakes

1. **Going to real before sim looks good.** Real time is expensive,
   sim time is free.
2. **No fail-mode clustering.** "It just fails sometimes" → record
   randomly, no improvement. Cluster first.
3. **Training from scratch on every iteration.** Always continue
   from the previous checkpoint.
4. **Adding 200 random demos per cycle.** 50 targeted demos beat 200
   random.
5. **Stopping when the policy "looks good" subjectively.** Numbers
   only. 90% real success on a held-out set, or no go.
6. **Deploying without wrappers.** Bare-policy deploy is a recipe
   for a daytime e-stop.

## What's next

The policy is good enough. You're back on the main bring-up track.
Run through the checklist before letting the cell go to pilot.

→ Next: [05-bring-up-checklist.md](../05-bring-up-checklist.md)
