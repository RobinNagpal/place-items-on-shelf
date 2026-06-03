# 01-c — Bring Up the Motion Planner in Sim

You have a virtual cell. You can see the arm sit on the table. But
right now the arm only moves if you drag its joints by hand. This
step gives the arm a **planner** — so you can say "go to this pose"
and the arm figures out *how*.

For most ROS 2 projects, that planner is **MoveIt 2** (Layer 3
[`04-motion-planning.md`](../../03-software-stack/04-motion-planning.md)).
This file walks you through bringing MoveIt up against the simulator.

If you're **not** on ROS 2, or MoveIt isn't the right fit, see
"Alternatives to MoveIt" near the bottom — the rest of the workflow
still applies, you just swap the planner.

## What you need before this step

- Working virtual cell from
  [step 2](02-build-the-virtual-cell.md).
- A motion planner available for your stack (MoveIt 2 on ROS 2
  Jazzy / Humble — or one of the alternatives below).

## The two MoveIt configurations you might already have

1. **The vendor already ships one** — check for an
   `<arm>_moveit_config/` package. UR, Franka, Kinova, myCobot, etc.
   all ship one. If you have it, use it.
2. **You don't have one** — you generate it once with the **MoveIt
   Setup Assistant**, a GUI that takes your URDF and a few clicks
   and emits a complete `<arm>_moveit_config` package.

## What the MoveIt setup actually configures

Whether you generate it or use a vendor package, the configuration
captures these decisions:

- **Self-collision matrix** — pairs of links that can never collide,
  so the planner skips checking them.
- **Virtual joint** — `world → base_link` (usually fixed).
- **Planning groups** — at minimum one named `<arm>` for the
  kinematic chain `base_link → tool0`, and a second for the
  `<gripper>` if you have one.
- **Reference poses** — `home`, `ready`, `tuck` for testing.
- **Controllers** — typically a joint-trajectory controller for the
  arm; an action controller for the gripper.
- **Planning algorithm and IK solver** — RRTConnect (default
  planner); **TRAC-IK** or **PickIK** for inverse kinematics. The
  default KDL IK silently misses solutions on near-singular poses —
  switch.

If you go through Setup Assistant, walk those tabs in order and save
the package as `<arm>_moveit_config`.

## Launch the planner against the simulator

A typical "sim demo" launch (vendor packages usually ship one) brings
up, all in one process group:

- The simulator world from [step 2](02-build-the-virtual-cell.md).
- A node that turns joint angles into transforms.
- The simulator's hardware interface (see
  [step 2 of 02-sim-to-real-bridge](../02-sim-to-real-bridge/02-ros2-control-driver-swap.md) for the swap to real
  later).
- The MoveIt planner.
- The visualiser (RViz 2) with the MoveIt motion-planning plugin.

Wait for "You can start planning now!" in the visualiser before
testing.

## Test it by hand in the visualiser

1. Open the **Motion Planning** panel.
2. Drag the **interactive marker** at the end effector to a new
   pose.
3. **Plan.** The visualiser shows the proposed trajectory as a
   ghost arm.
4. **Execute.** The simulated arm follows the plan.
5. In the **Planning Scene** tab, add collision objects (the table)
   and verify the planner avoids them.

If the arm moves to the target, the planner is healthy.

## Things to check before moving on

- **Self-collision flagging.** Drag the gripper into the base. The
  planner should refuse ("goal in self-collision").
- **Joint limits.** Drag toward a joint extreme. The planner should
  refuse past the description's limit.
- **Table as a collision object.** Add it; verify the planner
  avoids it.
- **A "home" pose plan** works in one click.

If any of these don't behave, fix them now. Every later step assumes
the planner is correct.

## Alternatives to MoveIt

MoveIt is the dominant choice on ROS 2, but it's not the only one.
Pick the right tool for your stack:

| Stack | Common motion-planning choice |
|-------|------------------------------|
| **ROS 2, general manipulation** | MoveIt 2 (this file). |
| **Vendor-native programming** | UR PolyScope / URScript, Franka Desk, FANUC TP, ABB RobotStudio, KUKA Sunrise. The pendant / vendor IDE *is* the planner. |
| **Drake** | Drake's own trajectory optimisation (TrajOpt) and inverse kinematics. Strong on contact-rich manipulation. |
| **Pinocchio / Crocoddyl** | C++ rigid-body library + optimisation-based planning. Common in research, especially humanoids and legged robots. |
| **OMPL directly** | Sampling-based planner library that MoveIt uses internally. Wrap it yourself for niche cases. |
| **OpenRAVE** | Legacy; only in inherited projects. |
| **MoveIt 1 (ROS 1)** | Maintained for old projects; new code targets MoveIt 2. |

Whichever you pick, the rest of the simulation-first workflow stays
the same — sim, planner, scripted task, fake perception, stress
test.

## Tools you'll use a lot

- The visualiser's interactive marker (RViz 2 on ROS 2).
- A scripted interface to the planner — `moveit_py` (Python) or
  `MoveGroupInterface` (C++) on ROS 2; the vendor's API on a
  vendor-native stack.
- **MoveIt Task Constructor (MTC)** — for multi-stage
  pick-and-place pipelines (see
  [step 4](04-scripted-first-task.md)).

## Output of this step

```
Motion planner used:         MoveIt 2 / Drake / vendor / other (___)
Planner config package:      <arm>_moveit_config (version: ___ )
Planning groups:             <arm>, <gripper>
Default planner algorithm:   RRTConnect / STOMP / Pilz / TrajOpt / ___
IK solver:                   KDL / TRAC-IK / IKFast / PickIK / ___
Self-collisions generated:   yes / no
Reference poses defined:     home, ready, ___
Plan + Execute works:        yes / no
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
4. **Joint limits in the description wider than reality.** The real
   arm will hit its stops. Trim limits to match.
5. **Skipping the drag-and-plan check.** If it doesn't work here,
   it definitely won't work from your task code.
6. **Vendor config copied without checking the URDF version.** A
   URDF mismatch causes silent IK failures.

## What's next

You can plan motions one click at a time. Real tasks aren't one
click; they're a *sequence* (approach, descend, grasp, lift, move,
release). Time to write that sequence.

→ Next: [04-scripted-first-task.md](04-scripted-first-task.md)
