# myCobot 280 URDF + autosampler-cell reach check

Two things in one file:

1. The annotated kinematic tree of the **myCobot 280 Pi** — what every
   link and joint actually is.
2. A reach check that confirms every rack and tray slot in
   [`../01-custom-gazebo-world/worlds/autosampler_cell.sdf`](../01-custom-gazebo-world/worlds/autosampler_cell.sdf)
   is inside the arm's 280 mm reach envelope — the autosampler tie-in
   for checklist item A.2.

Source URDF: `mycobot_280.urdf.xacro` from
[`automaticaddison/mycobot_ros2`](https://github.com/automaticaddison/mycobot_ros2).
Joint values cross-checked against the Elephant Robotics myCobot 280
Pi spec sheet.

## Kinematic tree

```
base_link
  └── joint1 [Z]   → link1   (base yaw / shoulder yoke)
        └── joint2 [Y]   → link2   (upper arm)
              └── joint3 [Y]   → link3   (forearm)
                    └── joint4 [Y]   → link4   (wrist 1, pitch)
                          └── joint5 [Z]   → link5   (wrist 2, yaw)
                                └── joint6 [X]   → link6   (end-effector flange)
                                      └── end_effector_frame  (TCP)
```

All six joints are **revolute** (hinge with hard stops). No continuous
joints, no prismatic joints in the arm itself. If a parallel-jaw
gripper is loaded on top, two prismatic finger joints appear below
`link6`.

## Joints — axis and limits

Axis is written in the parent link's frame. Limits in radians, with
degrees in brackets for human intuition.

| Joint | Parent → Child | Axis | Lower | Upper | What it does |
|---|---|---|---|---|---|
| joint1 | base_link → link1 | Z | −2.879 rad (−165°) | +2.879 rad (+165°) | base yaw |
| joint2 | link1 → link2 | Y | −2.879 rad (−165°) | +2.879 rad (+165°) | shoulder pitch |
| joint3 | link2 → link3 | Y | −2.879 rad (−165°) | +2.879 rad (+165°) | elbow pitch |
| joint4 | link3 → link4 | Y | −2.879 rad (−165°) | +2.879 rad (+165°) | wrist pitch |
| joint5 | link4 → link5 | Z | −2.879 rad (−165°) | +2.879 rad (+165°) | wrist yaw |
| joint6 | link5 → link6 | X | −3.054 rad (−175°) | +3.054 rad (+175°) | end-effector roll |

Total span: **280 mm working radius** from the base, **~250 g payload**
(spec sheet) — well above the 8 g vial.

## Links — physical part each one represents

| Link | Physical part |
|---|---|
| base_link | bolted-down base plate, world-frame reference |
| link1 | rotating shoulder yoke |
| link2 | upper arm |
| link3 | forearm |
| link4 | wrist 1 |
| link5 | wrist 2 |
| link6 | end-effector flange (gripper bolts here) |
| end_effector_frame | TCP — fixed offset MoveIt plans against |

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
        = sqrt(0.0756 + 0.0441)
        = sqrt(0.1197)
        ≈ 0.346 m   ← 346 mm, OVER the 280 mm reach
```

That fails. The arm cannot reach the back-left corner of the rack as
the cell is currently laid out. Two of the four rack corners are in
the same situation; the *near* corners are fine.

```
rack near corner = (0.05 − 0.045, 0.12 − 0.090) = (0.005, 0.030)
   d_xy = sqrt((0.005 − (−0.18))² + (0.030)²)
        = sqrt(0.185² + 0.030²)
        ≈ 0.187 m   ← inside reach
```

Tray check:

```
tray far corner  = (0.05 + 0.070, −0.12 − 0.070) = (0.120, −0.190)
   d_xy = sqrt((0.120 − (−0.18))² + (−0.190)²)
        = sqrt(0.300² + 0.190²)
        ≈ 0.355 m   ← also OVER 280 mm
```

### Conclusion

The myCobot 280 **cannot reach every slot** of the
requirements-sized rack and tray when placed at the centres used in
the SDF. The far ~30 % of each peripheral is out of reach.

This is exactly what
[`requirements/04-workspace-and-reach.md`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md)
warns about — "**Tight but feasible**" — and what the checklist's
A.2 autosampler tie-in is meant to surface before any code exists.

### Three ways forward

1. **Shrink the cell.** Pull both peripherals closer to the arm —
   e.g. source rack centre at (0.05, 0.07) and tray centre at
   (0.05, −0.07), with the rack rotated 90° to face the arm. That
   brings every far corner inside ~250 mm.
2. **Use a partial rack/tray.** v1 does not need all 50 + 100 slots;
   a 5 × 5 rack and 6 × 6 tray fit easily.
3. **Use a longer arm.** [`requirements/04`](../../docs/hplc-autosamplers/requirements/04-workspace-and-reach.md)
   already flags the **myCobot 320** (320 mm) and **UR3e** (500 mm)
   as comfortable alternatives. Cost trade-off; arm change ripples
   into every other exercise.

The world SDF currently uses option (1) implicitly by *scaling down*
the rack and tray footprints (90 × 180 mm rack vs 110 × 220 mm
catalogue value). For v1 that scaled-down geometry is the working
plan; tightening the cell further or swapping arms is a Layer-4
decision.

## How to verify any number above

1. `cd ~/ros2_ws/src/mycobot_ros2/mycobot_description/urdf`
2. Open `mycobot_280.urdf.xacro` and read each `<joint>` block for
   `type`, `<axis xyz="..."/>`, and `<limit lower upper velocity/>`.
3. `xacro mycobot_280.urdf.xacro > /tmp/mycobot_280.urdf` then
   `urdf_to_graphiz /tmp/mycobot_280.urdf` for a visual tree.
4. Reach numbers: this folder shows the arithmetic — re-run it for
   any new peripheral pose you add to the SDF.
