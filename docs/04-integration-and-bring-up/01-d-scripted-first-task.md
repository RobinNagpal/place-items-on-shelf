# 01-d — Scripted First Task

You have MoveIt planning in sim. Time to write the **first end-to-end
task** — a Python or C++ script that picks up an object and places it
somewhere else. Hard-coded poses, no perception, no AI.

This is the simplest possible "task." It exists to verify the
plumbing: task code → MoveIt → controllers → simulator. If it works
here, everything later can build on it. If it doesn't, the rest of
the project is on sand.

## What you need before this step

- Working MoveIt + sim from [01-c](01-c-bring-up-moveit-in-sim.md).
- A gripper driver (sim plugin or vendor driver). If you don't have
  one, fake it with `ros2_control`'s `GripperActionController`.
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

Three reasonable ways to write the script:

### A — `moveit_py` (Python)

The newest, most documented Python API for MoveIt 2. Concise. Good
for prototypes.

Sketch:

```python
from moveit.planning import MoveItPy
from geometry_msgs.msg import PoseStamped

moveit = MoveItPy(node_name="pick_place_demo")
arm = moveit.get_planning_component("manipulator")
arm.set_start_state_to_current_state()
arm.set_goal_state(pose_stamped_msg=above_pose, pose_link="tool0")
plan = arm.plan()
if plan: arm.execute()
```

**Best for:** quick scripts, demos, research.

### B — `MoveGroupInterface` (C++)

The mature C++ API. More verbose but the canonical reference. Most
example repos still use it.

**Best for:** production code, real-time-adjacent tasks, when you
want the lowest-level access without going to `move_group`'s service
calls directly.

### C — **MoveIt Task Constructor (MTC)**

A framework for **stitching motion stages together.** You describe
each stage (`MoveTo`, `Generate Grasp Pose`, `Connect`, `Move Linear`),
MTC figures out a valid sequence.

**Best for:** real pick-and-place. MTC saves you from manually
debugging each stage's failure mode. Slightly higher learning curve,
much less fragile.

If you're starting fresh, try `moveit_py` first; if the task gets
non-trivial (multiple grasp candidates, retries), move to MTC.

## A minimum task code structure

Regardless of approach, your task code should:

- **Use named pose constants** at the top of the file (`HOME`,
  `OBSERVE`, `PRE_GRASP`, …). Never inline magic numbers.
- **Use a real frame, not coordinates only.** Pose targets are
  `PoseStamped(header.frame_id="world")` — make the frame explicit.
- **Wrap each step in a try / log / abort pattern.** If a plan
  fails, stop and log — don't push forward.
- **Be re-runnable.** A second run after a failure should reset to
  `HOME`, not assume the previous state.
- **Take object pose as an argument**, not hard-coded — even though
  this task hard-codes the object location, structure the function
  signature so you can swap in a real detection later.

## Gripper handling in sim

If your gripper driver is fake, model it as a simple
`GripperActionController` with `open` / `close` goals. In Gazebo, this
works via `gz_ros2_control` + a joint friction trick. Don't try to
simulate complex grasping physics yet — for the first task it's enough
that the object follows the gripper when "closed."

For more realistic sim grasping later, look at:

- **gz-sim's `AttachLink` plugin** — attach the object to the gripper
  link when the gripper closes.
- **Isaac Sim Grasp**: built-in suction / parallel-jaw grasp helpers.
- **MuJoCo equality constraints**: declarative attach / detach.

## Running and verifying

1. Launch the world + MoveIt (`demo_gazebo.launch.py`).
2. Run the task: `ros2 run <pkg> pick_place_demo`.
3. Watch RViz — every planned trajectory should appear as a ghost
   arm, then execute.
4. Check the object lands at the drop pose.
5. Look at `ros2 topic echo /<planning_group>/execute_trajectory/_action/status`
   for the action status of each step.

Run it **three times in a row** without restarting Gazebo. If any of
the three fails differently, you have a non-deterministic bug — fix
that before moving on.

## Output of this step

```
Task framework:        moveit_py / MoveGroupInterface (C++) / MTC
Task source file:      ___
Named pose constants:  HOME, PRE_GRASP, ___ (count: ___ )
Gripper interface:     GripperActionController / vendor / fake AttachLink
Cartesian path used?:  yes (compute_cartesian_path) / no
Plan-time budget:      ___ s
Pass rate (3 runs):    ___/3
Action status logging: yes / no
```

## Common mistakes

1. **Hard-coded object pose in three places.** Define it once.
2. **No retreat after grasp.** The next plan starts from a bad pose
   and fails mysteriously.
3. **`compute_cartesian_path` with a too-loose `eef_step`.** The arm
   "jumps" between waypoints. Use 1–5 mm.
4. **Plan + Execute with no result check.** A failed plan returns
   silently and the next stage runs from the wrong state.
5. **Closing the gripper before the arm has stopped.** Use the
   trajectory result to confirm motion complete before sending the
   gripper command.
6. **Skipping the three-run check.** A test that passes once is
   half-broken.

## What's next

The task works with a hard-coded object pose. In real life, the
object isn't at a fixed pose. Even in sim, you want to **simulate**
that — by faking the perception output.

→ Next: [01-e-fake-perception-in-sim.md](01-e-fake-perception-in-sim.md)
