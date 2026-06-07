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

The sections below answer each of those plainly, plus several
related questions about how the machine is configured and what
ends up sharing the tray in real labs.

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
| 11 – 98        | **Real unknown samples** — all of one kind from many sources (e.g. dissolved tablets from many batches of one product, **OR** patient bloods from many patients in one study, **OR** water samples from many sites on one method). Bracketing standards are interleaved every ~12 vials (see note below). | The actual reason the run exists |
| 99 – 100       | **Repeat QC + blank**          | Confirm nothing drifted during the run             |

> **The "11 – 98 unknowns" block is not 88 unbroken samples.**
> Pharma SOPs and the FDA M10 bioanalytical guidance require a
> **bracketing standard injected after at most 12 sample vials**,
> plus a final standard + QC at the end of the sequence. So a
> realistic 100-vial tray ends up holding **~80 real unknowns +
> ~20 calibrator / QC / bracketing vials** interleaved. The exact
> bracketing positions live in each lab's SOP. The point for our
> purposes is that the "unknowns" block is **one type of sample**
> from many sources — never a mix of three different tests.

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

## Can different tests share one tray?

**No, not in general.** One HPLC tray = one HPLC method = one
column, one mobile phase, one detector wavelength, one runtime.
The autosampler runs every vial through that method without
changing anything in between.

Three rules of thumb fall out of that:

1. **Different tests need different trays / different runs.** If
   a lab has samples to test for one chemical and other samples
   to test for a different chemical, those become two separate
   runs — often with a column swap in between.
2. **"Different" here means different chemistry, not different
   source.** The same test on samples from different sources
   (different patients, different production batches, different
   sites) shares one tray fine. That is the *normal* case.
3. **Multi-method sequences are technically possible but rare in
   practice.** Most HPLC control software (Agilent OpenLab, Waters
   Empower, Shimadzu LabSolutions) lets the technician chain
   methods inside one sequence file ("method A on vials 1 – 10,
   method B on vials 11 – 20"). It only works when both methods
   use the **same column** — otherwise the technician has to
   physically swap the column between blocks, which turns it
   back into two runs.

The robot does not decide which of these the run is. Whatever the
LIMS says — "one tray for product A, then one tray for product
B" — the robot just loads each tray in turn.

## How a technician sets up the HPLC machine

Before the autosampler ever sees a vial, the technician chooses
an **HPLC method**. A method is the full instrument recipe. The
lab already knows three things and the method depends on all
three:

| What the lab already knows                                     | What it tells the technician                                                                                       |
|----------------------------------------------------------------|--------------------------------------------------------------------------------------------------------------------|
| **Analyte** — the chemical to measure                          | Which detector wavelength to use, which column chemistry separates the analyte cleanly, what concentration range to calibrate over |
| **Matrix** — the liquid the analyte is dissolved in (water, plasma, urine, dissolved tablet, fruit juice…) | Whether sample prep is needed (filtration, extraction, protein crash), what mobile-phase gradient avoids interferences from other matrix components |
| **Validated method**                                           | The exact column part number, mobile-phase composition (e.g. 30 % acetonitrile : 70 % water with 0.1 % formic acid), flow rate (typically 0.5 – 1.5 mL/min), runtime per vial (15 – 30 min), injection volume (5 – 20 µL) |

Once the method is loaded, the technician sets up the run **once**
for the whole tray. The autosampler will not change any of those
settings vial-to-vial.

### What changes when the matrix changes

The same analyte in two different matrices is **not** the same
HPLC method. Concrete example: the lab needs to measure the same
chemical (call it compound X) in two things —

- **A dissolved tablet solution** (matrix = water + methanol
  containing dissolved excipients like sugar, starch, magnesium
  stearate).
- **Groundwater** (matrix = water with trace minerals, dissolved
  organic matter, possibly other pesticides).

These usually need **different methods**, because:

| What changes              | Why                                                                                                                                  |
|---------------------------|--------------------------------------------------------------------------------------------------------------------------------------|
| **Sample prep**           | Tablet → crush, dissolve, dilute, filter. Groundwater → solid-phase extraction (SPE) to concentrate trace compound X from a litre of water down to a millilitre. Completely different workflows. |
| **Concentration range**   | Tablet contains milligrams of compound X per tablet. Groundwater contains nanograms per litre. The detector wavelength, signal range and integration thresholds are tuned for very different signal levels. |
| **Interfering peaks**     | Tablet excipients elute at different retention times than groundwater humic acids. The mobile-phase gradient has to separate compound X cleanly from whichever interferences are actually present.                |
| **Column choice**         | A C18 reverse-phase column may work for both, but column dimensions (length, particle size) and guard-column choice often differ to cope with each matrix's dirt level.                                   |

So **same analyte + different matrix = different method = different
tray** in practice. Methods can be re-developed to share more
settings between matrices, but that is a method-development project
on its own — not something the technician changes on the day.

### What does *not* change vial-to-vial

For a tray of samples that **share** analyte + matrix + method, the
technician sets the method once and the instrument runs every vial
identically. The autosampler injects the same volume from each
vial; the column sees the same gradient; the detector reads at the
same wavelength. **Only the answer (peak area → concentration)
changes per vial.**

This is exactly why one HPLC + one tray + one method scales so
well for batch QC and bioanalysis — see the next section.

## When you're verifying one batch — what fills the other slots?

Concrete pharma QC scenario: a factory has produced one batch of a
tablet (call it **batch L-2026-0407**) and the QC lab has to prove
the batch is correct before it can ship. A 100-vial tray is
overkill for one tablet — so what fills the rest of the slots?

There are three common QC questions, and each one fills the tray
differently.

### Pattern A — "Is the average dose right?" (assay)

Twenty tablets from the same batch are crushed together into one
fine composite powder. A weighed portion of that powder is
dissolved and tested in duplicate or triplicate.

| Slots  | Vial contents                                                                                                |
|--------|--------------------------------------------------------------------------------------------------------------|
| 1      | Blank (solvent)                                                                                              |
| 2 – 6  | 5 calibration standards (e.g. 50, 80, 100, 120, 150 % of the target dose)                                    |
| 7 – 8  | System suitability standards                                                                                 |
| 9 – 10 | QC samples                                                                                                   |
| 11 – 13 | **3 vials of the composite from batch L-2026-0407** (the batch under test)                                  |
| 14     | Bracketing standard                                                                                          |
| 15 – 17 | **3 vials of the composite from batch L-2026-0408** (the next batch shipping that week, same product)       |
| 18     | Bracketing standard                                                                                          |
| 19 – 21 | **3 vials of the composite from batch L-2026-0409**                                                          |
| …      | … each "block" is 3 vials of one batch + 1 bracketing standard                                               |
| 99     | Final QC                                                                                                     |
| 100    | Final blank                                                                                                  |

So the **majority of slots are different batches of the same
product**, with cal / QC / bracketing scaffolding around them. **The
batch you are verifying is just 2 – 3 vials**, sharing the tray with
20 – 30 other batches all needing the same release test.

### Pattern B — "Is every tablet within spec?" (content uniformity)

USP &lt;905&gt; requires testing **10 individual tablets** from one
batch, each prepared separately, to prove the active ingredient is
evenly distributed.

| Slots   | Vial contents                                                                                                |
|---------|--------------------------------------------------------------------------------------------------------------|
| 1       | Blank                                                                                                        |
| 2 – 6   | 5 calibration standards                                                                                      |
| 7 – 8   | System suitability                                                                                           |
| 9 – 10  | QC samples                                                                                                   |
| 11 – 20 | **10 vials, each one a single tablet from batch L-2026-0407**, crushed and dissolved individually            |
| 21      | Bracketing standard                                                                                          |
| 22 – 31 | **10 vials, 10 individual tablets from batch L-2026-0408**                                                   |
| 32      | Bracketing standard                                                                                          |
| 33 – 42 | **10 vials, 10 individual tablets from batch L-2026-0409**                                                   |
| …       | …                                                                                                            |
| 99      | Final QC                                                                                                     |
| 100     | Final blank                                                                                                  |

Here the **majority of slots are different individual tablets from
the same batch** — the test asks about variation *within* one
batch, not between batches.

### Pattern C — "Does it hold up over time?" (stability)

ICH stability testing puts the same batch into climate chambers
(25 °C / 60 % RH, 30 °C / 65 % RH, 40 °C / 75 % RH) and pulls
samples at 0, 1, 3, 6, 9, 12, 18, 24 months. One tray can hold
many timepoints at once.

| Slots   | Vial contents                                                                |
|---------|------------------------------------------------------------------------------|
| 11 – 13 | **Batch L-2026-0407, T = 0 (initial)**, 3 replicates                         |
| 14      | Bracketing standard                                                          |
| 15 – 17 | **Batch L-2026-0407, T = 1 month, 25 °C / 60 % RH**                          |
| 18 – 20 | **Batch L-2026-0407, T = 3 months, 25 °C / 60 % RH**                         |
| 21 – 23 | **Batch L-2026-0407, T = 6 months, 25 °C / 60 % RH**                         |
| 24      | Bracketing standard                                                          |
| 25 – 27 | **Batch L-2026-0407, T = 1 month, 40 °C / 75 % RH**                          |
| 28 – 30 | **Batch L-2026-0407, T = 3 months, 40 °C / 75 % RH**                         |
| …       | …                                                                            |

Here the **majority of slots are the same batch tested at different
storage conditions and times** — same product, same method, just a
matrix of time × temperature.

### Plain-English summary

> "Other vials in the tray" = the **scaffolding the regulators
> require** (blanks + calibrators + system suitability + QCs +
> bracketing standards) **+ a stack of related samples**.
>
> "Related" almost always means **same product + same method**,
> and then one of:
>
> - Different batches of that product (Pattern A — release).
> - Different individual tablets from one batch (Pattern B — uniformity).
> - The same batch under different storage conditions / times (Pattern C — stability).

The technician decides which pattern fills the tray based on which
question the run is answering. The LIMS records which slot holds
which sample. The HPLC just runs the method through every vial.

## How vials are prepared (and where they come from)

The short answer: **the lab prepares them, the same day, on the
same bench as the HPLC.** Vials do not arrive pre-made. Sample
prep is where most of a technician's time goes — and most of
where the chemistry-specific knowledge lives.

The one exception is **reference materials** (e.g. NIST-certified
pure-substance standards). Those arrive in factory-sealed
ampoules; the technician dilutes them into the working calibration
vials. But the *sample* vials that ride in the autosampler tray
are always lab-made.

A full walkthrough of every prep step, the equipment per step,
and worked recipes for each common sample type lives in its own
doc:

> See [`06-how-vials-are-prepared.md`](06-how-vials-are-prepared.md)
> for the equipment, the step-by-step recipe, and worked examples
> (dissolved tablet, plasma drug monitoring, groundwater pesticide,
> beverage caffeine, calibration standard).

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
- [FDA M10 — Bioanalytical Method Validation and Study Sample Analysis](https://www.fda.gov/media/162903/download) — the bracketing-standard / QC-acceptance rules that shape the 100-vial tray layout.
- [A Well-Written Analytical Procedure for Regulated HPLC Testing — LCGC International](https://www.chromatographyonline.com/view/a-well-written-analytical-procedure-for-regulated-hplc-testing)
- [Bracketing of Standards — PharmaGuideHub](https://pharmaguidehub.com/blog/2024/02/05/bracketing-of-standards/) — "no more than 12 samples between bracketing standards" rule.
- [HPLC Sample Preparation — Organomation](https://www.organomation.com/hplc-sample-preparation) — end-to-end overview of the prep steps detailed in [`06-how-vials-are-prepared.md`](06-how-vials-are-prepared.md).

## What's next

→ Next: [`03-manual-steps-today.md`](03-manual-steps-today.md) —
the steps a human still does by hand, in much more detail than
the recipe above.
