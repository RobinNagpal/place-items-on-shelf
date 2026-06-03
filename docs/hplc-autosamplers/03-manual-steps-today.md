# 03 — Manual Steps In The HPLC Workflow Today

> **Who this is for:** Anyone who wants to know exactly which parts
> of the HPLC workflow are still done by hand, so they can see why
> tray loading is the right first target for a robot.

A typical HPLC analysis has roughly four stages. The HPLC instrument
itself handles the third one (injection and detection) automatically.
The other three are still mostly manual in most labs.

## Step A — Sample preparation (manual today)

This is the most varied and skilled part. The technician turns raw
material into a clean liquid in an HPLC vial. The exact steps depend
on the sample, but the typical workflow includes:

1. **Sampling** — take a representative portion of the raw material.
2. **Weighing** — measure that portion on an analytical balance
   (typically to ±0.1 mg).
3. **Dissolving** — add a measured amount of solvent (water, methanol,
   acetonitrile, buffer) and mix.
4. **Mixing** — vortex (a small vibrating mixer) or sonicate
   (ultrasonic bath) to fully dissolve the sample.
5. **Diluting** — pipette an aliquot into more solvent to bring the
   concentration into the detector's working range.
6. **Filtering** — push the liquid through a small syringe filter
   (typically **0.22 µm or 0.45 µm** pore size) to remove particles
   that would clog the HPLC column.
7. **Extraction** (only for messy samples) — use a technique like
   **solid-phase extraction (SPE)** to pull the target compound out
   of a complex matrix (blood, food, soil).
8. **Transferring** — pour or pipette the final liquid into a clean
   2 mL HPLC vial.

> **Why this is hard to automate cheaply:** each step needs different
> equipment (balance, vortex, sonicator, pipettor, filter, SPE
> manifold). Real lab-automation systems for sample prep (Hamilton
> STAR, Tecan Fluent, etc.) cost in the tens of thousands of dollars
> and dominate this step.

For this project, **sample prep is out of scope**. We assume the
technician has finished it and the vials are full, capped, and
labelled.

## Step B — Capping and labelling (manual today)

After the vial is filled, the technician:

1. **Caps** the vial. Two common kinds:
   - **Screw cap** — easy; twist by hand.
   - **Crimp cap** — needs a hand crimper or pneumatic crimper to
     squeeze the metal seal onto the vial.
2. **Labels** the vial. Either:
   - **Barcode sticker** (most common in QC labs) — printed from the
     lab system with a unique ID.
   - **Hand-written number** (smaller labs) — on the cap or the
     vial's writing patch.

For this project, **capping is out of scope** for v1. Vials arrive
capped. **Reading the barcode is in scope** — the robot must know
which vial it is holding.

## Step C — Tray loading (manual today — **our target**)

This is the step the robot replaces.

The technician has, say, 96 ready vials in a rack on the bench, and
an empty 96-slot autosampler tray next to them. The job is to:

1. **Pick up vial 1** from the source rack.
2. **(Optionally) scan its barcode** with a hand reader.
3. **Place vial 1 in the correct slot** of the tray.
   - "Correct slot" usually comes from the HPLC method file — a
     numbered list saying which sample goes in which slot.
4. **Repeat for vial 2, 3, …** until the rack is empty or the tray
   is full.

For each placement, the technician must also **write down** (or have
the LIMS write down) the barcode-to-slot mapping. That mapping is
what the HPLC software later uses to label the results.

### Why this step is painful for humans

- **Volume.** A busy QC lab loads hundreds of vials a day.
- **Repetitive.** Pick → walk → place → write → pick → walk → place.
- **Error-prone late in a shift.** A tired tech swaps vials #47 and
  #48 and now every result after that is wrong.
- **Fragile.** Drop a vial; the sample is lost, the glass is sharp.

### Why this step is **good for a robot**

- **One simple object shape.** A 12 × 32 mm cylinder, every time.
- **Two simple locations.** Source rack and destination tray, both
  fixed.
- **Tight but achievable precision.** The tray slot is ~14 mm wide
  for a 12 mm vial — about ±1 mm placement tolerance.
- **Slow tempo.** ~10–20 seconds per vial is fine.
- **Logging is built in.** Everything the robot does, it logs.

## Step D — Drawer in / drawer out (manual today)

After the tray is loaded:

1. The technician **opens the autosampler drawer**.
2. **Slides the tray in.**
3. **Closes the drawer.**
4. **Tells the HPLC software** the barcode-to-slot mapping (this is
   electronic — copy-paste from the LIMS).
5. **Presses Start.**

When the run finishes (often hours later), the same steps run in
reverse to retrieve the tray.

For our project, **drawer in / out is partially in scope**. The arm
can shove and pull a tray if the drawer is the slide-out kind, but
some autosamplers have spring-loaded or motorised drawers that we
will leave to the technician. **Pressing Start is left to the
technician** for v1 — much simpler than integrating with vendor
software.

## Summary table

| Step | What is it? | Status today | Our scope (v1) |
|------|-------------|--------------|----------------|
| A    | Sample prep | Manual + some big-budget liquid handlers | **Out of scope** |
| B    | Cap & label | Manual | **Capping out, barcode reading in** |
| C    | Tray load   | Manual | **In scope — the heart of the project** |
| D    | Drawer & Start | Manual | **Partially in scope (drawer); Start out** |

## Sources

- [HPLC Sample Prep in 4 Steps — Lab Manager](https://www.labmanager.com/hplc-sample-prep-in-4-steps-2214)
- [Sample Preparation for HPLC Analysis — Drawell](https://www.drawellanalytical.com/sample-preparation-for-hplc-analysis-step-guides-and-common-techniques/)
- [Sample Preparation for Analytical Quality Control — Sartorius brochure](https://www.sartorius.com/download/22726/broch-hplc-preparation-w-1141-e-data.pdf)
- [HPLC Sample Preparation — Organomation](https://www.organomation.com/hplc-sample-preparation)
- [DPAL HPLC Methodology Manual](https://padproject.nd.edu/assets/385652/hplc_methodology_manual_2020.pdf)

## What's next

→ Next: [`04-why-automate-tray-loading.md`](04-why-automate-tray-loading.md) —
the case for picking *this* step (and not the others) as the first
robot target.
