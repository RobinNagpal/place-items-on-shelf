# 01-e — Fake Perception in Sim

Your hard-coded pick works. Now you make the task **read the
object's pose from a perception input**, like real life — except the
"perception" is still fake. It's just a small node that *looks at
the simulator's ground truth* and publishes it as if a real detector
had produced it.

The point: the rest of your code already speaks "perception", so
when real perception lands later, you swap the fake node for a real
one and nothing else changes.

## Why bother — why not skip straight to real perception?

Real perception (YOLO, depth + segmentation, fiducials) adds a
dozen new failure modes at once: bad lighting, slow inference,
jitter, missed frames. You don't want to debug those at the same
time as your task code.

So you start with **a fake node** that publishes a perfect pose at
a steady rate, and write your task code against *that*. When you
swap in real perception later, only the perception node changes.

## What you need before this step

- A working scripted task from
  [step 4](04-scripted-first-task.md).
- A clear decision on the **shape** of the perception output —
  usually one of:
  - **A single pose** message.
  - **A list of detections** with bounding boxes.
  - **A transform broadcast** — one frame per object.

Pick one *now* and stick with it. The decision propagates everywhere.

## The fake-perception node — what it does

A tiny node that:

1. Reads the simulator's **ground-truth** object pose.
2. Adds optional noise (zero-mean Gaussian, a few mm and a few °).
3. Publishes on the agreed perception channel at the agreed rate
   (e.g. 30 Hz).

How you read ground truth depends on the simulator:

- **Gazebo** — subscribe to the system pose topic and filter for
  your object's model name.
- **Isaac Sim** — query the prim's world transform from the
  editor's Python API.
- **MuJoCo** — read the body's position directly.
- **Webots / CoppeliaSim** — equivalent API call in the script
  attached to the object.

## Add noise on purpose

Real perception will give you a pose ±5–20 mm off. If your task
code only works with a perfect pose, you'll watch it fail the
moment real perception lands.

A reasonable noise model for the first sim pass:

- **Translation:** ±5 mm Gaussian per axis.
- **Rotation:** ±5° Gaussian per axis.
- **Drop rate:** 2% — every 50th frame returns nothing (a dropped
  detection).
- **Latency:** 100 ms — publish *yesterday's* pose, simulating a
  slow detector.

Expose these as run-time parameters so you can crank them up later
for stress testing.

## Swap the task code to consume perception

In [step 4](04-scripted-first-task.md) you hard-coded the grasp
pose. Now:

1. Subscribe to your perception channel in the task node.
2. Wait until a pose arrives (with a timeout — important).
3. Use it as the `object_pose` argument to your pick function.
4. **Re-read the pose** after each motion stage in case the object
   moves between stages (it shouldn't, in sim, but real life will).

If perception goes silent for N seconds, **abort and return to
home.** No pose = no pick.

## Verify it end-to-end

Run the task three times. Each time, before launch, **move the
object in the sim** to a different pose (drag it in the visualiser,
or use the simulator's "set pose" API).

The task should pick it from the new pose every time, without code
changes. If it doesn't, your task code is still using a hard-coded
pose somewhere.

## Output of this step

```
Perception message shape:       single pose / detection array / transform
Channel name:                   ___
Publish rate:                   ___ Hz
Ground-truth source:            simulator system topic / scripted query / direct body read
Noise added (translation, m):   ___
Noise added (rotation, deg):    ___
Drop rate (%):                  ___
Latency added (ms):             ___
Task adapts to moved object?:   yes / no
Timeout on missing perception:  ___ s
```

## Common mistakes

1. **No noise.** Code that works on perfect ground truth breaks on
   real perception. Add noise on day one.
2. **No drop / no-pose handling.** Real perception drops frames.
   Your task code must tolerate "no detection right now."
3. **Subscribing once at startup, not re-querying.** Object can
   move between attempts in real life.
4. **Different channel name in fake vs planned-real.** Lock the
   name now. If your real perception will publish on
   `/detections`, your fake publishes on `/detections`.
5. **Hidden hard-coded pose still in task code.** Grep for any
   pose literal in the task source.

## What's next

The task picks from a moving object, with noisy perception, in sim.
Now you **stress-test** the whole thing.

→ Next: [06-stress-test-in-sim.md](06-stress-test-in-sim.md)
