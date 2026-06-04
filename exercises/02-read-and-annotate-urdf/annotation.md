# myCobot 280 URDF — Annotated

The annotated kinematic tree of the **myCobot 280 Pi**, produced by
reading its URDF and labelling each link and joint in plain English.

Source URDF: `mycobot_280.urdf.xacro` from
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2),
package `mycobot_description/urdf/`. Numbers below are from the
Elephant Robotics spec sheet for the **myCobot 280 Pi (2022 revision)**
and the URDF that ships with that fork. Confirm against your own
clone before relying on them — vendor forks sometimes tweak limits.

## Kinematic tree

A 6-DoF serial chain. Each joint rotates around exactly one axis. The
arrow points from parent to child.

```
world
  └── base_link                       (the bolted-down base)
        └── joint1 [Z]
              └── link1               (the rotating "shoulder yoke")
                    └── joint2 [Y]
                          └── link2   (the upper arm)
                                └── joint3 [Y]
                                      └── link3   (the forearm)
                                            └── joint4 [Y]
                                                  └── link4 (wrist 1)
                                                        └── joint5 [Z]
                                                              └── link5 (wrist 2)
                                                                    └── joint6 [X]
                                                                          └── link6
                                                                                └── end_effector_frame
```

All six joints are **revolute** (a fixed-axis hinge, with hard stops).
No prismatic joints, no continuous joints, no mimic joints.

If a parallel-jaw gripper is loaded on top of this URDF (a separate
xacro `include` in the addison fork), you also get:

```
link6
  └── gripper_base                    (fixed joint, no motion)
        ├── gripper_left_finger       (prismatic, ±0..0.03 m)
        └── gripper_right_finger      (prismatic, mirror of left)
```

## Links — physical part each one represents

| Link | Physical part | Notes |
|---|---|---|
| `base_link` | the bolted-down base plate | always stays where you mounted it; this is the world-frame reference for everything else |
| `link1` | rotating base / shoulder yoke | the "swivel" that turns the whole arm left-right |
| `link2` | upper arm | from shoulder pitch to elbow |
| `link3` | forearm | from elbow to wrist pitch |
| `link4` | wrist 1 | the first wrist segment (pitch) |
| `link5` | wrist 2 | the second wrist segment (yaw) |
| `link6` | end-effector flange | the metal disc you bolt a gripper to |
| `end_effector_frame` | tool centre point (TCP) | a fixed offset from `link6` to where a tool actually grips. MoveIt's "EE link" |

Each link has a `<visual>` mesh (the pretty STL/DAE used in RViz and
Gazebo), a `<collision>` mesh (a simpler shape used for contact checks),
and an `<inertial>` block (mass, centre of mass, inertia tensor). Mass
totals ~850 g across the moving links, which matches the spec sheet's
850 g arm weight.

## Joints — axes and limits

All values from the spec sheet plus the URDF's `<limit>` tags.
Convention: the axis listed is the one written in the URDF's `<axis
xyz="..."/>` tag, expressed in the **parent link's frame**.

| Joint | Parent → Child | Axis | Lower limit | Upper limit | Max velocity | What it does |
|---|---|---|---|---|---|---|
| `joint1` | `base_link` → `link1` | Z (vertical) | -2.879 rad (-165°) | +2.879 rad (+165°) | ~1.5 rad/s | base yaw — swings the whole arm left-right |
| `joint2` | `link1` → `link2` | Y | -2.879 rad (-165°) | +2.879 rad (+165°) | ~1.5 rad/s | shoulder pitch — lifts the upper arm up-down |
| `joint3` | `link2` → `link3` | Y | -2.879 rad (-165°) | +2.879 rad (+165°) | ~1.5 rad/s | elbow pitch — bends the forearm relative to the upper arm |
| `joint4` | `link3` → `link4` | Y | -2.879 rad (-165°) | +2.879 rad (+165°) | ~1.5 rad/s | wrist pitch — tilts the wrist up-down |
| `joint5` | `link4` → `link5` | Z | -2.879 rad (-165°) | +2.879 rad (+165°) | ~1.5 rad/s | wrist yaw — twists the wrist left-right |
| `joint6` | `link5` → `link6` | X | -3.054 rad (-175°) | +3.054 rad (+175°) | ~1.5 rad/s | end-effector roll — rotates the flange the gripper bolts onto |

Notes on the axes:

- Joints 2, 3, 4 share the same Y axis in their parent's frame. That
  makes them a pitch-pitch-pitch chain — useful when you want to think
  of the arm as "shoulder → elbow → wrist tilt".
- Joints 1 and 5 are both about Z. They give the two yaw degrees of
  freedom (base swing and wrist twist).
- Joint 6 is about X — the gripper roll. Combined with joint 5 (Z) and
  joint 4 (Y), the wrist achieves the standard pitch-yaw-roll triple
  every 6-DoF arm needs.

Joint 6 has a slightly wider range (±175°) than the others (±165°)
because rolling the gripper past the symmetry point is sometimes the
shortest path to a target orientation.

## Quick reference: home pose vs ready pose

From the SRDF in the same package
(`mycobot_moveit_config/config/mycobot_280/mycobot_280.srdf`):

| Pose | joint1 | joint2 | joint3 | joint4 | joint5 | joint6 |
|---|---|---|---|---|---|---|
| `home` | 0 | 0 | 0 | 0 | 0 | 0 |
| `ready` | 0 | -1.57 | 1.57 | 0 | 0 | 0 |

`home` is the straight-up "T-pose". `ready` is the typical
shoulder-back, elbow-up scout pose used as a planning start.

## How to confirm any number above

1. `cd ~/ros2_ws/src/mycobot_ros2/mycobot_description/urdf`
2. Open `mycobot_280.urdf.xacro` in a text editor.
3. For each `<joint name="jointN">`, look at:
   - `type` (always `revolute` for joints 1–6),
   - `<axis xyz="..."/>` (which of `1 0 0`, `0 1 0`, `0 0 1` it is),
   - `<limit lower="..." upper="..." velocity="..."/>` (in radians).
4. To see the chain visually, run
   `urdf_to_graphiz mycobot_280.urdf` (Classic) or load it in RViz and
   add a `RobotModel` display — the TF tree shows every link.

## What this annotation lets you do next

- Know which joint to touch for a given motion before you write a single
  line of code.
- Set realistic joint goals in items 18 ("joint-space hello world") and
  21 ("hardcoded pick-and-place sequence").
- Spot out-of-reach goals early — the 280 mm working radius plus the
  ±165° limits define the reachable workspace.
- Debug TF errors in RViz by knowing which physical part each frame name
  refers to.
