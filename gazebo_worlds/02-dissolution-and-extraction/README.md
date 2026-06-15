# 02 — Dissolution / extraction (ketchup case)

Run: `gz sim gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf`

Gazebo world for HPLC workflow [**Step 2 — Dissolution / extraction**](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md),
**ketchup case only**. The doc routine for ketchup is: take the
pre-weighed ~5 g sample → add solvent → mix until the 5-HMF has been
pulled out of the pulp.

This world strips the routine down to **only what a benchtop arm can
reliably do**:

- The three beakers on the bench **already contain the ~5 g ketchup
  sample** at the bottom. Step 1 (weighing) is skipped, so we put the
  weighed paste straight into the destination vessel instead of
  carrying it in a weigh boat.
- The arm physically **swirls** each beaker after pouring solvent in,
  to mix. The Step 2 doc lists "swirl by hand" as one of the four
  valid mixing methods, so this matches the original routine.
- There is **no hot plate** and **no stir bar**. A hot plate's knobs
  are too small for the arm to grip and operate, and Gazebo cannot
  simulate the magnetic coupling that makes a stir bar spin anyway,
  so both were removed.

No arm is included. A yellow Ø100 mm disc at the back of the bench
marks where the arm base will be bolted down later.

## Workflow — what the arm does

Pick → place → pour → place back, repeated three times. One beaker
at a time:

1. Pick up **beaker_1** from the right side of the bench.
2. Place it at the centre of the bench (pour station).
3. Pick up the solvent bottle.
4. Tilt it over beaker_1 to pour ~50 mL solvent in.
5. Put the solvent bottle back on the left side.
6. Pick up beaker_1 from the centre.
7. (Optional) Swirl it gently in a small circular motion for ~10
   seconds so the sample mixes into the solvent.
8. Place beaker_1 back at its original spot on the right side.
9. Repeat steps 1-8 for **beaker_2**, then for **beaker_3**.

End state: each of the three beakers now holds the cloudy reddish
extract, ready for Step 3 (dilution).

## What is on the bench

Frame: **+X = forward**, **+Y = left**, **+Z = up**. Bench top is at
**z = 0.900 m**. Operator-view right = world **-Y**.

| # | Object | Real product reference | Size (mm) | Pose (X, Y) | Mass | Purpose |
|---|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench section, 4-leg | Top 1000 × 600 × 50, 4× Ø50 × 850 steel legs | centred at (0, 0) | static | Work surface. Legs go down to the floor so the bench is not floating. |
| 2 | **Arm marker** | n/a — visual flag only | Ø100 × 2 yellow disc | (-0.22, 0.00) | static | Future arm base location. |
| 3 | **Beaker 1 + sample** | Corning Pyrex 1000 low-form, 100 mL (P/N 1000-100) + ~5 g ketchup blob (Ø30 × 8 mm red disc at the bottom) | Ø50 × 70 glass | (0.05, -0.30) | 80 g | First extraction vessel. Furthest from the arm. |
| 4 | **Beaker 2 + sample** | Same as Beaker 1 | Ø50 × 70 glass | (0.05, -0.18) | 80 g | Second extraction vessel. |
| 5 | **Beaker 3 + sample** | Same as Beaker 1 | Ø50 × 70 glass | (0.05, -0.06) | 80 g | Third extraction vessel. Closest to the arm. |
| 6 | **Solvent bottle (water / mild acid)** | Schott Duran 500 mL wide-mouth reagent bottle GL45 (P/N 218017552) | Body Ø85 × 150 (with a pale-blue translucent Ø80 × 120 mm water level filling ~80 % of the body), cap Ø50 × 25 blue | (0.10, +0.25) | 700 g | The diluent the doc names for ketchup. Sits on the left side so the arm can pick it up after placing a beaker at the centre. The water cylinder is a **static visual prop** — Gazebo's physics is rigid-body only, so the bottle does not actually pour fluid when tilted. A small plugin could shrink the water visual on tilt later to fake a pour. |

### What was deliberately left out

- **Hot plate / magnetic stirrer.** A real benchtop hot plate has
  small knobs and a button panel. A simple cobot gripper cannot
  reliably grip and turn those — modelling the device would mean
  modelling an action the arm cannot do.
- **Stir bar.** Depends on the hot plate, and Gazebo cannot simulate
  the magnetic coupling that makes a real stir bar spin anyway.
- **Weigh boat with sample.** Belongs to Step 1 (weighing), which
  this project skips. The pre-weighed paste is shown directly inside
  each beaker.
- **Ultrasonic bath.** Mentioned by the general Step 2 routine but
  not by the ketchup paragraph.
- **Analytical balance.** Lives in [Step 1](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md).
- **Volumetric flask, pipette, vials, filter, centrifuge.** Live in
  Steps 3 / 4 / 5 — see the other `gazebo_worlds/` subfolders.

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

Reach check from the marker at (-0.22, 0, 0.901):

| Target | Distance | Inside myCobot 280 (~280 mm)? |
|---|---|---|
| Beaker 3 (closest) at (0.05, -0.06) | ~277 mm | Borderline |
| Beaker 2 at (0.05, -0.18) | ~325 mm | **No** |
| Beaker 1 (farthest) at (0.05, -0.30) | ~404 mm | **No** |
| Solvent bottle at (0.10, +0.25) | ~406 mm | **No** |

The bench is sized generously so a longer-reach arm (UR3 / Franka FR3
at ≥ 500 mm) does not have to relayout the cell. For a myCobot 280,
tighten the beaker spacing and move the solvent bottle inward.

## Coordinate sanity check

Bench top at **z = 0.900 m**. Every object sits directly on the bench
top — the previous "beaker on the hot plate" stack is gone, so all
heights are straightforward:

| Object | Bottom z | Top z |
|---|---|---|
| Beaker (each) | 0.900 | 0.970 |
| Ketchup blob inside each beaker | 0.900 | 0.908 |
| Solvent bottle body | 0.900 | 1.050 |
| Solvent bottle cap | 1.050 | 1.075 |

## Is one world enough for Step 2?

**Yes, for the ketchup case.** Step 2 is one station, one routine.
A `paracetamol_dissolution.sdf` sibling would cover the clean
dissolution case later; other steps get their own subfolders under
`gazebo_worlds/`.

## Synthetic-data capture

The world has an **overhead RGB camera** bolted on so it can produce
a small dataset of the bench from above. The current implementation
is deliberately **Step 1 only** — place the camera, save its frames
to disk, optionally move the camera between captures. No labels yet,
no object jitter, no lighting variation. Those are Step 2 and Step 3,
deferred to a follow-up.

See [`synthetic_data/README.md`](synthetic_data/README.md) for the
two-terminal WSL recipe. The capture itself is done by Gazebo's
`<save>` element on the camera sensor — no ROS bridge, no Python
subscriber, no `cv_bridge`.

This is the first concrete warm-up for
[`docs/synthetic-data/features/01-detection-images-and-masks.md`](../../docs/synthetic-data/features/01-detection-images-and-masks.md).

## File list

```
02-dissolution-and-extraction/
├── README.md                  (this file)
├── ketchup_extraction.sdf     (the Gazebo world; overhead camera auto-saves frames)
└── synthetic_data/            (Step 1: capture frames at multiple camera angles)
    ├── README.md
    └── move_camera.py
```
