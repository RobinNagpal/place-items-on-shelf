# 05 — Transfer to the vial (ketchup case)

Run: `gz sim gazebo_worlds/05-transfer-to-vial/ketchup_transfer_to_vial.sdf`

Gazebo world for HPLC workflow [**Step 5 — Transfer to the vial**](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/05-transfer-to-vial.md),
ketchup case only. The doc says the ketchup case is *not* physically
harder than paracetamol at this step — the liquid is now thin and
clear after filtering. The ketchup difficulty is **bookkeeping**:
*several supplier batches × two-or-three repeat preparations* means
**more vials to track**. So this world is laid out as **3 batches ×
2 replicates = 6 empty vials in a rack**, plus the clean filtered
ketchup from Step 4 and a transfer pipette.

No arm is included. Yellow Ø100 mm disc at the back of the bench
marks where the arm base will go. The project skips Step 6 (Capping),
so there is **no cap tray** on this bench.

## Workflow — what the arm does

Short, in order. Pick → dip → squeeze → drip, then repeat per vial.

1. Pick up the Pasteur transfer pipette.
2. Dip its tip into the source beaker and squeeze the bulb gently to draw clean liquid up.
3. Move the tip over the opening of vial `b1_r1`.
4. Squeeze the bulb gently to drip ~1.5 mL into the vial.
5. Repeat steps 2-4 for the remaining 5 vials, in order: `b1_r2`, `b2_r1`, `b2_r2`, `b3_r1`, `b3_r2`.
6. Put the pipette back on the bench.

## What is on the bench

Frame: **+X = forward**, **+Y = left**, **+Z = up**. Bench top at
**z = 0.900 m**.

| # | Object | Real product reference | Size (mm) | Pose (X, Y) | Purpose |
|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench, 4-leg | Top 1000 × 600 × 50, 4× Ø50 × 850 steel legs | centred at (0, 0) | Work surface. Same as Steps 2 / 3 / 4. |
| 2 | **Arm marker** | n/a — visual flag | Ø100 × 2 yellow disc | (-0.22, 0.00) | Future arm base location. |
| 3 | **Source beaker** (filtered ketchup) | Corning Pyrex 1000 low-form, 100 mL (P/N 1000-100) | Ø50 × 70 with light-reddish translucent contents | (0.00, +0.28) | Carries the clean filtered ketchup from Step 4. The arm aspirates from here. |
| 4 | **Vial tray (6-position)** | 6-position 2 mL HPLC vial tray, dark polymer | 60 × 40 × 25 dark-grey block, 18 mm pitch, **6 visible dark Ø14 mm slot-mouth rings** flush with the top + a white position-1 corner marker | (0.05, 0.00) | Holds the empty vials upright while the arm fills them. Styled to match the **destination tray in Step 8** (Agilent G2255A-style polymer block with visible slot mouths) so the two worlds read as the same family of bench item. |
| 5 | **Vial × 6** (empty) | Agilent 5182-0716 11 mm crimp / screw-top clear glass autosampler vial, 2 mL | Ø12 × 32 borosilicate glass | (0.041 / 0.059, -0.018 / 0.000 / +0.018) | Destination vessels. Named **`vial_bX_rY`** (batch X, replicate Y) — 3 batches × 2 replicates = 6 vials. The arm hits each opening reliably; the doc identifies this exact task as the ideal **first proof-of-concept**. |
| 6 | **Pasteur transfer pipette** | Samco 222-1S 3 mL polyethylene transfer pipette | Bulb Ø14 × 25, stem Ø6 × 110, tip Ø2 × 10; total 145 | (0.15, +0.15) lying along Y | Moves liquid from the source beaker into each vial. Disposable — a fresh one per batch in a stricter SOP, but 1 covers all 6 vials here. |

### Why these objects in particular

The Step 5 doc routine is: have a clean empty vial → take the filtered
liquid → aim over the narrow opening → fill to about 1.5 mL. Mapping:

| Doc sub-step | Object responsible |
|---|---|
| "have a clean, empty vial ready, often in a small rack" | vial tray + 6 empty vials |
| "take the filtered liquid" | source beaker (with the Step 4 output) |
| "aim carefully over the narrow opening and let liquid flow in" | Pasteur pipette (the arm holds it, dips into the source, dispenses over each vial in turn) |
| "fill to roughly the right level, even under 2 mL" | reading the vial graduation by eye (no extra tool needed) |
| "move on to the next vial, keeping each sample strictly separate" | the 6 vials in a 2×3 grid with predictable, distinct `vial_bX_rY` positions for tracking |

### What was deliberately left out

- **Vial caps + the cap tray.** Capping is [Step 6](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/README.md),
  which this project skips because it is hard to automate. So no loose
  caps and no cap tray on this bench.
- **Crimping tool / capper.** Same reason — Step 6.
- **Label printer / pre-printed vial labels.** The doc warns about the
  *wrong vial* mistake but the labelling action itself is a one-time
  pre-step in most SOPs, not part of the pour. Tracking is done by
  rack position in this world.
- **Multiple source beakers.** A stricter SOP would have one source
  vessel per batch. We single-source here for clarity — the bench
  would otherwise read as a different kind of cell (parallel
  preparation rather than transfer).
- **Backup blank vials.** A real run also fills a *solvent blank*
  vial. Not required by the doc's Step 5 paragraph.

## Arm placeholder

Yellow Ø100 mm disc at **(-0.22, 0.00)**. Same position as Steps
2 / 3 / 4. Install an arm with:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

Reach check: every vial in the rack is within (≤ 290 mm) of the
marker — well inside any benchtop arm's reach envelope. The doc
specifically names this step as the **ideal first proof-of-concept**
because reaching a fixed, ~9 mm opening reliably is the right
difficulty for any small benchtop arm including the myCobot 280.

## Coordinate sanity check

Bench top at **z = 0.900 m**. Vial tops at z = 0.932 (32 mm vials).
Source beaker top at z = 0.970. Pipette is ~7 mm thick at the bulb,
so its centre sits at z = 0.907.

## Is one Gazebo world enough for Step 5?

**Yes**, for the ketchup case. The bookkeeping difficulty of "more
vials" is already captured by the 3-batch × 2-replicate naming.

A **paracetamol** sibling would look very similar (5 brands + 1
standard + 1 blank = 7 vials) but with a different naming scheme. A
**capping-aware** version belongs in Step 6, not here.

## File list

```
05-transfer-to-vial/
├── README.md                          (this file)
└── ketchup_transfer_to_vial.sdf       (the Gazebo world)
```
