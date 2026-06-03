# 01-c — Bring Up MoveIt in Sim

You have a virtual cell. You can see the arm sit on the table. But
right now the arm only moves if you drag its joints by hand. This
step gives the arm a planner — so you can say "go to this pose" and
the arm figures out *how*.

That planner is **MoveIt 2** (Layer 3
[`04-motion-planning.md`](../03-software-stack/04-motion-planning.md))
for almost everyone.

## What you need before this step

- Working virtual cell from [01-b](01-b-build-the-virtual-cell.md).
- ROS 2 sourced, the arm description package built.
- MoveIt 2 installed for your ROS 2 distro:
  `sudo apt install ros-${ROS_DISTRO}-moveit`.

## The two MoveIt configurations you might already have

1. **The vendor already ships one** — check for a
   `<arm>_moveit_config/` package. UR, Franka, Kinova, myCobot, etc.
   all ship one. If you have it, use it. Skip to "Launch and test."
2. **You don't have one** — you generate it once with
   `moveit_setup_assistant`. Below.

## Generate a MoveIt config (only if no vendor config exists)

```
ros2 launch moveit_setup_assistant setup_assistant.launch.py
```

A GUI opens. Walk through these tabs in order:

1. **Load URDF** — point at the URDF / xacro from [01-b](01-b-build-the-virtual-cell.md).
2. **Self-Collisions** — click "Generate". MoveIt computes pairs that
   never collide and skips them at run time.
3. **Virtual Joints** — add a `world → base_link` fixed joint.
4. **Planning Groups** — add one named `<arm>` whose chain is
   `base_link` → `tool0` (or your wrist link).
5. **Robot Poses** — define `home`, `ready`, `tuck` poses for later
   testing.
6. **End Effectors** — declare the gripper group if your arm has one.
7. **Controllers** — pick `JointTrajectoryController` (or
   `position_controllers/JointGroupPositionController` for direct
   position).
8. **Generate Package** — save as `<arm>_moveit_config`.

Build the new package:

```
cd ~/ros2_ws && colcon build --packages-select <arm>_moveit_config
source install/setup.bash
```

## Launch MoveIt against the simulator

A typical `demo_gazebo.launch.py` (vendor packages usually ship one)
brings up:

- The Gazebo world from [01-b](01-b-build-the-virtual-cell.md).
- The `robot_state_publisher` (turns joint angles into `tf`).
- `gz_ros2_control` (the sim hardware interface — see
  [02-b](02-b-ros2-control-driver-swap.md)).
- `move_group` (the planner).
- RViz 2 with the MoveIt motion-planning plugin.

Run it:

```
ros2 launch <arm>_moveit_config demo_gazebo.launch.py
```

Wait for "You can start planning now!" in the RViz status line.

## Test it by hand in RViz

In the RViz MoveIt panel:

1. Open the **Motion Planning** panel.
2. Drag the **interactive marker** at the end effector to a new pose.
3. Click **Plan**. RViz shows the proposed trajectory as a moving
   ghost arm.
4. Click **Execute**. The real (simulated) arm should follow.
5. Click **Update** in the **Planning Scene** tab to load collision
   objects.

If the arm moves to the target, MoveIt is healthy.

## Things to check before moving on

- **Self-collision flagging.** Drag the gripper into the base. RViz
  should refuse to plan ("goal in self-collision").
- **Joint limits.** Drag toward a joint extreme. RViz should refuse
  past the URDF's limit.
- **Table as a collision object.** Add it as a `box` in the
  Planning Scene tab. Verify the planner avoids it.
- **A "home" pose plan** works in one click.

If any of these don't behave, fix them now. Every later step assumes
MoveIt is correct.

## Tools you'll use a lot

- **RViz MoveIt panel** — the interactive interface to MoveIt.
- **`ros2 service call /plan_kinematic_path`** — call the planner from
  the command line for scripted tests.
- **`moveit_py`** — the Python API for MoveIt 2. The path most task
  code uses.
- **`MoveGroupInterface` (C++)** — for production code.
- **`MoveIt Task Constructor`** — for multi-stage pick-and-place
  pipelines (used in [01-d](01-d-scripted-first-task.md)).

## Output of this step

```
MoveIt config package:       <arm>_moveit_config (version: ___ )
Planning group(s):           <arm>, <gripper>
Default planner:             RRTConnect / STOMP / Pilz / ___
IK solver:                   KDL / TRAC-IK / IKFast / ___
Self-collisions generated:   yes / no
Reference poses defined:     home, ready, ___
Sim launch file:             <arm>_moveit_config/launch/demo_gazebo.launch.py
RViz Plan + Execute works:   yes / no
Joint limits honoured:       yes / no
Self-collision blocks plan:  yes / no
```

## Common mistakes

1. **Default KDL IK.** Switch to TRAC-IK or PickIK. KDL silently
   misses solutions on near-singular poses.
2. **No table in the planning scene.** Planner happily plans through
   the table. Add it as a collision object.
3. **One huge planning group containing everything.** Keep `<arm>`
   and `<gripper>` separate.
4. **Joint limits in URDF wider than reality.** The real arm will
   collide with itself. Trim limits to match the real arm's stops.
5. **Skipping the RViz drag-and-plan check.** If it doesn't work
   here, it definitely won't work from your task code.
6. **Vendor MoveIt config copied without checking the URDF version.**
   A URDF mismatch causes silent IK failures.

## What's next

You can plan motions one click at a time. Real tasks aren't one click;
they're a *sequence* (approach, descend, grasp, lift, move, release).
Time to write that sequence in code.

→ Next: [01-d-scripted-first-task.md](01-d-scripted-first-task.md)
