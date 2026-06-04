# 01 — Task And Objects

> Answers questions **1** and **2** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "What is the task, in one sentence?" and "What objects is the robot
> handling?"

## The task, in one sentence

> Pick a **2 mL, 12 × 32 mm HPLC sample vial** from a **50-position
> polypropylene rack**, read its barcode, and place it in the
> correct slot of a **100-position Agilent autosampler tray**
> sitting in a benchtop alignment plate.

This sentence already names the exact reference products — see the
three Object sections below for full specs.

That is the whole loop. Everything else in this requirements folder
is conditions on how well, how fast, and under what limits the robot
must do this loop.

## The objects

The robot only touches three classes of object: the **vial**, the
**source rack**, and the **destination tray**. The numbers below
come from specific commercial products that we treat as the v1
reference, so the rest of the project can lock in dimensions
without guessing. Sources are at the bottom.

### Object 1 — HPLC sample vial (the only object actually gripped)

**Reference product:** [9 mm HPLC autosampler vial — hplcvials.com](https://www.hplcvials.com/product/autosampler-vial/9mm-hplc-autosampler-vial.html)
(this is the catalogue item the project owner pointed at as the
target vial).

| Property            | Value (from the reference product)                                   |
|---------------------|----------------------------------------------------------------------|
| Shape               | Cylinder with a small cap on top                                     |
| **Outer diameter**  | **12 mm** (the "12" in 12 × 32 mm)                                   |
| **Height**          | **32 mm** (the "32" in 12 × 32 mm)                                   |
| Neck diameter       | **9 mm**, screw thread                                                |
| Cap material        | **Polypropylene** (PP), 9 mm screw cap                               |
| Septum              | **PTFE / silicone**, either non-slit or pre-slit                     |
| Nominal volume      | **1.5 – 2.0 mL** (the listed range)                                  |
| Material            | **Borosilicate glass, USP Type I (1st hydrolytic class)** — clear or amber |
| Weight (filled)     | ~5–10 g (estimated; product page doesn't list it)                    |
| Compatible inserts  | 250 µL / 300 µL                                                      |
| Fragility           | Glass — cracks if pinched too hard; cap can pop if shaken            |
| Surface             | Smooth glass — slippery, especially if cold or wet from condensation |

**What this means for the gripper:**

- Inner finger spacing must accommodate **12 mm** plus a small grip
  pad on each side. Plan ~14 mm jaw opening.
- Grip force must hold ~10 g securely **without cracking glass** —
  this argues for soft pads (silicone) and a force-limited gripper.
- The vial centre of mass is ~16 mm above the bench when standing,
  so the gripper should grip near the **upper third** of the vial
  (around the neck transition, below the cap) to keep it upright.
- The **9 mm screw cap** is narrower than the 12 mm body, so a
  step-shaped jaw or a soft pad that wraps the body just below the
  cap gives the most reliable grip.

### Object 2 — Inbound rack (the source)

**Reference product:** [MicroSolv MV9502R-02B — 50-position polypropylene rack for 12 × 32 mm vials](https://www.analytics-shop.com/us/mv9502r-02b)
(a widely available off-the-shelf 50-slot rack — confirmed
compatible with the 12 × 32 mm reference vial above). Equivalent
50-position racks are sold by Fisher, Aijiren, and others.

| Property      | Value (from the reference product)                                     |
|---------------|------------------------------------------------------------------------|
| Material      | **Polypropylene (PP)**, chemically resistant to most HPLC solvents     |
| Layout        | **50 wells, alphanumerically indexed** (typical 5 × 10 grid)            |
| Compatible vial | **12 × 32 mm autosampler vials**                                       |
| Bottoms       | Accommodates **both conical and flat-bottom vials**                    |
| Stackable     | Yes                                                                    |
| Autoclavable  | Yes                                                                    |
| Footprint     | Vendor sheet does not publish exact L × W; typical 50-position racks are ~110 × 220 mm |
| Vial fit      | Vial sits upright with **~25–30 mm of vial above the rack surface**     |

**What this means for the robot:**

- A vial in the rack is **mostly above** the rack surface — about
  25 mm exposed — so the gripper does **not** need to reach down
  into a hole. Top-down grip works.
- The rack is **stackable and indexed**, so v1 perception can rely
  on the rack's printed grid as a coarse pose check before each
  pick.
- Different brands of 50-position racks are dimensionally similar
  but not identical — when the project picks a specific rack, we
  calibrate the rack's pose into the arm's world frame once.

### Object 3 — HPLC autosampler tray (the destination)

**Reference product line:** [Agilent vial trays and drawers for HPLC autosamplers](https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/autosampler-fraction-collector-supplies-for-hplc/sample-trays-for-hplc)
(the trays catalogue the project owner pointed at as the
destination side).

**Reference instrument:** [Agilent 1290 Infinity II Vialsampler datasheet (PDF)](https://hpst.cz/sites/default/files/oldfiles/5991-6286en.pdf).
That datasheet gives the concrete numbers below.

| Property              | Value (from the Vialsampler datasheet)                           |
|-----------------------|------------------------------------------------------------------|
| **v1 target tray**    | **Agilent 100 × 2 mL "classic" tray** — straight 10 × 10 grid     |
| Default 1290 II layout | **66 × 2 mL vials per drawer**, **2 drawers = 132 vials total**  |
| Other supported trays | **36 × 6 mL vials** (2 trays); **40 × 6 mL** and **15 × 6 mL** also catalogued |
| Material              | Metal or plastic, vendor-specific                                |
| Slot diameter         | **~14 mm** (about 2 mm wider than the 12 mm vial)                |
| **Slot clearance**    | **~1 mm radial** — placement tolerance is roughly **±1 mm**       |
| Footprint             | Vendor catalogue does not publish a single number; the drawer fits inside the instrument cube of **324 × 396 × 468 mm**, so each tray is well under 300 × 400 mm |
| **Location during loading (v1)** | **On the bench, in an alignment plate next to the arm — NOT inside the HPLC.** Picks the Agilent "external tray" / WalkUp pattern. |
| Tray orientation      | Numbered, with slot 1 in a fixed corner                          |
| Compatible HPLC instrument (reference) | Agilent 1290 Infinity II Vialsampler (G7129B / G7129C). Same trays also fit the 1260 / 1290 family. |

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
[`../research/03-manual-steps-today.md`](../research/03-manual-steps-today.md) Step C
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

- **1 mL low-volume vials** (same outer 12 × 32 mm body, smaller
  inner volume — gripper is unaffected).
- **Screw vs crimp cap** (same overall vial body, but crimp cap is
  ~1 mm taller and not threaded — different grip height by a few
  millimetres).
- **Amber glass** (the reference product lists both clear and
  amber; amber is much harder for a simple RGB camera to see).
- **Partial racks** (not every slot is filled at the start of a
  run).
- **6 mL vials** (used with Agilent 36 × 6 mL or 15 × 6 mL trays;
  bigger body, different gripper opening).
- **Other tray sizes** in the Agilent family (15 / 40 / 132). v1
  pins to the 100-position 2 mL tray.

## Sources

**Reference products (the catalogue items this requirements doc is
pinned to):**

- **Vial:** [9 mm HPLC autosampler vial — hplcvials.com](https://www.hplcvials.com/product/autosampler-vial/9mm-hplc-autosampler-vial.html) — confirms 12 × 32 mm, 9 mm neck, PP cap, PTFE/silicone septum, USP Type I borosilicate glass, 1.5–2.0 mL.
- **Source rack:** [MicroSolv MV9502R-02B 50-position vial rack — analytics-shop.com](https://www.analytics-shop.com/us/mv9502r-02b) — polypropylene, 50 indexed wells, stackable, autoclavable, accepts conical or flat-bottom 12 × 32 mm vials.
- **Destination tray family:** [Agilent vial trays and drawers for HPLC autosamplers — agilent.com](https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/autosampler-fraction-collector-supplies-for-hplc/sample-trays-for-hplc) — Agilent's catalogue of 15 / 40 / 100 / 132-position trays.
- **Reference instrument:** [Agilent 1290 Infinity II Vialsampler data sheet (PDF, hpst.cz mirror)](https://hpst.cz/sites/default/files/oldfiles/5991-6286en.pdf) — confirms 132 × 2 mL standard capacity (2 × 66-vial drawers), 100 × 2 mL classic-tray option, 36 × 6 mL option, instrument cube 324 × 396 × 468 mm, 19 kg, 350 W.

**Background / cross-references (general standards, not the v1
catalogue choice):**

- [Standard autosampler vials (12 × 32 mm) — Sigma-Aldrich](https://www.sigmaaldrich.com/US/en/product/aldrich/z291706)
- [Understanding 2 mL Vial Sizes and Volumes — MTC HPLC Primer](https://www.mtc-usa.com/kb-article/aa-01800)
- [HPLC vials product overview — Thermo Fisher](https://www.thermofisher.com/us/en/home/industrial/chromatography/chromatography-consumables/autosampler-vials-caps-hplc-gc.html)
- [Sample Vials and Accessories — Waters PDF](https://www.waters.com/webassets/cms/library/docs/720001818en.pdf)

→ Next: [`02-environment.md`](02-environment.md)
