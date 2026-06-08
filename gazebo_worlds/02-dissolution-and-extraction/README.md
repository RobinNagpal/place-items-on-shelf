# 02 — Dissolution / extraction (ketchup case)

Run: `gz sim gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf`

Gazebo world for HPLC workflow [**Step 2 — Dissolution / extraction**](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md),
**ketchup case only**. The doc routine modelled here is: take the
pre-weighed ~5 g sample from Step 1 → tip it into a beaker → add
water / mild acid solvent → stir, optionally warm gently.

No arm is included. A yellow Ø100 mm disc at the back of the bench
marks where the arm base will be bolted down later.

## What is on the bench

Frame: **+X = forward**, **+Y = left**, **+Z = up**. Bench top is at
**z = 0.900 m**.

| # | Object | Real product reference | Size (mm) | Pose (X, Y) | Mass | Purpose |
|---|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench section, 4-leg | Top 1000 × 600 × 50, 4× Ø50 × 850 steel legs | centred at (0, 0) | static | Work surface. Legs go down to the floor so the bench is not floating. |
| 2 | **Arm marker** | n/a — visual flag only | Ø100 × 2 yellow disc | (-0.22, 0.00) | static | Future arm base location. |
| 3 | **Hot plate** | IKA C-MAG HS 7 magnetic stirrer + hot plate | 220 × 220 × 120, 180 × 180 ceramic top | (0.05, 0.00) | static | Provides the *warm gently* and the magnetic spin field for the stir bar. |
| 4 | **Beaker (100 mL)** | Corning Pyrex 1000 low-form, 100 mL (P/N 1000-100) | Ø50 × 70 | on the ceramic top | 75 g | The extraction vessel. |
| 5 | **Stir bar** | PTFE-coated octagonal magnet | Ø25 × 8 white | inside the beaker | 5 g | The thing the hot-plate magnet drags in a spin. **In sim it does not actually rotate** — see *Stir-bar limitation* below. |
| 6 | **Ketchup bottle** | Heinz / Mitchell's 14 oz glass bottle | Body Ø55 × 130 + tapered shoulder (3 stacked discs) + neck Ø22 × 30 + cap Ø28 × 18 white; total 208 | (0.10, +0.25) | 500 g | The source jar of ketchup. Tapered shoulder mimics the real bottle silhouette. |
| 7 | **Solvent bottle (water / mild acid)** | Schott Duran 500 mL wide-mouth reagent bottle GL45 (P/N 218017552) | Body Ø85 × 150, cap Ø50 × 25 blue | (0.10, -0.25) | 700 g | The diluent the doc names for ketchup. |
| 8 | **Weigh boat + sample** | 60 mm white PS antistatic weigh boat | 60 × 60 × 15 + Ø25 × 6 red blob | (-0.05, +0.18) | 10 g | Carries the pre-weighed ~5 g ketchup from Step 1. The arm scoops directly out of the weigh boat with the beaker rim (or the gripper) — no separate spatula. |

### Stir-bar limitation

The stir bar's geometry is correct but Gazebo cannot simulate the
magnetic coupling that makes a real stir bar spin. In the real cell, a
motor inside the hot-plate base rotates a hidden magnet under the
ceramic top; that field drags the PTFE-coated iron bar in the beaker
in a circle. We have no equivalent in Gazebo's physics engine.

So this stir bar is a **static visual prop**. To make it actually
rotate during a simulation, you would either (a) attach a hidden
revolute joint between the stir bar and the beaker bottom and command
a joint velocity with a small ROS 2 node, or (b) use the
`gz-sim-velocity-control-system` plugin to spin the link directly.
For a first-pass world that is just object placement, the static prop
is fine.

### Why these are the only items

The ketchup paragraph of the workflow doc requires exactly four
actions: **transfer the pre-weighed sample → add solvent → stir →
optionally warm**. The list above is the smallest set that supports
all four. Deliberately left out:

- **Ultrasonic bath.** The general routine mentions it; the ketchup
  paragraph specifically does not.
- **Analytical balance.** Lives in [Step 1](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md).
- **Volumetric flask, pipette, vials.** Live in [Step 3](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/03-dilution.md)
  and later. See `gazebo_worlds/03-dilution/` for those.
- **Filter / centrifuge tube.** Pulp removal happens in [Step 4](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md).

## Arm placeholder

Yellow Ø100 mm disc at **(-0.22, 0.00)** on the bench top. To install
an arm:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

Reach check: the farthest object (ketchup bottle at (0.10, +0.25)) is
~407 mm from the marker — outside the myCobot 280's ~280 mm envelope.
For a myCobot, move the ketchup and solvent bottles to (0.05, ±0.15).
The bench is sized generously so a longer-reach arm (UR3 / Franka FR3)
does not have to relayout the cell.

## Coordinate sanity check

Bench top at **z = 0.900 m**. For objects sitting flat on the bench,
the SDF pose's z = 0.900 + height/2 (boxes / cylinders are centred on
their geometry). The beaker is the only exception — it sits on the
hot plate's ceramic top at z = 1.020, so its centre is at z = 1.055.
The ketchup bottle, which has multiple stacked sections, uses a model
pose at z = 0.900 and per-section local z offsets measured from the
bench top.

## Is one world enough for Step 2?

**Yes, for the ketchup case.** Step 2 is one station, one routine.
A `paracetamol_dissolution.sdf` sibling would cover the clean
dissolution case later; other steps get their own subfolders under
`gazebo_worlds/`.

## File list

```
02-dissolution-and-extraction/
├── README.md                  (this file)
└── ketchup_extraction.sdf     (the Gazebo world)
```
