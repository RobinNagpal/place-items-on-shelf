# 04 — Workspace And Reach

> Answers question **6** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "What is the workspace and reach?"

## The cell, from above

A rough plan view of the v1 cell. **The autosampler tray sits on
the bench, in its own alignment mount, not inside the HPLC.** The
HPLC itself is offset to the side; the human carries the loaded
tray over when the robot finishes.

```
       ┌──────────────────┐
       │   HPLC instrument│       ← off to one side; out of arm's reach
       │ (human inserts   │         the robot NEVER reaches into it
       │  loaded tray)    │
       └──────────────────┘
                ⇧ human carries tray over here when robot is done


        ┌────────────────────────────────────────┐
        │                                        │
        │            [robot arm base]            │  ←── arm mount
        │                                        │
        └──────┬─────────────────┬───────────────┘
               │                 │
          (~100 mm)         (~150 mm)
               │                 │
   ┌───────────┴──┐      ┌───────┴──────┐      ┌──────────────┐
   │ barcode      │      │ inbound rack │      │ destination  │
   │ reader       │      │ (48 vials)   │      │ tray on      │
   │              │      │              │      │ alignment    │
   └──────────────┘      └──────────────┘      │ plate (96)   │
                                                └──────────────┘
                                                ← tray is on the BENCH
```

All three peripherals (rack, benchtop tray mount, barcode reader)
live in a single roughly **40 × 40 cm region** centred on the arm
base. **The HPLC instrument is intentionally outside the arm's
reach envelope** — a tray-transport step (human in v1, motorised
shuttle in a hypothetical v2) bridges the gap.

## Working volume

| Property                 | Value                                                |
|--------------------------|------------------------------------------------------|
| Working area (top view)  | **~40 cm × 40 cm**                                   |
| Working height           | **~20 cm above bench**                               |
| Working volume           | ~40 × 40 × 20 cm                                     |
| Arm base height          | At bench level (0 mm)                                |
| Tray slot height         | ~20 mm above bench (tray on an alignment plate)      |
| Rack slot height         | ~50 mm above bench                                    |
| Barcode reader height    | Window centred ~80 mm above bench                    |

### The reference HPLC's own footprint

The reference instrument is the **Agilent 1290 Infinity II
Vialsampler** (see
[`01-task-and-objects.md`](01-task-and-objects.md) for sourcing).
Its own cube is:

- **324 mm wide × 396 mm deep × 468 mm tall** (12.8 × 15.6 × 18.4 in)
- **19 kg** without sample cooler
- Drawer opens toward the operator on the **396 mm-deep** face.

This means the HPLC needs roughly **35 × 45 cm** of bench area of
its own, **plus** the 40 × 40 cm robot cell next to it. Budget at
least **~80 × 50 cm of bench length** for the combined setup.

## Reach required

The arm must reach:

- The **furthest corner of the inbound rack** (≈ rack centre +
  ½ × diagonal).
- The **furthest corner of the autosampler tray** — usually the
  far rear corner inside the drawer.
- The **barcode reader window**, mid-air, mid-cycle.

Worst-case farthest point from the arm base, given the rough plan
above: about **250 mm horizontally** and **150 mm vertically**.

| Candidate arm        | Reach   | Verdict for this cell                                |
|----------------------|---------|------------------------------------------------------|
| **myCobot 280 Pi**   | 280 mm  | **Tight but feasible** — peripherals must be packed close. Plan for ~10 % margin loss when accounting for end-effector length. |
| myCobot 320          | 320 mm  | Comfortable                                          |
| UR3e                 | 500 mm  | Generous                                             |
| Franka Research 3    | 855 mm  | Overkill for v1, but fine                            |

## Obstacles inside the workspace

The arm must plan motions that avoid:

1. **The benchtop tray alignment plate** — the plate has walls
   around the tray to keep it in a fixed pose.
2. **The inbound rack walls** — the rack has plastic walls between
   vials.
3. **The barcode reader stand** — a vertical post.
4. **Already-placed vials** in the tray — these grow during a load
   cycle and act as new obstacles for later picks.
5. **The technician's hands**, sometimes — handled by safety
   speed/separation monitoring, not by collision avoidance.
6. **The arm's own body** — the planner already handles self-collision.

> **What the arm does NOT have to avoid (because the HPLC is out
> of reach):** the autosampler housing, the open drawer, drawer
> rails, instrument fascia. The benchtop-tray decision (see
> [`../research/03-manual-steps-today.md`](../research/03-manual-steps-today.md), Step C)
> removes this entire class of obstacles.

## Mounting

- **Fixed base**, bolted to a rigid bench plate.
- The base plate is **levelled to ±0.5 mm** with adjustable feet so
  the arm's coordinate frame is reliably horizontal.
- A small **fiducial marker** (e.g. ArUco tag) is placed on the
  bench in known offset from the base, used by perception to
  re-zero the world frame at calibration time.

## What this means for the next layers

| Layer-2 topic         | Constraint from this doc                          |
|-----------------------|---------------------------------------------------|
| Arm reach             | ≥ **300 mm** preferred; 280 mm is tight           |
| Arm base mount        | Rigid plate, levelled, fiducial near base         |
| Cell layout           | Peripherals packed within 40 × 40 × 30 cm         |
| End-effector length   | Short — every mm of gripper length steals reach    |

## Sources

- [myCobot 280 Pi Specifications — Elephant Robotics](https://www.elephantrobotics.com/en/mycobot-280-pi-2023-specifications/)
- [Universal Robots UR3e specifications page](https://www.universal-robots.com/products/ur3-robot/)
- [Agilent autosampler trays and drawers (catalogue)](https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/autosampler-fraction-collector-supplies-for-hplc/sample-trays-for-hplc)
- [Agilent 1290 Infinity II Vialsampler data sheet (PDF, hpst.cz)](https://hpst.cz/sites/default/files/oldfiles/5991-6286en.pdf) — instrument cube 324 × 396 × 468 mm, 19 kg.

→ Next: [`05-practical-limits.md`](05-practical-limits.md)
