# myCobot 280 URDF + autosampler-cell reach check

Two things in one file:

1. The annotated kinematic tree of the **myCobot 280 Pi**, read straight
   from the upstream URDF.
2. A reach check that confirms (or fails) every rack and tray slot in
   [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf)
   against the arm's 280 mm reach envelope — the autosampler tie-in for
   checklist item A.2.

## Where the arm is actually defined (upstream)

We use the same fork the rest of this project uses:
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2)
(the repo referenced by [`robots/mycobot-280-pi/cobot280_moveit_task/`](../../robots/mycobot-280-pi/cobot280_moveit_task/)).

The arm is built up from a small tree of xacro files. To understand the
joints and structure, read these in order:

| Path in the upstream repo | What it defines |
|---|---|
| [`mycobot_description/urdf/robots/mycobot_280.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/robots/mycobot_280.urdf.xacro) | top-level — composes the base, the arm, the gripper, the ros2_control plugin, and the camera into one robot |
| [`mycobot_description/urdf/mech/g_shape_base_v2_0.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/mech/g_shape_base_v2_0.urdf.xacro) | the "G-shape" desk-clamp **base** that defines `base_link` |
| [`mycobot_description/urdf/mech/mycobot_280_arm.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/mech/mycobot_280_arm.urdf.xacro) | **the arm itself** — `link1`..`link6`, `link6_flange`, and the 1 fixed + 6 revolute joints between them |
| [`mycobot_description/urdf/mech/adaptive_gripper.urdf.xacro`](https://github.com/automaticaddison/mycobot_ros2/blob/main/mycobot_description/urdf/mech/adaptive_gripper.urdf.xacro) | the optional **adaptive gripper** loaded on the flange |

The numbers in this annotation are copied straight out of
`mycobot_280_arm.urdf.xacro` on `main`. Open that file side-by-side with
this document to verify any line.

## Kinematic tree (as actually written in the URDF)

```
world                                     (defined by top-level xacro when add_world=true)
  └── virtual_joint [fixed]
        └── base_link                     (from g_shape_base_v2_0.urdf.xacro)
              └── base_link_to_link1 [fixed]
                    └── link1             (rotating shoulder yoke)
                          └── link1_to_link2 [revolute]
                                └── link2 (upper arm)
                                      └── link2_to_link3 [revolute]
                                            └── link3 (forearm)
                                                  └── link3_to_link4 [revolute]
                                                        └── link4 (wrist 1)
                                                              └── link4_to_link5 [revolute]
                                                                    └── link5 (wrist 2)
                                                                          └── link5_to_link6 [revolute]
                                                                                └── link6 (last actuated link)
                                                                                      └── link6_to_link6_flange [revolute]
                                                                                            └── link6_flange (tool flange / TCP)
```

Six revolute joints, one fixed joint between the base and link1.
That's **6 DoF**, which matches the spec. The fixed joint exists so the
URDF can describe the static mount geometry without putting a motor
there.

## Joints — what each one is, from the URDF

Important: in this URDF, **every `<axis>` tag is `xyz="0 0 1"`**. The
direction the joint actually rotates in is determined by each joint's
`<origin rpy="…">` — the rpy rotates the parent's frame, and the
joint then spins around the Z axis of the rotated frame.

So when you read the table below, the "physical motion" column is what
you would see if you looked at the arm; the URDF achieves that motion
by combining `axis = 0 0 1` with a specific `rpy` on the joint origin.

| Joint name (URDF) | Type | `<origin rpy>` | Physical motion | Lower | Upper |
|---|---|---|---|---|---|
| `base_link_to_link1` | fixed | `0 0 0` | none — link1 is bolted onto the base | – | – |
| `link1_to_link2` | revolute | `0 0 π/2` | **base yaw** — swings the whole arm left/right | −2.879793 rad (−165°) | +2.879793 rad (+165°) |
| `link2_to_link3` | revolute | `0 π/2 −π/2` | **shoulder pitch** — lifts the upper arm | −2.879793 rad (−165°) | +2.879793 rad (+165°) |
| `link3_to_link4` | revolute | `0 0 0` | **elbow pitch** — bends the forearm relative to the upper arm | −2.879793 rad (−165°) | +2.879793 rad (+165°) |
| `link4_to_link5` | revolute | `0 0 −π/2` | **wrist pitch** — tilts the wrist up/down | −2.879793 rad (−165°) | +2.879793 rad (+165°) |
| `link5_to_link6` | revolute | `π/2 −π/2 0` | **wrist yaw** — twists the wrist left/right | −2.879793 rad (−165°) | +2.879793 rad (+165°) |
| `link6_to_link6_flange` | revolute | `−π/2 0 0` | **end-effector roll** — rotates the flange the gripper bolts to | −3.05 rad (−175°) | +3.05 rad (+175°) |

Other numbers shared by all revolute joints (from the same xacro):

- `effort = 56 Nm`
- `velocity = 2.792527 rad/s` (~160°/s)
- `damping = 0`, `friction = 0` (frictionless in sim — real arm differs)

The last joint (`link6_to_link6_flange`) has a slightly **wider range**
(±175°) than the others (±165°) because rolling the gripper past the
symmetry point is sometimes the shortest path to a target orientation.

## Links — physical part each one represents

| Link (URDF name) | Mass (URDF) | Physical part |
|---|---|---|
| `base_link` | from g_shape_base xacro | the bolted-down base / desk clamp |
| `link1` | 0.120 kg | rotating shoulder yoke (carries the joint-1 servo) |
| `link2` | 0.190 kg | upper arm |
| `link3` | 0.160 kg | forearm |
| `link4` | 0.124 kg | wrist 1 |
| `link5` | 0.110 kg | wrist 2 |
| `link6` | 0.0739 kg | last actuated link |
| `link6_flange` | 0.035 kg | tool flange — the gripper bolts here; this is the TCP MoveIt plans against |

Total arm mass ≈ **0.85 kg**, matching the Elephant Robotics spec
sheet. Visual meshes (`mycobot_description/meshes/mycobot_280/visual/*.dae`)
are simplified to boxes / cylinders for the collision shape so the
planner runs fast.

## Reach check against the autosampler cell

From [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf):

| Object | Centre (x, y, z) m | Footprint | Far-corner offset from centre |
|---|---|---|---|
| Arm base | (−0.18, 0, 0.775) | – | – |
| Source rack | (0.05, 0.12, 0.80) | 90 × 180 × 50 mm | ±45 mm in x, ±90 mm in y |
| Destination tray | (0.05, −0.12, 0.80) | 140 × 140 × 10 mm | ±70 mm in x, ±70 mm in y |

Worst-case horizontal distance from the arm base to a corner:

```
rack far corner  = (0.05 + 0.045, 0.12 + 0.090) = (0.095, 0.210)
   d_xy = sqrt((0.095 − (−0.18))² + (0.210 − 0)²)
        = sqrt(0.275² + 0.210²)
        ≈ 0.346 m   ← 346 mm, OVER the 280 mm reach
```

That fails. The arm cannot reach the back-left corner of the rack as
the cell is currently laid out. Two of the four rack corners are in
the same situation; the *near* corners are fine.

```
rack near corner = (0.05 − 0.045, 0.12 − 0.090) = (0.005, 0.030)
   d_xy ≈ 0.187 m   ← inside reach
```

Tray check:

```
tray far corner  = (0.05 + 0.070, −0.12 − 0.070) = (0.120, −0.190)
   d_xy = sqrt((0.120 − (−0.18))² + 0.190²)
        ≈ 0.355 m   ← also OVER 280 mm
```

### Conclusion

The myCobot 280 **cannot reach every slot** of the requirements-sized
rack and tray when placed at the centres used in the SDF. The far
~30 % of each peripheral is out of reach. This is exactly what
[`requirements/04-workspace-and-reach.md`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md)
warns about — **"Tight but feasible"** — and what the A.2 autosampler
tie-in is meant to surface before any code exists.

### Three ways forward

1. **Shrink the cell.** Pull both peripherals closer to the arm.
2. **Use a partial rack/tray.** v1 does not need all 50 + 100 slots.
3. **Use a longer arm.** myCobot 320 (320 mm) or UR3e (500 mm).

The world SDF currently uses option (1) implicitly by *scaling down*
the rack and tray footprints (90 × 180 mm rack vs 110 × 220 mm
catalogue, 140 × 140 mm tray vs sub-300 × 400 mm catalogue). For v1
that scaled-down geometry is the working plan; tightening the cell
further or swapping arms is a Layer-4 decision.

## How to verify any number above

1. Clone the upstream: `git clone https://github.com/automaticaddison/mycobot_ros2`
2. Open `mycobot_description/urdf/mech/mycobot_280_arm.urdf.xacro` —
   every joint and link in the table above is right there.
3. To get a single flat URDF (xacro expanded), from a ROS 2 env:
   `xacro mycobot_description/urdf/robots/mycobot_280.urdf.xacro > /tmp/mycobot_280.urdf`
4. Then `urdf_to_graphiz /tmp/mycobot_280.urdf` for a visual tree.
5. Reach numbers: this folder shows the arithmetic — re-run it for any
   new peripheral pose you add to the SDF.
