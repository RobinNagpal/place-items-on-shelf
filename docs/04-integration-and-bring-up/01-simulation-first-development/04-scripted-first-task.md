# 01-d — Scripted First Task

You have a motion planner working in sim. Time to write the **first
end-to-end task** — a script that picks up an object and places it
somewhere else. Hard-coded poses, no perception, no AI.

This is the simplest possible "task." It exists to verify the
plumbing: task code → planner → controllers → simulator. If it
works here, everything later can build on it. If it doesn't, the
rest of the project is on sand.

## What you need before this step

- Working planner + sim from
  [step 3](03-bring-up-moveit-in-sim.md).
- A gripper interface — vendor driver, sim plugin, or a placeholder
  action controller.
- An object in the scene at a known pose.

## The eight steps of a basic pick-and-place

Every pick-and-place script — yours included — does these in order:

1. **Move to a "home" or "above the cell" pose.** Safe start.
2. **Open the gripper.** Always start with a known gripper state.
3. **Plan to a pre-grasp pose** — ~10 cm above the object, gripper
   pointing down.
4. **Plan a Cartesian descent** straight down to the grasp pose.
5. **Close the gripper.**
6. **Plan a Cartesian retreat** straight up.
7. **Plan to a drop pose** above the bin / drop zone.
8. **Plan a Cartesian descent + open + retreat.**

You only need to write this once. Then you parameterise it.

## Pick a task-writing approach

Three reasonable ways to structure the script:

### A — A high-level Python API

The MoveIt Python API on ROS 2, or the vendor's Python SDK (UR
RTDE, Franka FCI, Kinova Kortex). Concise, good for prototypes.

**Best for:** quick scripts, demos, research.

### B — A C++ API

`MoveGroupInterface` on MoveIt, or the vendor's C++ SDK. More
verbose but the canonical reference. Most example repos still use
it.

**Best for:** production code, real-time-adjacent tasks, when you
want the lowest-level access without going to raw service calls.

### C — MoveIt Task Constructor (MTC), or equivalent task framework

A framework for **stitching motion stages together.** You describe
each stage ("move to", "generate grasp pose", "connect", "move
linear"), and the framework figures out a valid sequence.

**Best for:** real pick-and-place. MTC saves you from manually
debugging each stage's failure mode. Higher learning curve, much
less fragile.

If you're starting fresh, try the high-level Python API first. If
the task gets non-trivial (multiple grasp candidates, retries),
move to a task framework.

## A minimum task code structure

Regardless of approach, your task code should:

- **Use named pose constants** at the top of the file (`HOME`,
  `OBSERVE`, `PRE_GRASP`, …). Never inline magic numbers.
- **Tag every pose with a real frame**, not coordinates alone.
- **Wrap each step in a try / log / abort pattern.** If a plan
  fails, stop and log — don't push forward.
- **Be re-runnable.** A second run after a failure should reset to
  `HOME`, not assume the previous state.
- **Take the object pose as an argument**, even when this task
  hard-codes it. Structure the function so you can swap in a real
  detection later.

## Gripper handling in sim

If your gripper driver is a placeholder, model it as a simple open
/ close action. Each simulator has its own way of "closing the
gripper" without simulating contact physics fully:

- **Gazebo** — `gz_ros2_control` plus a joint friction trick, or
  the `AttachLink` plugin that attaches the object to the gripper
  link when closed.
- **Isaac Sim** — built-in suction / parallel-jaw grasp helpers.
- **MuJoCo** — equality constraints for declarative attach /
  detach.

Don't try to simulate complex grasping physics yet — for the first
task, "object follows the gripper when closed" is enough.

## Running and verifying

1. Launch the world + planner (the "sim demo" launch from
   [step 3](03-bring-up-moveit-in-sim.md)).
2. Start the task.
3. Watch the visualiser — every planned trajectory should appear
   as a ghost arm and then execute.
4. Confirm the object lands at the drop pose.
5. Read the trajectory-action status for each step — every
   "succeeded" should appear; a "failed" anywhere is the bug to
   fix.

Run the task **three times in a row** without restarting the
simulator. If the three runs fail differently, you have a
non-deterministic bug — fix that before moving on.

## Output of this step

```
Task framework:         Python API / C++ API / MTC / vendor SDK
Task source file:       ___
Named pose constants:   HOME, PRE_GRASP, ___ (count: ___ )
Gripper interface:      action controller / vendor / fake attach
Cartesian path used?:   yes / no
Plan-time budget:       ___ s
Pass rate (3 runs):     ___/3
Action status logged:   yes / no
```

## Common mistakes

1. **Hard-coded object pose in three places.** Define it once.
2. **No retreat after grasp.** The next plan starts from a bad
   pose and fails mysteriously.
3. **Cartesian path with a too-loose step.** The arm "jumps"
   between waypoints. Use 1–5 mm.
4. **Plan + Execute with no result check.** A failed plan returns
   silently and the next stage runs from the wrong state.
5. **Closing the gripper before the arm has stopped.** Use the
   trajectory result to confirm motion complete before sending
   the gripper command.
6. **Skipping the three-run check.** A test that passes once is
   half-broken.

## What's next

The task works with a hard-coded object pose. In real life, the
object isn't at a fixed pose. Even in sim, you want to **simulate**
that — by faking the perception output.

→ Next: [05-fake-perception-in-sim.md](05-fake-perception-in-sim.md)
