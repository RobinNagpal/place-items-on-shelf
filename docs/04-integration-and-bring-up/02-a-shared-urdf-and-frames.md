# 02-a — Shared URDF and Frame Conventions

You're about to point your code at real hardware. The single rule
that makes this *not* a rewrite is: **the same URDF describes the
arm in both the simulator and the real world.** The same
frame names. The same joint names. The same kinematics.

If sim and real disagree on those, every later step lies to you.

## What you need before this step

- A simulation-first cell that works through
  [01-f](01-f-stress-test-in-sim.md).
- The vendor's URDF (or your custom one) — the same one
  [01-b](01-b-build-the-virtual-cell.md) loaded.
- A clear idea of what your **real** mounting setup looks like.

## The contract: what must match

Sim and real share these:

| Thing | Why it must match |
|-------|-------------------|
| Joint names (`joint_1`, `shoulder_pan_joint`, …) | The controllers and MoveIt config reference them by name. |
| Frame names (`base_link`, `tool0`, `camera_link`, …) | Your task code targets poses in named frames. A rename breaks everything. |
| Joint order in the trajectory message | The driver assigns indices in URDF order. A different order = wrong joints move. |
| Joint limits (lower, upper, velocity, effort) | The planner respects URDF limits. Loose limits in sim = real arm hits a stop. |
| Link masses and inertias | Less critical for position control; load this for force / dynamics. |
| Collision meshes vs. visual meshes | Sim uses both; real uses only the collision side for self-collision checks. |
| TF tree topology | Any `static_transform_publisher` in sim must exist in real too. |

The fix when sim and real diverge is **always to make real match sim,**
not the other way around — sim is your source of truth for code; real
provides the actual physics. If your URDF is wrong, fix the URDF and
re-test in sim before deploying.

## Standard frame names everybody expects

ROS 2 / MoveIt code in the wild assumes:

- **`world`** — the global reference, fixed.
- **`base_link`** — the arm's base. Mounted to `world` by a static
  transform (`world → base_link`).
- **`link_1` … `link_N`** — the kinematic chain.
- **`tool0`** — the flange (last link before whatever you bolt on).
- **`<gripper>_base_link`** — the gripper.
- **`<gripper>_tip`** — the contact point, where you aim grasps.
- **`camera_link`** — the camera body.
- **`<camera>_optical_frame`** — the optical axis (Z forward, X
  right, Y down — REP-103).
- **`object_<id>`** — published by perception, one per object.

Don't rename these unless you absolutely must. Library compatibility
silently breaks.

## REP-103 and the right-hand rule

ROS 2 frames follow [REP-103](https://www.ros.org/reps/rep-0103.html):

- **X** forward, **Y** left, **Z** up — for the robot's base.
- **Optical frames** flip: **Z** forward (into the scene), **X**
  right, **Y** down.
- Angles in radians, distances in metres, time in seconds.

Mixing degrees and radians inside the same launch file is a top-five
source of weird bugs. Lock units now.

## What changes between sim and real — and where to put each change

There *are* differences. They belong in **separate files**, not in
the URDF:

| What changes | Where it goes |
|--------------|---------------|
| Which `ros2_control` plugin runs | A `<sim>` vs `<real>` controller config (see [02-b](02-b-ros2-control-driver-swap.md)). |
| Calibration offsets (camera to arm) | A YAML loaded at runtime, not the URDF. |
| Joint home offsets (zero positions) | Vendor driver parameter, not URDF. |
| Speed / acceleration limits for safety | Controller config, not URDF kinematics. |
| Real-world clutter (walls, fixtures) | The MoveIt planning scene, loaded by your task code. |

Keep the URDF as the **canonical kinematics file**. Everything else
goes in environment-specific configs.

## A practical layout

A typical robotics workspace ends up with:

```
ros2_ws/
  src/
    <arm>_description/        # URDF / xacro — shared
    <arm>_moveit_config/      # MoveIt config — shared
    <project>_bringup/
      launch/sim.launch.py    # sim-only entrypoint
      launch/real.launch.py   # real-only entrypoint
      config/controllers_sim.yaml
      config/controllers_real.yaml
      config/calibration.yaml # measured on real, ignored in sim
```

Two launch files, one URDF. The launch files differ only in which
controllers config + hardware plugin they load.

## Step-by-step verification

Run these checks **before** plugging real hardware in:

1. **Parse the URDF:** `check_urdf <arm>.urdf` returns no errors.
2. **Visual vs collision overlap:** Open the URDF in RViz with both
   visualisations; they shouldn't differ wildly.
3. **TF tree:** `ros2 run tf2_tools view_frames` — graph shows the
   expected topology.
4. **Joint limits sanity:** Drag every joint in the
   `joint_state_publisher_gui` from min to max in RViz. No self-
   collision flagged when there shouldn't be; flagged when there
   should be.
5. **Static transforms:** Confirm `world → base_link` and
   `tool0 → <gripper>_tip` are published as expected — your task code
   expects them.

If step 5 fails on real, your perception will compute the wrong grasp
pose. This is the #1 sim-to-real bug.

## Output of this step

```
URDF source:                 <package, version, commit>
Mount transform (world→base_link): x=___, y=___, z=___, roll=___, pitch=___, yaw=___
Tool frame:                  tool0
Gripper tip frame:           <gripper>_tip — offset from tool0: ___
Camera link:                 camera_link — offset from base_link: ___ (placeholder; real value comes in 02-c)
Joint name list:             ___
Joint limits (rad):          joint_1: [___,___], …
Units locked (m, rad, s):    yes / no
Launch files:                sim.launch.py, real.launch.py
URDF check passes:           yes / no
TF tree intact:              yes / no
```

## Common mistakes

1. **Two URDFs.** "sim URDF" and "real URDF" diverge over months. One
   URDF only.
2. **Calibration baked into URDF.** Now you can't change calibration
   without rebuilding. Use a runtime YAML.
3. **Frame rename "to be more readable".** You broke every tutorial,
   every MoveIt config, every TF lookup. Don't.
4. **Loose joint limits in URDF.** Sim happily plans past them, real
   hits a stop.
5. **Different units in different files.** Lock metres + radians +
   seconds across the project.
6. **No static transform from `world` to `base_link`.** TF tree is
   disconnected, everything silently fails.

## What's next

URDF and frames are unified. Now you swap the **hardware driver**
underneath that URDF — from the sim plugin to the real arm's driver.

→ Next: [02-b-ros2-control-driver-swap.md](02-b-ros2-control-driver-swap.md)
