# 08 — Placement in the autosampler (ketchup case)

Run: `gz sim gazebo_worlds/08-placement-in-autosampler/ketchup_placement_in_autosampler.sdf`

Gazebo world for HPLC workflow [**Step 8 — Placement in the autosampler**](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/08-placement-in-autosampler.md),
ketchup case only. The doc routine is: pick each finished, capped,
labelled vial and set it gently into its exact numbered slot in the
autosampler tray, in the order the **worklist** demands.

Step 8 is the **headline task** for this whole project — the v1
[spec sheet](../../docs/hplc-autosamplers/requirements/00-spec-summary.md)
pins specific reference products, ±1 mm placement precision, ≤ 20 s
mean cycle time, and 0 mis-slots per 1000 vials against exactly this
routine. The objects in this world are therefore not generic stand-ins;
they are the **same reference parts the spec names**.

No arm is included. Yellow Ø100 mm disc at the back of the bench marks
where the arm base will be bolted down (same convention as Steps 2/3/4/5).

## Workflow — what the arm does

Short, in order. Pick → scan → place, then repeat per vial.

The arm does **not** physically read the worklist printout. The
worklist is stored as software state on the controller — the
controller already knows *which* vial to pick next from the source
rack and *which* destination-tray slot it goes into. The arm just
executes that pick-and-place sequence. The paper printout on the
bench is a human-readable audit copy, not the arm's input.

1. Pick up the next vial from the source rack (the controller dictates the order; the cap colour is the camera's visual cross-check).
2. Move the vial under the barcode reader's red window — wait for the scan to confirm the label matches the controller's expected value for this step.
3. Move the vial over the target slot on the destination tray (use the ArUco fiducial on the alignment plate to re-zero first if needed).
4. Lower it gently into the slot until the cap rests on the tray surface.
5. Release the vial and lift the gripper clear.
6. Repeat steps 1-5 for the remaining vials, in the order the controller specifies, until all 12 slots are filled.

After all 12 vials are placed, the technician (not the arm) carries
the loaded tray over to the HPLC instrument and slides it in.

## What is on the bench

Frame: **+X = forward**, **+Y = left**, **+Z = up**. Bench top at
**z = 0.900 m**.

| # | Object | Real product reference | Size (mm) | Pose (X, Y) | Purpose |
|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench, 4-leg | Top 1000 × 600 × 50, 4× Ø50 × 850 steel legs | centred at (0, 0) | Work surface. Same as Steps 2/3/4/5 for layout continuity. |
| 2 | **Arm marker** | n/a — visual flag | Ø100 × 2 yellow disc | (-0.22, 0.00) | Future arm base location. |
| 3 | **HPLC instrument body** | Agilent 1290 Infinity II Vialsampler (G7129B / G7129C) | 396 × 324 × 468 (D × W × H) cream chassis with a dark autosampler-drawer band and a small green status LED on the front | (-0.50, 0.00), centred at z = 0.234 (floor-standing behind the bench) | The destination machine. Sits **outside the arm's reach envelope by design** — v1 does NOT do in-instrument reaches; the operator carries the loaded tray over after the arm finishes filling it. |
| 4 | **Alignment plate** | Custom 240 × 240 × 6 mm anodized aluminium plate with two Ø3 mm corner locator pins + ArUco-style fiducial | 240 × 240 × 6 plate, top at z = 0.906 | (0.05, 0.00) | The mechanism that recovers the spec's ±1 mm slot precision. Locates the tray to a calibrated bench position; ArUco patch lets the arm camera re-zero per shift. |
| 5 | **Destination tray** | Agilent **G2255A 100-position "classic"** autosampler tray, 10 × 10 grid, 18 mm pitch, Ø14 mm slot ID | 195 × 195 × 50 dark polymer block with 100 visible Ø14 slot mouths and a white "position 1" corner marker | (0.05, 0.00), bottom at z = 0.906 | **The target.** Shown EMPTY here — Step 8 is the act of moving the 12 ketchup vials *into* this grid in worklist order. |
| 6 | **Source rack** | MicroSolv **MV9502R-02B** polypropylene 50-position rack | 150 × 80 × 25 white PP block, 10 × 5 wells, 15 mm pitch, accepts 12 mm OD vials | (0.10, 0.32) | The **starting** vessel. Holds the 12 capped+labelled ketchup vials waiting to be moved. 38 wells are empty (the run uses 12 of 50). |
| 7 | **Worklist printout** | Standard 100 × 70 mm thermal-printed worklist slip | 100 × 70 × 0.2 white paper with 5 thin printed rows | (0.20, 0.32) | A **paper audit copy** of the worklist for the technician. The arm does **not** read this — the pick / place order lives as software state on the controller. The printout is on the bench so a human can spot-check what the run is doing. |
| 8 | **Barcode reader** | USB handheld scanner on vertical stand (e.g. Honeywell Voyager / Zebra DS2208 style) | 60 × 60 × 10 base + Ø12 × 100 stem + 80 × 50 × 40 angled head + red emissive window | (0.20, -0.30) | Per v1 spec the arm **scans every vial barcode before placement** to verify label-to-position match. Reads via USB-HID into the local controller. |

## The 12 ketchup vials and their worklist order

All twelve are the v1 reference vial: a **9 mm HPLC autosampler vial,
12 × 32 mm clear borosilicate glass body, ~5–10 g filled, PP screw cap
with PTFE/silicone septum** (the same vial Step 5 transferred into and
Step 6 capped). The visible cap colour codes which sample the label
identifies:

| Worklist pos | Vial name in SDF | Cap colour | Sample |
|---|---|---|---|
| 1 | `vial_pos1_blank` | white | Blank — solvent only |
| 2 | `vial_pos2_standard` | blue | Pure ketchup-analyte reference standard |
| 3 | `vial_pos3_A_r1` | red | Supplier batch **A**, replicate 1 |
| 4 | `vial_pos4_A_r2` | red | Supplier batch **A**, replicate 2 |
| 5 | `vial_pos5_A_r3` | red | Supplier batch **A**, replicate 3 |
| 6 | `vial_pos6_B_r1` | green | Supplier batch **B**, replicate 1 |
| 7 | `vial_pos7_B_r2` | green | Supplier batch **B**, replicate 2 |
| 8 | `vial_pos8_B_r3` | green | Supplier batch **B**, replicate 3 |
| 9 | `vial_pos9_C_r1` | orange | Supplier batch **C**, replicate 1 |
| 10 | `vial_pos10_C_r2` | orange | Supplier batch **C**, replicate 2 |
| 11 | `vial_pos11_C_r3` | orange | Supplier batch **C**, replicate 3 |
| 12 | `vial_pos12_standard_drift` | blue | Standard repeated at end (drift check) |

The cap colour is a deliberate visual cue: a quick glance at the rack
should match a quick glance at the worklist's first column. Real
labels would carry barcodes too — those come from Step 7 — but the
colour band is what a camera sees fastest in this 12 × 32 mm size.

Why **12** vials specifically? The doc says the ketchup case has
*several supplier batches × 2–3 repeats, plus standard and blank,
perhaps ~8–12 or more*. We picked the top of that band — 3 batches ×
3 replicates + 1 standard + 1 blank + 1 drift-check standard — so the
"more vials to track" theme is unambiguous.

### Why these objects in particular

Step 8 boils down to: take labelled-and-capped vials out of where they
were prepared, and put them where the machine expects to find them.
Mapping:

| Doc sub-step | Object responsible |
|---|---|
| "look at the worklist" | done in **software** by the controller (the arm does not read the worklist); the paper printout is only a technician-side audit copy |
| "take each labelled vial" (starting location) | source rack with the 12 capped+labelled vials |
| "verify label matches the position" | barcode reader + the coloured caps as a quick visual cross-check |
| "set it gently into the matching numbered slot" | destination tray (the 10 × 10 grid) on the alignment plate |
| "slide the tray into the machine" | HPLC instrument body (drawer band facing the bench) — done by the **technician**, not the arm |

### What was deliberately left out

- **An open / extended autosampler drawer.** The doc routine ends with
  the *technician* sliding the tray in. In v1 the arm only loads the
  tray on the bench. Showing an open drawer would suggest the arm
  reaches into it — which it must not.
- **A barcode printer or label roll.** Labelling is Step 7 and has
  already happened by the time we get to Step 8. Vials arrive at the
  source rack already labelled.
- **Empty tray-slot sleeves with depth modelling.** The 100 slots are
  shown as flat Ø14 mm rings on the tray top (the operator's visual
  target) rather than carved-out wells. Gazebo's primitive geometry
  cannot subtract holes from a box; doing this properly would need a
  CAD mesh, which is out of scope for the in-bench overview world.
- **Stir-bar / pipette / centrifuge etc.** All of those belong to
  Steps 2 – 5. Step 8 happens after the prep bench is cleared.
- **E-stop button, status light tower, dock for the gripper.** These
  are real v1-spec safety items but they belong to the **arm cell**
  scene, not the **placement task** scene. Adding them here would
  blur the workflow boundary.

## Arm placeholder

Yellow Ø100 mm disc at **(-0.22, 0.00)**. Same position as Steps
2/3/4/5. Install an arm with:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

**Reach check.** From the arm marker at (-0.22, 0, 0.901):

| Target | Distance | Inside myCobot 280 (~280 mm)? |
|---|---|---|
| Source rack centre (0.10, 0.32) | ~453 mm | **No** |
| Destination tray centre (0.05, 0.00) | ~270 mm | Borderline |
| Tray far corner (0.148, 0.098) | ~380 mm | **No** |
| Barcode reader window (0.22, -0.30) | ~516 mm | **No** |

The v1 spec already calls this out: **myCobot 280 at 280 mm is tight**;
a UR3 / FR3 (≥ 500 mm) or a similar ≥ 300 mm cobot is the realistic
choice for this task. The marker is kept at the Step 2-5 position
only for layout continuity across worlds.

## Coordinate sanity check

Bench top at **z = 0.900 m**. Tallest item on the bench: the
destination tray top at **z = 0.956** (50 mm tall, sitting on the
6 mm plate). Vial caps in the source rack at **z = 0.940**.

The HPLC body sits **on the floor** behind the bench (the bench
itself is hollow underneath). Body centre at z = 0.234, body top at
z = 0.468, drawer band centred at z = 0.234 (i.e. 666 mm below the
bench top). That is well below the arm marker and behind the bench
edge, so the arm cannot reach the drawer from its mount point —
exactly the "outside reach envelope by design" constraint from the
v1 spec.

## Is one Gazebo world enough for Step 8?

**Yes**, for the ketchup case. The whole act — pick from rack, scan,
place into the 10 × 10 grid — happens at one bench with one set of
fixtures.

A **paracetamol** sibling would look mostly identical, with **7
vials** instead of 12 (1 blank + 1 standard + 5 batches + 1 drift
standard) and only one cap colour family. Worth adding later for
contrast, but not necessary to capture the Step 8 routine.

## File list

```
08-placement-in-autosampler/
├── README.md                                  (this file)
└── ketchup_placement_in_autosampler.sdf       (the Gazebo world)
```
