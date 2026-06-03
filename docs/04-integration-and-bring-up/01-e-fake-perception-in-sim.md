# 01-e — Fake Perception in Sim

Your hard-coded pick works. Now you make the task **read the object's
pose from a perception input**, like real life — except the
"perception" is still fake. It's just a small node that *looks at the
simulator's ground truth* and publishes it as if a real detector had
produced it.

The point: the rest of your code already speaks "perception", so when
real perception lands later, you swap the fake node for a real one
and nothing else changes.

## Why bother — why not skip straight to real perception?

Real perception (YOLO, depth + segmentation, ArUco) adds a dozen new
failure modes at once: bad lighting, slow inference, jitter, missed
frames. You don't want to debug those at the same time as your task
code.

So you start with **a fake node** that publishes a perfect pose at a
steady rate, and write your task code against *that*. When you swap
in real perception later, only the perception node changes.

## What you need before this step

- A working scripted task from [01-d](01-d-scripted-first-task.md).
- A clear decision on how perception output will be shaped — usually
  one of:
  - **`geometry_msgs/PoseStamped`** — single-object pose.
  - **`vision_msgs/Detection3DArray`** — multi-object with bounding
    boxes.
  - **`tf2`** broadcast — publish a frame per object.

Pick one *now* and stick with it. The decision propagates everywhere.

## The fake-perception node — what it does

A tiny ROS 2 node that:

1. Subscribes to or queries the simulator's **ground-truth object
   pose**.
2. Adds optional noise (zero-mean Gaussian, a few mm and a few °).
3. Publishes on the agreed perception topic at the agreed rate
   (e.g. 30 Hz).

Three implementations, all small:

### A — Gazebo: read from `/world/<world>/pose/info`

Gazebo Harmonic publishes every model's pose on a system topic. Your
node subscribes, filters for the object's model name, and republishes
in your perception format.

### B — Isaac Sim: scripted Python in the editor

Isaac's Python API gives you `xform.GetWorldTransform()` for any prim.
Run a small async task each tick that publishes via `rclpy`.

### C — MuJoCo: poll `data.body('object').xpos`

MuJoCo gives you body positions in C / Python directly. Wrap in a
publisher node.

## Add noise on purpose

Real perception will give you a pose ±5–20 mm off. If your task
code only works with a perfect pose, you'll watch it fail the moment
real perception lands.

A reasonable noise model for the first sim pass:

- **Translation:** ±5 mm Gaussian per axis.
- **Rotation:** ±5° Gaussian per axis.
- **Drop rate:** 2% — every 50th frame returns nothing (a dropped
  detection).
- **Latency:** 100 ms — publish *yesterday's* pose, simulating a slow
  detector.

Make these noise parameters tuneable as ROS 2 parameters so you can
crank them up later for stress testing.

## Swap the task code to consume perception

In [01-d](01-d-scripted-first-task.md) you hard-coded the grasp pose.
Now:

1. Subscribe to your perception topic in the task node.
2. Wait until a pose arrives (with a timeout — important).
3. Use it as the `object_pose` argument to your pick function.
4. **Re-read the pose** after each motion stage in case the object
   moves between stages (it shouldn't, in sim, but real life will).

If perception goes silent for N seconds, **abort and return to home.**
No pose = no pick.

## Verify it end-to-end

Run the task three times. Each time, before launch, **move the object
in the sim** to a different pose (drag it in RViz, or call
`gz service -s /world/default/set_pose`).

The task should pick it from the new pose every time, without code
changes. If it doesn't, your task code is still using a hard-coded
pose somewhere.

## Output of this step

```
Perception message type:        PoseStamped / Detection3DArray / tf2
Topic name:                     /perception/object_pose / /detections / N/A
Publish rate:                   ___ Hz
Ground-truth source:            Gazebo pose/info / Isaac script / MuJoCo body
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
2. **No drop / no-pose handling.** Real perception drops frames. Your
   task code must tolerate "no detection right now."
3. **Subscribing once at startup, not re-querying.** Object can move
   between attempts in real life.
4. **Different topic name in fake vs planned-real.** Lock the name
   now. If your real perception will publish on `/detections`, your
   fake publishes on `/detections`.
5. **Hidden hard-coded pose still in task code.** Grep for any
   `Pose()` literal in the task source.

## What's next

The task picks from a moving object, with noisy perception, in sim.
Now you **stress-test** the whole thing.

→ Next: [01-f-stress-test-in-sim.md](01-f-stress-test-in-sim.md)
