# 02 — What Is HPLC, And What Is An Autosampler?

> **Who this is for:** Anyone who has never seen an HPLC. This doc
> stays short on the chemistry — we only need enough to know what
> the robot is feeding and why standards matter.
>
> The robot only ever touches the **outside** of a vial. But to
> answer "why are we placing 100 vials at once?" or "how strict is
> the order?" we have to know what the *inside* of the vial is for.
> That is what the second half of this doc covers.

## HPLC in one line

**HPLC** = **High-Performance Liquid Chromatography**. A machine
that takes a small volume of liquid sample and tells you what
chemicals are in it, and how much of each. Used everywhere — pharma
QC, food, water, clinical, R&D — and one of the most common
analytical instruments in the world.

We don't need to understand the chemistry. We only need to know:

- It is **automatic** for the testing part — once samples are
  loaded, it runs by itself, often overnight.
- It eats samples from a **tray of small glass vials**.

Everything below is about the tray, the vials, and what is in them,
because that is what the robot has to plan around.

## What is an autosampler?

The **autosampler** is the front piece of the HPLC. Its job is to
**hold many sample vials** and feed them one by one to the
analytical column.

The whole instrument-side flow looks like:

1. Tray of vials sits inside the autosampler.
2. A tiny needle inside the autosampler moves to vial 1, dips
   through the cap, and sips a few microlitres.
3. Repeats for every vial in the tray.
4. Hours later, the tray is done.

**This needle-and-sip part is already automatic.** The robot
project does **not** touch it. The robot's whole job is to
**pre-load the tray** that the autosampler then runs.

## The two standards that matter for the robot

Across nearly every brand (Agilent, Waters, Shimadzu, Thermo
Fisher), two things are standard. Both make the robot's job
much easier.

### Standard 1 — the vial

A small clear glass cylinder, **12 mm × 32 mm**, with a screw or
crimp cap and a thin septum the HPLC needle pierces. **2 mL** is
the most common volume.

That is the *only object shape the gripper has to grasp.* No
brand differences in vial geometry.

> Exact reference product the project pins to (with dimensions,
> material, cap type, septum type):
> [`../requirements/01-task-and-objects.md`](../requirements/01-task-and-objects.md),
> "Object 1 — HPLC sample vial".

### Standard 2 — the tray

A flat plate with a grid of round holes sized for the standard
vial. The most common high-throughput layout is **96 or 100
positions** in a roughly 8 × 12 or 10 × 10 grid. Slot diameter is
~14 mm — about 2 mm wider than the vial, so the robot has roughly
**±1 mm placement tolerance**.

Slot 1 is always in a fixed corner; the rest are numbered in
reading order. So mapping "barcode X goes in slot N" is purely a
software lookup.

> Exact reference tray and instrument (with capacity options,
> footprint, sourcing):
> [`../requirements/01-task-and-objects.md`](../requirements/01-task-and-objects.md),
> "Object 3 — HPLC autosampler tray".

## What is **not** the autosampler's job?

Two gaps that the autosampler doesn't fill, even on the fanciest
HPLC:

1. **Sample preparation.** Getting raw material into the vial
   (weigh, dissolve, dilute, filter) is still a separate step.
2. **Loading the tray.** A human (or our robot) puts the vials
   into the tray. The autosampler doesn't do this.

These two gaps are where lab automation lives. Our project
attacks **gap #2** — see
[`03-manual-steps-today.md`](03-manual-steps-today.md) for what
"loading the tray" actually looks like.

## Where labs use HPLC (specific places, not generic)

HPLC sits on a bench in roughly five kinds of working labs:

| Lab type                              | What they test                                                                | Why HPLC and not something else              |
|---------------------------------------|-------------------------------------------------------------------------------|----------------------------------------------|
| **Pharmaceutical QC** (Pfizer, Merck, GSK, generics manufacturers) | Every finished drug batch: amount of active ingredient, impurities, breakdown products | Regulators (FDA, EMA) require it; standard method for almost all small-molecule drugs |
| **Clinical / hospital labs**          | Drug levels in patient blood (e.g. anti-epileptics, immunosuppressants), vitamin D, hormones | Trace amounts in a complex matrix (blood, plasma) need HPLC's separation power |
| **Food & beverage QC**                | Vitamins in cereals, caffeine in soft drinks, mycotoxins in nuts/grains, preservatives, sugars | Many food compounds aren't volatile, so gas chromatography won't do — HPLC is the default |
| **Environmental labs**                | Pesticides and herbicides in groundwater, antibiotics in surface water        | Regulations (EPA in the US, EU Water Framework Directive) require trace-level detection |
| **Forensic / anti-doping** (WADA-accredited labs, police toxicology) | Drugs of abuse in urine / blood, performance-enhancing drugs in athletes      | Court-admissible identification needs HPLC-MS confirmation |
| **Cannabis / hemp testing** (US & Canada licensed labs) | Cannabinoid potency (THC, CBD), pesticide residues, mycotoxins              | State regulations require certified HPLC results before product can be sold |
| **Academic chemistry / R&D**          | New molecules from synthesis labs, biology research samples                   | Method development, not high-volume QC                 |

The first four categories are where the vials-per-day number is
high. Academic labs use HPLC too but at much lower throughput.

## How often labs actually run HPLC

These numbers come from public lab-equipment surveys and from how
the analytical-instruments industry sizes itself.

| Setting                                                  | Vials per day per HPLC | Typical fleet per site |
|----------------------------------------------------------|------------------------|------------------------|
| Big pharma QC site (single drug factory)                 | **200–500**            | **5–20** HPLCs         |
| Contract testing lab (food / environmental / cannabis)   | **100–300**            | 2–10 HPLCs             |
| Hospital clinical lab                                    | **50–200**             | 1–3 HPLCs              |
| Forensic / anti-doping lab                               | **50–150**             | 2–8 HPLCs              |
| Academic / R&D lab                                       | **5–30**               | 1 HPLC                 |

A typical pharma QC HPLC runs **roughly 24 hours a day, 5 days a
week**: trays load in the morning, the instrument runs through
the night, and the next tray is queued the next morning. The
loading step blocks how many trays a human can prep per shift —
that is the number the robot moves.

## Why we cover all of this here

For the robot, the *outside* of every vial is the same: 12 × 32 mm
glass cylinder, ~10 g, slippery. The motion is identical no matter
what is inside.

But three of the project's hardest decisions only make sense once
you know what is **inside** the vial:

- **Why 100 vials per tray and not 1?** Because one HPLC run is
  almost always a *batch* of related samples — see [Why many vials
  per tray](#why-we-put-many-vials-in-one-tray) below.
- **Why barcodes and not just slot order?** Because the *order*
  inside the tray is set by the lab's run schedule, not by the
  order the technician picked vials off the bench — see
  [How vials are identified](#how-vials-are-identified).
- **Why "no breakage" and not "low breakage"?** Because the
  liquid inside is sometimes irreplaceable — see [What is
  actually in the vial](#what-is-actually-in-the-vial).

The next four sections answer each of those plainly.

## What is actually in the vial

A 2 mL HPLC vial is **not full**. It holds **1.0–1.5 mL of
prepared liquid**, leaving a small air gap (the "headspace") so
the autosampler needle can dip in cleanly.

The liquid is almost always:

1. **The substance of interest, dissolved in a solvent.** The
   substance is the thing the HPLC will measure; the solvent is
   whatever the substance dissolves cleanly in (water, methanol,
   acetonitrile, or a buffer — these four cover most cases).
2. **Filtered.** Pushed through a 0.22 µm or 0.45 µm syringe
   filter to remove particles, otherwise the HPLC column clogs.
3. **At a known concentration**, typically 0.01–10 mg of substance
   per mL of solvent. Outside that range the detector either
   sees nothing or saturates.

That is it. No solids, no gels, no foam. Always a clean liquid.

Why a thin glass tube and not plastic: HPLC solvents like
acetonitrile dissolve some plastics, so glass is the safe default.
The cap is plastic (polypropylene) but it never touches the column.

## What real samples look like

Three concrete examples — these are the kinds of samples that
will sit in our reference 100-vial tray:

| Sample type                  | What is dissolved          | In what solvent              | Use case                                            |
|------------------------------|----------------------------|------------------------------|-----------------------------------------------------|
| **Crushed paracetamol tablet** | ~0.5 mg/mL paracetamol     | 50 % water + 50 % methanol   | Pharma QC: confirm each batch has the right dose    |
| **Patient plasma (drug monitoring)** | A few µg/mL of a drug like carbamazepine | Acetonitrile (after crashing the blood proteins out) | Clinical: adjust epilepsy patient's dose            |
| **Groundwater + pesticide extract** | A few ng/mL of atrazine    | Methanol (after SPE concentration) | Environmental: check drinking-water source         |
| **Cola, degassed and diluted** | ~100 µg/mL caffeine        | Water                        | Food QC: confirm caffeine content on the label      |
| **Calibration standard**     | Pure substance at known concentration | Same solvent as the samples  | Every run includes 3–7 of these to calibrate the detector |

**Why "no breakage" is not negotiable:** the patient-plasma vial
above is a single millilitre of one patient's blood. If the robot
breaks it, the lab has to call the patient back. The tablet vial
can be re-prepared in minutes; the plasma cannot. The robot has
to treat *every* vial as irreplaceable.

## Why we put many vials in one tray

The autosampler runs **one method** (one set of column, solvent,
detector settings) for the whole tray. Within that method, every
vial is a different *sample* in a structured run schedule.

A typical 100-vial QC tray is laid out like this:

| Slots          | Vial contents                  | Why it is there                                   |
|----------------|--------------------------------|---------------------------------------------------|
| 1              | **Blank** (solvent only)       | Check the column is clean                          |
| 2 – 6          | **Calibration standards** at 5 known concentrations (e.g. 1, 5, 10, 50, 100 µg/mL of the target) | Build a calibration curve so peak area → concentration |
| 7 – 8          | **System suitability check**   | Confirm the column and detector are healthy        |
| 9 – 10         | **Quality control samples** (known concentration, blind to the run) | Statistical check that the method is working      |
| 11 – 98        | **Real unknown samples** (the patient bloods, the tablet batches, the water samples) | The actual reason the run exists                   |
| 99 – 100       | **Repeat QC + blank**          | Confirm nothing drifted during the run             |

So the answer to "why many vials at once" is:

- The HPLC method takes **15–30 minutes per sample**. A 100-vial
  tray fills the instrument for **~25–50 hours of unattended
  run time** (it can run nights and weekends — see
  [`../requirements/03-success-precision-speed.md`](../requirements/03-success-precision-speed.md)).
- A single unknown sample is **useless on its own** — you need the
  blank, the standards, and the QC samples around it to know the
  measurement is real.
- Loading 100 at once is what lets one technician serve one HPLC
  for a whole day without going back to the instrument every
  20 minutes.

The robot doesn't care about the chemistry. It cares that the
*order* in the tray is fixed by the LIMS — "calibration standard
#3 must be in slot 5", "patient blood ID 472 must be in slot 27" —
and a wrong slot invalidates the whole run.

## How vials are prepared (and where they come from)

The short answer: **the lab prepares them, the same day, on the
same bench as the HPLC.** Vials do not arrive pre-made.

Why not pre-made:

- Most samples are time-sensitive. A blood plasma extract degrades
  in hours. A tablet dissolved in solvent can hydrolyse overnight.
- Every sample uses a slightly different preparation method
  (different solvent ratios, different filter sizes, different
  dilution). Outsourcing the prep would mean outsourcing the
  whole assay.

The one exception is **reference materials** (e.g. NIST-certified
standards of pure substances, or commercial drug-substance
reference standards). Those arrive in factory-sealed vials and
the technician dilutes them into the working calibration vials —
but the *sample* vials that ride in our robot's tray are always
lab-made.

### How the technician makes one vial

Each sample goes through a subset of these steps. The full list
with use cases lives in
[`03-manual-steps-today.md`](03-manual-steps-today.md); the
high-level recipe is:

1. **Weigh** the raw material on an analytical balance (e.g.
   crushed tablet powder, ±0.1 mg).
2. **Dissolve** it in a measured volume of solvent (water,
   methanol, acetonitrile, buffer).
3. **Mix** with a vortex or sonicate to make sure it is fully
   in solution.
4. **Dilute** an aliquot into more solvent so the concentration
   lands in the detector's working range.
5. **Filter** through a 0.22 µm or 0.45 µm syringe filter to
   remove particles.
6. **(Optional) extract** with **solid-phase extraction (SPE)**
   for messy matrices (blood, food, soil) — this concentrates the
   target compound and removes interferents.
7. **Transfer** the final clean liquid into a 2 mL HPLC vial,
   leaving a small headspace.
8. **Cap** the vial — screw cap (twist) or crimp cap (special
   tool).
9. **Label** the vial — barcode sticker or hand-written ID.

### Which steps actually run for which sample

The recipe is not the same for every vial. Real use cases:

| Sample                        | Steps actually run                                    |
|-------------------------------|-------------------------------------------------------|
| **Tablet QC** (paracetamol)   | Weigh → dissolve → dilute → filter → transfer → cap → label |
| **Plasma drug monitoring**    | Aliquot plasma → crash proteins with acetonitrile → centrifuge → filter → transfer → cap → label |
| **Water pesticide screen**    | SPE concentration → elute → filter → transfer → cap → label |
| **Cola caffeine**             | Degas → dilute → filter → transfer → cap → label      |
| **Calibration standard**      | Dilute pure substance → transfer → cap → label        |

For our project, **all of the above happens before the robot
sees anything**. By the time the vials hit the inbound rack, they
are filled, capped, and labelled. The robot's job starts at the
rack.

## How vials are identified

Once 100 vials sit in a rack, they look identical. The lab has
three ways to tell them apart, in roughly decreasing order of how
common each is in a professional QC lab:

| Method                              | What it looks like                                    | Where it is used                                  | Trustworthy?                          |
|-------------------------------------|-------------------------------------------------------|---------------------------------------------------|---------------------------------------|
| **Printed 1D barcode** (Code 128)   | White sticker with vertical bars and a 6–12 digit ID  | Almost every regulated lab — pharma QC, clinical, anti-doping | Yes — the LIMS knows what each ID means |
| **Printed 2D barcode** (Data Matrix or QR)  | Small square sticker, ~5 × 5 mm                  | Newer / high-throughput labs — fits on the vial cap | Yes — same as 1D, more capacity        |
| **Hand-written number on the cap**  | Sharpie marker, "S-47" or "B12"                       | Small labs, R&D, teaching labs                    | Risky — fades, smudges, no automatic audit trail |
| **Slot position alone** (no label)  | Vial in tray slot N "is" sample N                     | Only when one technician loads, runs, and analyses one tray in one sitting | Fragile — one wrong placement breaks the whole run |

**Why our project assumes barcodes (1D Code 128 on a side
sticker):**

- Every regulated lab the robot is intended for already uses
  barcodes — the lab does not need to change its workflow.
- A USB-HID barcode reader is **cheap (~$50–$200)** and treats
  the scanned ID like keyboard input — trivial to integrate.
- A barcode-in-the-loop loading step **physically prevents** the
  most common manual mistake: putting the right vial in the
  wrong slot. The robot reads the barcode, asks the LIMS where
  this vial goes, and places it there — there is no "looking
  away while reaching" failure mode.
- The barcode also closes the audit trail required by 21 CFR
  Part 11 (see
  [`../requirements/06-additional-considerations.md`](../requirements/06-additional-considerations.md)):
  "this barcode was placed in this slot at this time by this
  operator".

The robot **does not** decode 2D barcodes in v1 — 1D Code 128 is
the lowest common denominator across the target labs. 2D support
can be added later by swapping the reader; the rest of the
software pipeline is unchanged.

## Sources

- [HPLC Autosamplers: Perspectives, Principles, and Practices — LCGC](https://www.chromatographyonline.com/view/hplc-autosamplers-perspectives-principles-and-practices)
- [HPLC Sample Prep in 4 Steps — Lab Manager](https://www.labmanager.com/hplc-sample-prep-in-4-steps-2214)
- [Sample Preparation for HPLC Analysis — Drawell](https://www.drawellanalytical.com/sample-preparation-for-hplc-analysis-step-guides-and-common-techniques/)
- [Therapeutic Drug Monitoring by HPLC — overview, NCBI Bookshelf](https://www.ncbi.nlm.nih.gov/books/NBK551519/)
- [HPLC in Pharmaceutical Quality Control — overview, Sciencedirect](https://www.sciencedirect.com/topics/chemistry/high-performance-liquid-chromatography)
- [21 CFR Part 11 audit-trail requirements — Molecular Devices](https://www.moleculardevices.com/lab-notes/microplate-readers/fda-21-cfr-part-11-and-importance-of-regulatory-compliance-in-gmp-glp-labs)
- [Code 128 barcode standard — Wikipedia overview](https://en.wikipedia.org/wiki/Code_128)

## What's next

→ Next: [`03-manual-steps-today.md`](03-manual-steps-today.md) —
the steps a human still does by hand, in much more detail than
the recipe above.
