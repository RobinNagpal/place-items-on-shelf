# Motion Planning

The motion planner is the **brain that turns "go to this pose" into a
sequence of joint angles over time** — without crashing the arm into
anything.

Without a planner, your code says "joint 1 to 30°, joint 2 to -45°…"
manually, for every move. That works for simple demos and falls apart
the moment the workspace has an obstacle or the target moves.

This file is just about which planner to use.

## What a planner actually does

A typical pick-and-place planner takes:

- A **current state** (where every joint is right now).
- A **goal** (pose, joint angles, or "in this region").
- A **world model** (the arm's URDF + nearby obstacles).
- **Constraints** (don't tilt the cup, don't spin the wrist past ±170°).

…and returns a **trajectory**: a smooth time-stamped sequence of joint
angles the arm should track. A separate **controller** (provided by the
arm driver) executes that trajectory at the actual hardware rate.

The planner is offline thinking. The controller is online following.
Keep that split clear.

## What you check, before anything else

- **Sampling vs. optimisation planner?** Sampling planners (OMPL,
  RRTConnect) find *a* path quickly. Optimisation planners (CHOMP,
  STOMP, TrajOpt) find *a smooth* path more slowly. MoveIt 2 lets you
  pick per task.
- **Do you need Cartesian paths?** "Move the gripper in a straight line
  while pouring" is harder than "get there somehow." MoveIt's
  `compute_cartesian_path` handles it; not all planners do.
- **Do you need to re-plan online?** Static scene + offline plan once
  is easy. Moving obstacles + 100 Hz re-plan is hard. Choose accordingly.
- **What's your IK story?** Inverse kinematics (joints from pose) for
  a 6-DOF arm has multiple solutions; the planner has to pick the right
  one. Solvers: KDL (default, slow, OK), TRAC-IK (numerical, fast),
  IKFast (compiled analytic, fastest).

## The main options

### MoveIt 2 — the default

The standard open motion planning stack for ROS 2. Wraps OMPL, CHOMP,
STOMP, Pilz, and others behind one API. Includes scene management,
collision checking, trajectory execution, and the move-group / planning
pipeline.

If you're on ROS 2, you start with MoveIt 2. The few projects that skip
it have a specific reason (extreme real-time, custom planner research).

- **MoveIt 2 + RViz Motion Planning plugin** — point-and-click planning.
  Great for demos.
- **MoveIt 2 + MoveGroup C++/Python API** — what you call from your own
  task code. The "hello world" path this repo's
  `cobot280_moveit_task/` demonstrates.
- **MoveIt 2 + ROS 2 Action `MoveGroup`** — slightly higher-level, used
  from behaviour trees and state machines.

**Best for:** every project that uses ROS 2 and isn't writing a
research planner from scratch.

### OMPL — sampling-based planning library

The library MoveIt uses under the hood for sampling planners. RRT,
RRT*, RRTConnect, BiTRRT, PRM, KPIECE, etc.

You rarely use OMPL directly. You configure *which* OMPL planner
MoveIt invokes via `ompl_planning.yaml` in your MoveIt config package.

**Best for what:**
- **RRTConnect** — fastest "find a path" for cluttered scenes. Default.
- **PRM* / RRT*** — when you want a near-optimal path; willing to spend
  the time.
- **KPIECE** — handles wide workspaces with sparse obstacles well.

### CHOMP / STOMP / TrajOpt — optimisation planners

These start from a guess and **optimise** the trajectory for smoothness
and clearance.

- **CHOMP** — covariant gradient-based. Smooth paths. Built into
  MoveIt 2.
- **STOMP** — stochastic trajectory optimiser. Robust to local minima.
  Built into MoveIt 2.
- **TrajOpt** — sequential convex optimisation. Fast and high-quality;
  used in industrial path planning. Separate library, integrates with
  MoveIt via `tesseract_motion_planners`.

**Best for:** when you want one smooth path per task, not a randomly
shaped sampled one. Production cells often prefer these.

### Pilz Industrial Motion Planner

A motion planner that mimics how industrial controllers move — `PTP`
(point-to-point), `LIN` (linear Cartesian), `CIRC` (circular). Built
into MoveIt 2.

**Best for:** industrial-style cells where engineers expect
predictable, repeatable straight-line moves.

### Vendor planners

Most industrial arms (FANUC, ABB, KUKA, Yaskawa, UR) ship their own
trajectory planners on the controller. You write a high-level move
(`MoveJ`, `MoveL`, `MoveC`), the controller plans and executes.

**Best for:** factory production, where the planner is part of the
certified product. Use these for the motion; use ROS 2 + MoveIt for
the perception, AI, and orchestration.

### Custom / research planners

Topology-based planners (LazyPRM, CBiRRT2), reinforcement-learning
policies, diffusion-based planners. Active research area.

**Best for:** novel manipulation problems. Not for new production
projects.

## Inverse kinematics solvers

Inside the planner, an IK solver turns "wrist at pose X" into joint
angles. The choice matters more than people expect.

- **KDL (default in MoveIt)** — numerical, included. Slow, sometimes
  misses solutions on near-singular configurations.
- **TRAC-IK** — improved numerical solver. Drop-in replacement. Faster
  and more reliable than KDL. Use it.
- **IKFast** — generates an arm-specific analytical solver, compiled
  to C++. Microsecond-level, perfect for high-rate IK. Generated with
  OpenRAVE's IKFast tool.
- **bio_ik** — heuristic optimiser, supports multi-goal constraints.
- **PickIK** — newer (ROS 2-era), well-maintained MoveIt plugin.

**Best for what:**
- TRAC-IK — fast safe default.
- IKFast — visual servoing, dense pose queries.

## Trajectory execution and control

The planner produces a trajectory; the controller executes it. On
ROS 2, this is typically a `JointTrajectoryController` from
`ros2_control`, fed by MoveIt's `MoveGroup` execution.

- **Joint Trajectory Controller** — common, position-based.
- **Effort / Velocity controllers** — for force / velocity control.
- **Admittance / Hybrid Force/Position** — for tasks that involve
  contact (insertion, polishing). Lives in `ros2_control` packages.

## How to pick

1. **ROS 2 + general manipulation?** → MoveIt 2 with RRTConnect for
   "any path" and STOMP / TrajOpt for "smooth path."
2. **Industrial straight-line moves expected?** → MoveIt 2 + Pilz
   Industrial Motion Planner.
3. **Production factory cell?** → Vendor planner on the controller.
4. **Dynamic obstacles, fast re-plan?** → MoveIt 2 + TrajOpt (or
   Tesseract for sequential plans), with online perception updates
   into the planning scene.
5. **Research?** → Stack whatever you want on top of MoveIt 2's
   pipeline.

## Output of this file — your motion-planning plan

```
Planner:              MoveIt 2 + RRTConnect / + STOMP / + Pilz / vendor
IK solver:             KDL / TRAC-IK / IKFast / bio_ik / PickIK
Cartesian paths needed?: yes (use compute_cartesian_path) / no
Online re-planning?:    no / yes (rate: ___ Hz)
Trajectory controller: JointTrajectoryController / Effort / Admittance / vendor
Collision world source: static URDF / live from depth camera / hybrid
Constraints used:      orientation lock / joint limits / box / line / cone
```

## Common mistakes

1. **No collision model of the table.** Planner finds "creative"
   trajectories that go through the table.
2. **Default KDL IK and surprise unreachable poses.** Switch to
   TRAC-IK. Almost always.
3. **Trying to control the arm at 1 kHz from a non-realtime kernel.**
   Trajectories stutter. Use `PREEMPT_RT` *or* slow the loop to
   100 Hz.
4. **Mixing planning units.** Some libraries default to mm, some to
   metres. Verify with a known-distance test before deploying.
5. **Trusting the planner without simulation.** Always plan-and-execute
   in Gazebo / Isaac Sim first.

## What's next

The planner needs to know **where the object is** to plan to it. That's
perception: turning camera pixels into "there's a cylinder at
(x, y, z)."

→ Next: [05-perception-software.md](05-perception-software.md)
