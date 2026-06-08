# 04 — Filtering (ketchup case)

Run: `gz sim gazebo_worlds/04-filtering/ketchup_filtering.sdf`

Gazebo world for HPLC workflow [**Step 4 — Filtering**](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md),
ketchup case only. The doc routine modelled here is **spin → pour off
→ filter**: pour the Step 3 dilution into a Falcon tube, spin in the
centrifuge so the pulp packs into a pellet and a clearer supernatant
floats on top, draw the supernatant into a syringe, push it through a
0.45 µm syringe filter, collect the clean filtrate into a beaker.

No arm is included. Yellow Ø100 mm disc at the back of the bench
marks where the arm base will go.

## What is on the bench

Frame: **+X = forward**, **+Y = left**, **+Z = up**. Bench top at
**z = 0.900 m**.

| # | Object | Real product reference | Size (mm) | Pose (X, Y) | Purpose |
|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench, 4-leg | Top 1000 × 600 × 50, 4× Ø50 × 850 steel legs | centred at (0, 0) | Work surface. Same as Step 2 / 3 for layout continuity. |
| 2 | **Arm marker** | n/a — visual flag | Ø100 × 2 yellow disc | (-0.22, 0.00) | Future arm base location. |
| 3 | **Centrifuge** | Hettich EBA 200 swing-bucket benchtop centrifuge | 280 × 300 × 200 base + Ø250 × 50 white lid; 250 total height | (-0.05, +0.30) | The *spin* in spin → pour → filter. Separates pulp (pellet) from clear-ish supernatant. Lid drawn closed; tiny green-glow display panel on the front face. |
| 4 | **Tube rack** | 4-position 50 mL acrylic tube rack | 80 × 80 × 30 white | (0.00, +0.15) | Holds the Falcon tubes upright before and after the spin. |
| 5 | **Falcon tube — pre-spin** | Corning Falcon 50 mL polypropylene conical tube (P/N 352070) | Ø30 × 115 + Ø32 × 10 orange cap | (-0.020, +0.130) | Carries the dilution about to be spun. Body colour = cloudy reddish (pulp suspended throughout). |
| 6 | **Falcon tube — post-spin** | Same as above | Ø30 × 115 + Ø32 × 10 orange cap | (+0.020, +0.130) | Already spun: a dark Ø29 × 15 mm pellet at the bottom, light reddish-clear supernatant above. This is the visual reference for what the arm pours off. |
| 7 | **Falcon tubes — empty (×2)** | Same as above | Ø30 × 115 + cap | (±0.020, +0.170) | Clean spares so the workflow can re-spin or balance the rotor. |
| 8 | **Source flask (100 mL)** | Corning Pyrex 5640 Class A 100 mL volumetric flask (P/N 5640-100) | Foot Ø50 × 5, bulb Ø60 sphere with light-reddish liquid inside, neck Ø12 × 140 | (-0.05, -0.30) | The Step 3 dilution that gets decanted into the Falcon tube. Same flask model as `gazebo_worlds/03-dilution/`. |
| 9 | **Syringe (10 mL)** | BD Plastipak Luer-Lok 10 mL (P/N 309604) | Barrel Ø16 × 90 + plunger Ø11 × 70 + Ø22 thumb pad + Ø6 × 8 Luer tip; total ~140 | (0.10, +0.05) lying along Y | Draws the supernatant out of the post-spin tube and pushes it through the filter. |
| 10 | **Syringe filter** | Millex-HV 0.45 µm PVDF, 25 mm OD Luer-Lok (P/N SLHVR25NB) | Disc Ø25 × 7 + inlet Ø6 × 8 + outlet Ø3 × 8 | (0.10, -0.05) lying along Y | The actual filtration membrane. 0.45 µm pore traps particles before they reach the HPLC column. The doc names 0.45 / 0.22 µm. |
| 11 | **Receiving beaker (100 mL)** | Corning Pyrex 1000 low-form, 100 mL (P/N 1000-100) | Ø50 × 70 clean glass | (0.10, -0.20) | Collects the filtrate. Empty in this world (it gets filled during the workflow run). |

### Why these objects in particular

The ketchup paragraph of the doc is one sentence: *spin → pour off →
filter*. The objects above cover each sub-step:

| Doc sub-step | Object responsible |
|---|---|
| "carry the dilution over from Step 3" | source flask |
| "transfer the cloudy dilution into a Falcon tube" | pre-spin Falcon tube + tube rack |
| "spin so pulp packs into a pellet" | centrifuge |
| "carefully pour off the clearer top liquid" | post-spin Falcon tube (visual reference for the two layers) |
| "draw it into a syringe" | 10 mL syringe |
| "push gently through a 0.45 µm filter" | Millex-HV 0.45 µm syringe filter |
| "collect the clean filtrate" | receiving beaker |

### What was deliberately left out

- **Pipette / Pasteur tools.** Pouring off the supernatant is usually
  done by tilting the whole tube, not by aspirating. A pipette would
  also disturb the pellet. The doc says *pour off*, so we left a
  pipette off the bench.
- **Vacuum manifold / Buchner funnel.** The doc only mentions syringe
  filtration. Vacuum filtration is a different routine, more common in
  industrial settings.
- **HPLC column.** Downstream of this entire workflow. Lives in the
  HPLC instrument, not on the bench.
- **Discard tube for first drops.** Real SOP often discards the first
  few drops of filtrate (the "loose particle flush"). Implied by the
  workflow but not a separate physical container on most benches —
  the operator just aims those drops at a wipe.
- **Loose Falcon-tube caps.** Caps stay on the tubes during the spin
  (they have to — otherwise the rotor leaks). All four tubes are
  drawn capped here.

## Arm placeholder

Yellow Ø100 mm disc at **(-0.22, 0.00)**. Same position as Steps 2
and 3. Install an arm with:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

Reach check: the centrifuge lid centre at (-0.05, +0.30) is ~344 mm
from the arm marker — outside myCobot's ~280 mm envelope. For a
myCobot you would have to move the centrifuge closer or pick a
longer-reach arm (UR3 / FR3).

## Coordinate sanity check

Bench top at **z = 0.900 m**. Tallest item: the centrifuge lid top at
**z = 1.150** (250 mm above bench). The arm needs ≥ 280 mm of vertical
clearance to lift a Falcon tube clear of the centrifuge rotor well.

## Is one Gazebo world enough for Step 4?

**Yes**, for the ketchup case. The whole spin → pour → filter
sequence happens at one bench. A `paracetamol_filtering.sdf` sibling
would be much sparser (no centrifuge, no Falcon tubes — paracetamol
needs only the syringe + filter + receiving vessel).

## File list

```
04-filtering/
├── README.md                  (this file)
└── ketchup_filtering.sdf      (the Gazebo world)
```
