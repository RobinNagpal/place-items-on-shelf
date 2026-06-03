# 01 — Task And Objects

> Answers questions **1** and **2** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "What is the task, in one sentence?" and "What objects is the robot
> handling?"

## The task, in one sentence

> Pick a 2 mL HPLC sample vial from an inbound rack, read its
> barcode, and place it in the correct slot of an HPLC autosampler
> tray.

That is the whole loop. Everything else in this requirements folder
is conditions on how well, how fast, and under what limits the robot
must do this loop.

## The objects

The robot only touches three classes of object: the **vial**, the
**source rack**, and the **destination tray**. Below each one, the
realistic numbers come from public datasheets — see Sources.

### Object 1 — HPLC sample vial (the only object actually gripped)

| Property            | Value                                                                |
|---------------------|----------------------------------------------------------------------|
| Shape               | Cylinder with a small cap on top                                     |
| **Outer diameter**  | **12 mm** (industry standard)                                        |
| **Height**          | **32 mm** (industry standard)                                        |
| Nominal volume      | **2 mL** (1.5 mL also common; 1 mL "low-volume" variants exist)      |
| Material            | USP Type 1 Class A, **borosilicate glass** (clear or amber)          |
| Weight (filled)     | ~5–10 g                                                              |
| Cap type            | **Screw cap (9 mm or 10 mm thread)** or **crimp cap (11 mm)**         |
| Septum              | Thin PTFE/silicone disc inside the cap                               |
| Fragility           | Glass — cracks if pinched too hard; cap can pop if shaken            |
| Surface             | Smooth glass — slippery, especially if cold or wet from condensation |

**What this means for the gripper:**

- Inner finger spacing must accommodate 12 mm + a small grip pad.
- Grip force must hold ~10 g securely **without cracking glass** —
  this argues for soft pads (silicone) and a force-limited gripper.
- The vial centre of mass is ~16 mm above the table when standing,
  so the gripper should grip near the **upper third** of the vial
  to keep it upright.

### Object 2 — Inbound rack (the source)

| Property      | Value                                                                  |
|---------------|------------------------------------------------------------------------|
| Material      | Polypropylene (most common) or aluminium                               |
| Layout        | Grid of round holes, often **6 × 8 = 48** or **5 × 10 = 50** slots     |
| Hole diameter | ~13 mm (a hair wider than the vial)                                    |
| Footprint     | Roughly 150 × 200 mm                                                   |
| Sits on       | Lab bench, fixed position                                              |
| Vial fit      | Vial sits upright with ~25–30 mm of vial above the rack surface         |

**What this means for the robot:**

- A vial in the rack is **mostly above** the rack surface — about
  25 mm exposed — so the gripper does **not** need to reach down
  into a hole. Top-down grip works.
- The rack does not need to be standardised across labs; perception
  can find each vial by its top.

### Object 3 — HPLC autosampler tray (the destination)

| Property              | Value                                                            |
|-----------------------|------------------------------------------------------------------|
| Layout (v1 target)    | **96 positions** in a roughly 8 × 12 grid                        |
| Other common layouts  | 15, 40, 100 positions (vendor-specific)                          |
| Material              | Metal or plastic, vendor-specific                                |
| Slot diameter         | ~14 mm (about 2 mm wider than the vial)                          |
| **Slot clearance**    | **~1 mm radial** — placement tolerance is roughly **±1 mm**       |
| Footprint             | Vendor-specific, roughly 150 × 200 mm                            |
| **Location during loading (v1)** | **On the bench, in an alignment plate next to the arm — NOT inside the HPLC.** |
| Tray orientation      | Numbered, with slot 1 in a fixed corner                          |

**Why the tray is on the bench, not in the instrument:**

Most HPLC autosamplers either house the tray fully inside (carousel
style) or behind a small drawer opening that is hard for a robot
wrist + gripper to fit through. Agilent themselves sell an
**"external tray" / WalkUp** option on the 1290 Infinity II
Vialsampler precisely so robots can load on the bench and a
transport step delivers the tray into the instrument afterwards.
v1 follows the same pattern: **the robot loads on the bench, then
a human carries the loaded tray the short distance into the
autosampler drawer.** See
[`../03-manual-steps-today.md`](../03-manual-steps-today.md) Step C
for the full rationale.

**What this means for the robot:**

- Placement precision must be on the order of **±1 mm at the slot**
  — see [`03-success-precision-speed.md`](03-success-precision-speed.md).
- Vendor differences (Agilent vs Waters vs Shimadzu) mostly affect
  tray *footprint*, not slot geometry. v1 targets one tray at a
  time, sitting in a fixed alignment plate calibrated to the arm.
- **The arm never has to reach inside the HPLC.** This is by design
  — it removes a whole class of collisions and lets us use a much
  smaller (and cheaper) arm.

## Variations the robot should handle later (not v1)

These are explicitly **not v1 requirements**, but they should not be
*designed out*:

- **1 mL vials** (same outer 12 × 32 mm body, smaller inner volume).
- **Screw vs crimp cap** (same overall geometry, different grip
  height by a few millimetres).
- **Amber vs clear glass** (changes how perception sees the vial —
  amber is much harder for a simple RGB camera).
- **Partial racks** (not every slot is filled at the start).

## Sources

- [Standard autosampler vials (12 × 32 mm) — Sigma-Aldrich](https://www.sigmaaldrich.com/US/en/product/aldrich/z291706)
- [Understanding 2 mL Vial Sizes and Volumes — MTC HPLC Primer](https://www.mtc-usa.com/kb-article/aa-01800)
- [HPLC vials product overview — Thermo Fisher](https://www.thermofisher.com/us/en/home/industrial/chromatography/chromatography-consumables/autosampler-vials-caps-hplc-gc.html)
- [Sample Vials and Accessories — Waters PDF](https://www.waters.com/webassets/cms/library/docs/720001818en.pdf)
- [Block, 24 × 2 mL Autosampler vials (12 × 32 mm) — Calpaclab](https://www.calpaclab.com/block-24x2ml-autosampler-hplc-vials-12x32mm-benchmark/bm-h5000-1232)
- [Agilent autosampler trays (15 / 40 / 100 positions)](https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/autosampler-fraction-collector-supplies-for-hplc/sample-trays-for-hplc)

→ Next: [`02-environment.md`](02-environment.md)
