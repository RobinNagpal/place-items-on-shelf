# 06 — How HPLC Vials Are Prepared

> **Who this is for:** Anyone who wants to know exactly what a
> lab technician does *before* a vial ever enters the autosampler
> tray. Plain English, no chemistry background assumed. This is
> the deep-dive that [`02-what-is-hplc-and-an-autosampler.md`](02-what-is-hplc-and-an-autosampler.md)
> and [`03-manual-steps-today.md`](03-manual-steps-today.md) refer
> to.

## What this doc is

A 2 mL glass HPLC vial doesn't materialise full and capped. Every
single vial that rides in the autosampler tray went through a
prep workflow on the bench, run by a human, with weighing,
dissolving, mixing, filtering, and sometimes more. **Prep is
where most of the lab's time and skill goes.** The HPLC is fast;
prep is slow.

This doc covers, in order:

1. The **final vial** — what the autosampler actually sees.
2. The **full step list** — every common step that can appear in
   a prep workflow.
3. The **equipment** for each step — concrete tools with
   typical models.
4. **Worked recipes** — five end-to-end examples covering very
   different sample types.
5. **Special techniques** — SPE, protein precipitation,
   liquid–liquid extraction, QuEChERS, derivatization.
6. **Common mistakes** — what trips up new technicians.

## What the autosampler sees at the end

After all the prep is done, every vial in the tray has the same
shape:

| Property         | Value                                                              |
|------------------|--------------------------------------------------------------------|
| Vial             | 2 mL glass, 12 × 32 mm, 9 mm neck                                  |
| Cap              | Polypropylene screw cap, with a PTFE/silicone septum               |
| **Fill volume**  | **1.0 – 1.5 mL** of clean liquid (never full — needs headspace)   |
| **Headspace**    | **0.5 – 1.0 mL** of air above the liquid                          |
| Liquid is        | Particle-free, clear (unless an amber vial is required for light-sensitive samples) |
| Concentration    | Inside the validated method's working range (typically 0.01 – 10 mg/mL of the analyte) |
| Solvent          | Compatible with the HPLC mobile phase                              |
| Bubbles          | None inside the liquid (a bubble at the needle = a failed injection) |
| Label / barcode  | Sticker or hand-written ID linking the vial to the LIMS sample ID  |

If any of these is wrong, the HPLC either skips the vial, gives a
bad reading, or damages the column. Prep exists to make sure all
of them are right, every time.

## The full step list

A vial is prepared by running **a subset** of the following steps,
in order. Not every sample uses every step.

| #  | Step                       | Purpose                                                              | When it is skipped                                  |
|----|----------------------------|----------------------------------------------------------------------|------------------------------------------------------|
| 1  | **Sub-sample / aliquot**   | Take a representative portion from the bulk material                  | Sample already arrives at the right size            |
| 2  | **Weigh**                  | Know the exact mass of solid (or solid-like) sample, ±0.1 mg          | Liquid sample measured by volume only               |
| 3  | **Dissolve**               | Get the analyte into solution in a defined solvent                    | Sample is already liquid (water, plasma, juice)     |
| 4  | **Mix**                    | Make sure the solute is fully dissolved (no settled powder)           | Sample is already homogeneous liquid                 |
| 5  | **Extract** (optional)     | Pull the analyte out of a complex matrix (blood, food, soil)          | Matrix is clean (e.g. a dissolved tablet)           |
| 6  | **Centrifuge** (optional)  | Separate denser particles or precipitated protein from the liquid     | Sample stayed clear through mixing                  |
| 7  | **Dilute**                 | Bring the analyte concentration into the detector's working range     | Sample is already at the right concentration         |
| 8  | **Filter**                 | Remove particles ≥ 0.22 µm or 0.45 µm so the HPLC column does not clog | Almost never skipped                                |
| 9  | **Transfer**               | Pipette ~1.0 – 1.5 mL into a 2 mL HPLC vial                          | Never skipped                                       |
| 10 | **Cap**                    | Screw cap or crimp cap to seal                                        | Never skipped                                       |
| 11 | **Label**                  | Barcode sticker (regulated labs) or hand-written ID                   | Never skipped (run is untraceable otherwise)        |

Steps 1, 5, 6 are the most workflow-specific. Steps 8 – 11 are
near-universal.

## Equipment per step

These are the tools that actually sit on the bench. Brand names
are common picks, not requirements.

| Step                | Equipment                                                                                       | Typical models                                                                                              |
|---------------------|-------------------------------------------------------------------------------------------------|-------------------------------------------------------------------------------------------------------------|
| Weigh               | Analytical balance, 0.1 mg readability                                                          | Mettler Toledo XPR, Sartorius Cubis II                                                                      |
| Dissolve            | Volumetric flask (Class A, 10 / 25 / 100 mL), solvent dispenser                                 | Brand / Hirschmann Class A glassware                                                                        |
| Pipette aliquots    | Adjustable micropipette (10 µL – 5 mL), serological pipette (5 / 10 / 25 mL)                    | Eppendorf Research Plus, Gilson Pipetman                                                                    |
| Mix                 | Vortex mixer, ultrasonic bath ("sonicator")                                                     | Scientific Industries Vortex-Genie 2, Branson 1800 (40 kHz ultrasonic bath)                                  |
| Centrifuge          | Microcentrifuge (for 1.5 / 2 mL tubes), benchtop centrifuge (for 15 / 50 mL tubes)              | Eppendorf 5424, Thermo Sorvall ST 8                                                                          |
| Extract (SPE)       | SPE cartridges + vacuum manifold                                                                | Waters Oasis HLB, Phenomenex Strata-X, Supelco Discovery, Visiprep 12-port manifold                          |
| Extract (LLE / protein crash) | Glass test tubes, separating funnel, polypropylene microtubes                           | Eppendorf Safe-Lock 1.5 mL                                                                                  |
| Filter              | Syringe (1 / 3 / 5 mL) + syringe filter (13 mm or 25 mm, 0.22 / 0.45 µm, PVDF / nylon / PTFE)  | Pall Acrodisc, Millipore Millex, Phenomenex Phenex                                                          |
| Transfer            | Disposable Pasteur pipette, glass dropper, or the same micropipette                              |                                                                                                              |
| Cap                 | Hand-twist (screw cap) or manual / pneumatic crimper (crimp cap)                                | National Scientific Vial Crimper                                                                            |
| Label               | Thermal-transfer label printer + LIMS                                                            | Zebra ZD420, Brady BBP30                                                                                    |

A well-equipped pharma QC bench has all of these within arm's
reach of the sample-prep workstation.

### Choosing the right syringe filter

The filter is one of the few prep choices that can silently ruin
a result. Three filter materials cover almost every HPLC sample:

| Filter material  | Best for                                                                                 | Avoid for                                              |
|------------------|------------------------------------------------------------------------------------------|--------------------------------------------------------|
| **PVDF**         | Aqueous samples, biological samples (plasma, urine), low protein binding                  | Strong organic solvents (DMSO, THF)                    |
| **Nylon**        | General aqueous + mild-organic mixes (water + methanol, water + acetonitrile)             | Strong acids or strong bases                           |
| **PTFE**         | Pure organic solvents, strong acids, strong bases                                         | Plain aqueous (PTFE needs a wetting step)              |

And pore size:

- **0.45 µm** — default for "is there visible cloud or dust?". Faster.
- **0.22 µm** — UHPLC columns with sub-2-µm particles, or any LC-MS method, because tiny particles kill the column.

## Worked recipes — five real use cases

Each recipe is the actual sequence a technician runs. Volumes are
realistic ballparks from public methods.

### Recipe A — Paracetamol tablet (pharma assay)

Goal: prove a batch of 500 mg paracetamol tablets has the labelled
dose.

1. Pick **20 tablets at random** from the batch.
2. **Crush** them together in a mortar to a fine, even powder.
3. **Weigh** an amount equivalent to one tablet (about 0.5 g) on
   the analytical balance, recording the exact mass to 0.1 mg.
4. **Transfer** the powder into a 100 mL Class A volumetric flask.
5. **Add** ~70 mL of mobile phase (typically 50 % methanol / 50 %
   water with 0.1 % phosphoric acid).
6. **Sonicate** the flask in the ultrasonic bath for 10 min to
   dissolve.
7. **Cool** to room temperature, then **dilute to the mark** with
   more mobile phase to reach exactly 100 mL.
8. **Pipette** 1 mL of this stock into a 10 mL Class A volumetric
   flask and **dilute to the mark** with mobile phase — gives a
   working concentration of ~0.5 mg/mL.
9. **Filter** ~2 mL through a 0.45 µm nylon syringe filter,
   discarding the first ~0.5 mL.
10. **Transfer** ~1.2 mL into a clean 2 mL HPLC vial, **cap**,
    **label** with the batch ID barcode.

Steps used: 1, 2, 3, 4, 7, 8, 9, 10, 11.

### Recipe B — Single tablet for content uniformity

Goal: USP &lt;905&gt; — test 10 individual tablets to prove the
active is evenly distributed within a batch.

1. **Weigh** one whole tablet on the analytical balance.
2. **Transfer** it into a 100 mL Class A volumetric flask.
3. **Add** ~70 mL of mobile phase.
4. **Sonicate** for 10 min until the tablet fully disintegrates.
5. **Cool** to room temperature, **dilute to the mark** with
   mobile phase.
6. **Pipette** 1 mL into a 10 mL flask, **dilute to the mark**.
7. **Filter** through 0.45 µm nylon.
8. **Transfer** to a 2 mL vial, **cap**, **label**.
9. **Repeat steps 1 – 8** for 9 more individual tablets — same
   batch, separate vials, separate labels.

Steps used: 2, 3, 4, 7, 8, 9, 10, 11. Repeated 10 times for one
batch.

### Recipe C — Patient plasma drug monitoring (protein crash)

Goal: measure the level of an anti-epileptic (e.g. carbamazepine)
in a patient's blood plasma so the doctor can adjust the dose.

1. **Centrifuge** the patient's blood tube (collected on EDTA) at
   3,000 g for 10 min — separates plasma from red cells.
2. **Pipette** 100 µL of plasma into a labelled 1.5 mL
   polypropylene microtube.
3. **Add** 200 µL of cold acetonitrile (kept on ice) drop-wise
   while vortexing — this **crashes the plasma proteins** out of
   solution.
4. **Vortex** for 30 s at max speed to mix fully.
5. **Centrifuge** the microtube at 14,000 g for 5 min — protein
   pellets at the bottom, clear supernatant on top.
6. **Pipette** ~250 µL of the supernatant into a clean microtube,
   careful not to touch the pellet.
7. **Add** 250 µL of HPLC-grade water to dilute the supernatant
   back toward an aqueous solvent (so it matches the starting
   mobile phase).
8. **Filter** through a 0.22 µm PVDF syringe filter.
9. **Transfer** ~1 mL into a 2 mL HPLC vial, **cap**, **label**
   with the patient's barcoded sample ID.

Steps used: 3 (sort of — "dissolve" = solvent extraction), 5
(protein crash), 6, 8, 9, 10, 11. Total bench time per sample
~15 min; many samples processed in parallel.

### Recipe D — Pesticide in groundwater (SPE concentration)

Goal: measure trace atrazine in 1 L of drinking-water source
water — concentration is in **ng/L**, so the sample has to be
concentrated by a factor of ~1,000.

1. **Filter** the 1 L water sample through a 0.45 µm glass-fibre
   filter to remove sediment.
2. **Adjust** the pH to ~7 if the water is naturally acidic or
   basic — a pH meter and a few drops of dilute HCl or NaOH.
3. **Condition** the SPE cartridge (e.g. Waters Oasis HLB 200 mg)
   on a 12-port vacuum manifold:
   - Pass 5 mL of methanol.
   - Pass 5 mL of HPLC-grade water.
4. **Load** the 1 L water sample through the cartridge at ~10
   mL/min using the manifold vacuum (takes ~100 min).
5. **Wash** the cartridge with 5 mL of 5 % methanol in water to
   remove water-soluble interferences.
6. **Dry** the cartridge under vacuum for 5 min.
7. **Elute** the analyte with 2 × 2 mL of methanol into a
   collection tube — collects ~4 mL of methanol containing all
   the atrazine that was on the cartridge.
8. **Evaporate** to dryness under a gentle nitrogen stream at
   40 °C (concentrates the analyte to a tiny invisible film).
9. **Reconstitute** in 1 mL of 50 % methanol / 50 % water —
   effective concentration factor = 1,000×.
10. **Filter** through a 0.22 µm PTFE syringe filter.
11. **Transfer** to a 2 mL HPLC vial, **cap**, **label**.

Steps used: 5 (SPE), 8, 9, 10, 11. Bench time per sample
~3 hours, mostly waiting for the load and the nitrogen-blow-down.

### Recipe E — Caffeine in cola (food QC)

Goal: confirm caffeine content matches the label on a soft-drink
production batch.

1. **Pour** ~25 mL of cola into a beaker.
2. **Degas** by sonicating for 5 min (removes the CO₂ so volumes
   measure correctly).
3. **Pipette** 1 mL of the degassed cola into a 10 mL volumetric
   flask.
4. **Dilute to the mark** with HPLC-grade water — gives ~10×
   dilution.
5. **Filter** through 0.45 µm nylon.
6. **Transfer** to a 2 mL HPLC vial, **cap**, **label**.

Steps used: 7, 8, 9, 10, 11. Bench time ~10 min — among the
easiest prep workflows.

### Recipe F — Calibration standards (serial dilution from a stock)

Goal: build the 5 calibration vials that slot into positions
2 – 6 of every tray.

1. **Weigh** 10.0 mg of the pure reference standard on the
   analytical balance.
2. **Transfer** to a 100 mL Class A volumetric flask.
3. **Dissolve** in ~50 mL of solvent and **dilute to the mark** —
   gives a **stock at 100 µg/mL**.
4. **Serial-dilute** into 10 mL volumetric flasks to make the
   working calibrators:

| Calibrator | Volume of stock to take | Final volume | Final concentration |
|------------|-------------------------|--------------|---------------------|
| Cal 1      | 100 µL                  | 10 mL        | 1 µg/mL             |
| Cal 2      | 500 µL                  | 10 mL        | 5 µg/mL             |
| Cal 3      | 1.0 mL                  | 10 mL        | 10 µg/mL            |
| Cal 4      | 5.0 mL                  | 10 mL        | 50 µg/mL            |
| Cal 5      | (use the stock at 100 µg/mL directly) | — | 100 µg/mL |

5. **Filter** each calibrator through 0.45 µm nylon.
6. **Transfer** ~1.2 mL into a clean 2 mL HPLC vial, **cap**,
   **label** with "CAL-1" through "CAL-5".

Steps used: 2, 3, 7, 8, 9, 10, 11. Bench time ~30 min; the
calibrators are usually prepared **first** and used as anchor
points for the rest of the run.

## Special techniques (called out)

These show up in some of the recipes above but are worth
explaining on their own.

### Solid-Phase Extraction (SPE)

Used in Recipe D. SPE pulls a target compound out of a dirty
matrix and concentrates it. Four steps inside the cartridge:

1. **Condition** — wet the sorbent (methanol, then water).
2. **Load** — pass the sample through; analyte sticks to the
   sorbent.
3. **Wash** — pass a weak solvent that washes interferences off
   but leaves the analyte stuck.
4. **Elute** — pass a stronger solvent that releases the analyte
   into a small collection volume.

SPE is the workhorse of trace analysis (pesticides, drugs in
biological matrices, hormones). It is also the longest single
step in most prep workflows.

### Protein precipitation ("protein crash")

Used in Recipe C. Plasma is mostly proteins, and proteins will
clog any HPLC column. To make plasma HPLC-friendly:

1. Add **2 – 3 volumes of cold acetonitrile** to 1 volume of
   plasma (e.g. 200 µL ACN to 100 µL plasma).
2. **Vortex** to mix.
3. **Centrifuge** — proteins pellet, supernatant is clear.

Acetonitrile crashes about 95 % of plasma proteins. Methanol is
sometimes used too; it is gentler but crashes less. Trichloroacetic
acid is harsher and used when acetonitrile fails.

### Liquid–Liquid Extraction (LLE)

Two immiscible solvents are shaken together; the analyte
preferentially partitions into one. LLE is older than SPE but
still widely used for non-polar drugs in biological matrices.

A typical LLE for a drug in plasma:

1. Add 200 µL of plasma + 100 µL of dilute alkali (to make the
   drug neutral) + 2 mL of methyl-tert-butyl ether (MTBE).
2. **Vortex** for 1 min, then **centrifuge** for 5 min — two
   clear layers form, MTBE on top.
3. **Pipette** the MTBE layer into a clean tube.
4. **Evaporate** under nitrogen, **reconstitute** in mobile phase,
   filter, transfer to vial.

### QuEChERS

Stands for **Q**uick, **E**asy, **C**heap, **E**ffective,
**R**ugged, **S**afe. Standard prep for pesticide residue in
fruit, vegetables, and other food matrices.

Two scoops of pre-packaged salts (one for extraction, one for
cleanup), shake, centrifuge, transfer. Replaced months of
classical LLE/SPE for food labs in the 2010s.

### Derivatization

Some analytes don't have a UV-absorbing group, so the detector
can't see them. Derivatization adds a chemical group (a
"chromophore" or a "fluorophore") that the detector can. Common
in amino-acid analysis and sugar analysis.

Adds 10 – 30 minutes per sample and adds another point where
something can go wrong. Most modern HPLC methods avoid it where
possible by using mass-spec detection instead.

## Common mistakes

The mistakes that come up again and again in lab QA reviews:

1. **Air bubble in the vial.** The autosampler needle picks up
   bubble, injects almost nothing, peaks vanish. Fix: tap the
   capped vial to settle the liquid before loading.
2. **Wrong filter chemistry.** Nylon binds basic drugs; PVDF
   leaches plasticizer into strong organics. Fix: pick the filter
   from the table above by solvent and analyte type.
3. **Headspace too small.** Needle pierces the septum but does
   not reach the liquid — autosampler reports a missed
   injection. Fix: keep fill volume at 1.0 – 1.5 mL, never closer
   than ~3 mm from the cap.
4. **Solvent mismatch with mobile phase.** If the sample solvent
   is much stronger than the mobile phase (e.g. neat methanol
   sample into a 20 % methanol mobile phase), peaks split or tail
   badly. Fix: dilute the sample into something close to the
   starting mobile phase.
5. **Cold sample, condensation on the outside.** A vial straight
   from the fridge picks up condensation that the barcode reader
   misreads. Fix: let it equilibrate to room temperature on the
   bench for ~10 min before scanning.
6. **Concentration outside the calibration range.** Detector
   either sees nothing or saturates. Fix: dilute (or concentrate)
   to land between the lowest and highest calibration standard.
7. **Wrong cap / septum.** A non-pre-slit septum on a method that
   needs one tears and drops fibres into the column. Fix: match
   the cap+septum to the method SOP.
8. **Label fell off.** The single most common reason for a sample
   being rejected. Fix: thermal-transfer printed labels on
   bench-grade adhesive — never inkjet, never hand-written on
   smooth glass.

## Where the robot fits in

This whole workflow happens **before** the robot. By the time the
vials hit the inbound rack, they are filled, capped, labelled,
and queued. The robot's only job — pick from rack → barcode
scan → place in tray — starts where this doc ends.

Steps 9 (transfer), 10 (cap), and 11 (label) are the closest
candidates for future automation; v1 keeps them in human hands so
the robot does not need a crimper, a label printer, or a
liquid-handling head.

## Sources

- [HPLC Sample Preparation — Organomation](https://www.organomation.com/hplc-sample-preparation) — end-to-end overview of the prep workflow.
- [Sample Preparation for HPLC Analysis — Drawell](https://www.drawellanalytical.com/sample-preparation-for-hplc-analysis-step-guides-and-common-techniques/) — step-by-step guide with common techniques.
- [HPLC Sample Prep in 4 Steps — Lab Manager](https://www.labmanager.com/hplc-sample-prep-in-4-steps-2214)
- [HPLC Sample Preparation — Phenomenex](https://www.phenomenex.com/knowledge-center/hplc-knowledge-center/guide-to-hplc-testing) — filter chemistry and column considerations.
- [Sample Preparation for Analytical Quality Control — Sartorius brochure](https://www.sartorius.com/download/22726/broch-hplc-preparation-w-1141-e-data.pdf) — pharma-grade prep reference.
- [QuEChERS method overview — AOAC](https://www.aoac.org/) — pesticide-in-food prep standard.
- [USP &lt;905&gt; Uniformity of Dosage Units — overview](https://www.usp.org/) — the content-uniformity test referenced in Recipe B.
- [DPAL HPLC Methodology Manual](https://padproject.nd.edu/assets/385652/hplc_methodology_manual_2020.pdf) — academic-level prep guide.
- [Therapeutic Drug Monitoring by HPLC — NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK551519/) — clinical / plasma prep background.

## What's next

→ Back to [`02-what-is-hplc-and-an-autosampler.md`](02-what-is-hplc-and-an-autosampler.md)
for the big-picture view of how these prepared vials are then
arranged in the autosampler tray, or to
[`03-manual-steps-today.md`](03-manual-steps-today.md) for the
remaining manual steps (cap, label, drawer) that the robot is
sometimes asked to take over.
