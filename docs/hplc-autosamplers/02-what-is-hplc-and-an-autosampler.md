# 02 — What Is HPLC, And What Is An Autosampler?

> **Who this is for:** Anyone who has never seen an HPLC. By the end
> of this doc you should know what the machine does, what it looks
> like, why labs care, and which part the robot interacts with.

## What is HPLC?

**HPLC** stands for **High-Performance Liquid Chromatography**.
Underneath the long name it is a simple idea:

> You have a small amount of a liquid mixture and you want to know
> what is in it.

The HPLC pushes that liquid through a long thin tube packed with
tiny solid particles (the **column**). Different chemicals in the
mixture stick to the particles by different amounts, so they come
out of the column at different times. A detector at the end measures
what is coming out, moment by moment. The result is a graph called
a **chromatogram**, with one peak per chemical.

From the timing and height of the peaks you can say things like:

- "Yes, the active drug ingredient is present, and it is at 99.4%
  purity."
- "There is 0.3 mg/L of pesticide X in this water sample."
- "This blood sample contains two of the three vitamins we tested
  for."

HPLC is one of the most-used analytical techniques in the world. It
is found in:

- **Pharmaceutical QC** — testing every batch of every drug.
- **Food and beverage** — vitamins, additives, contaminants.
- **Environmental** — water and soil analysis.
- **Clinical** — drug levels in patient samples.
- **Academic and R&D** — almost any chemistry research.

(The basics are well covered in the public DPAL HPLC methodology
manual and on most lab-supplier sites — see Sources at the bottom.)

## The parts of an HPLC, briefly

You don't need to know the inside in detail, but it helps to picture
the whole instrument:

1. **Solvent reservoirs** — bottles of the liquids that carry the
   sample through the column.
2. **Pump** — pushes those solvents at high pressure.
3. **Autosampler** — the part that picks one sample from the tray
   and injects it into the flow. **This is the part the robot
   interacts with.**
4. **Column** — the packed tube where separation happens.
5. **Detector** — measures what comes out (UV light, mass spec, etc).
6. **Computer / software** — collects the data and produces the
   chromatogram.

The whole thing sits on a single bench, about the size of a small
fridge for the modular brands.

## What is an autosampler?

The **autosampler** is a drawer-and-needle device at the front of
the HPLC. It does two jobs:

1. **Hold many samples at once**, in a tray.
2. **Move a tiny needle** from one vial to the next, sip a small
   volume from each, and inject it into the column.

A typical run looks like this from the outside:

- Technician loads a tray of, say, 96 vials.
- Slides the tray into the autosampler drawer.
- Closes the drawer.
- Tells the software the recipe ("inject 5 µL of vial 1, then 5 µL
  of vial 2, …").
- Presses **Start**.
- Goes home.
- Eight hours later, the run is done — 96 chromatograms saved.

While that is happening, **the operator does not need to be there**.
The instrument is fully automatic *for the running part*.

### The standard vial

Across almost every major HPLC brand — Agilent, Waters, Shimadzu,
Thermo Fisher — the autosampler uses **the same kind of vial**:

- A small clear glass cylinder.
- **Outer dimensions: 12 mm wide × 32 mm tall** (industry standard).
- **Nominal volume: 2 mL** (1.5 mL also common; 1 mL "low-volume"
  variants exist).
- **Material:** USP Type 1, Class A, 33 borosilicate glass.
- **Cap:** either a **screw cap** (9 mm or 10 mm thread, twisted on
  by hand) or a **crimp cap** (an aluminium seal squeezed on with a
  special tool — typically 11 mm).
- **Septum:** a thin rubber/PTFE disc inside the cap, pierced by the
  HPLC needle.

> The 12 × 32 mm vial is the **industry standard** because every
> autosampler is built around it. This is a happy fact for us — the
> robot only ever has to grip one shape.

### The standard tray

The tray sits inside the autosampler drawer and holds the vials in a
fixed grid of round holes. Common standard sizes across vendors:

- **96 positions** — by far the most common high-throughput layout
  (used in Shimadzu AOC-20, many Agilent / Waters trays, etc.).
- **40 positions** — common for mid-range modules.
- **15 positions** — common for short runs or precious samples.
- **100 positions** — Agilent offers a 100-slot variant.

For v1 of this project, **we target 96-position trays** because they
are the most common in QC labs and they make the cycle-time targets
most useful.

Slots in the tray are typically **a millimetre or two wider than the
vial**, so the vial drops in without sticking. That gives the robot
a placement tolerance on the order of ±1–2 mm — comfortable for a
small cobot.

## What is **not** the autosampler?

Two things the autosampler does **not** do:

1. **Prepare the sample.** It assumes you handed it ready-to-inject
   liquid in a vial. Getting raw material into that vial is *sample
   prep*, and it is still mostly manual today. (We cover this in
   [`03-manual-steps-today.md`](03-manual-steps-today.md).)
2. **Move trays in and out by itself.** The tray gets slid in by a
   human. (Some "carousel" autosamplers exist that hold multiple
   trays internally, but they are the minority.)

These two gaps — **prep** and **tray handling** — are exactly the
places where labs would like more automation. Our robot fits into
the **tray-handling** gap.

## Sources

- [Understanding 2 mL, 1.8 mL, or 1.5 mL Vial Sizes and Volumes — MTC HPLC Primer](https://www.mtc-usa.com/kb-article/aa-01800)
- [Standard autosampler vials (12 × 32 mm) — Sigma-Aldrich](https://www.sigmaaldrich.com/US/en/product/aldrich/z291706)
- [Autosampler Vials & Caps for HPLC & GC — Thermo Fisher](https://www.thermofisher.com/us/en/home/industrial/chromatography/chromatography-consumables/autosampler-vials-caps-hplc-gc.html)
- [Vial Trays and Drawers for HPLC Autosamplers — Agilent](https://www.agilent.com/en/product/liquid-chromatography/hplc-supplies-accessories/autosampler-fraction-collector-supplies-for-hplc/sample-trays-for-hplc)
- [Shimadzu AOC-20/20i/20s 96-position trays — Chromtech listing](https://chromtech.com/autosampler-trays-and-needle-seats/)
- [HPLC Autosamplers: Perspectives, Principles, and Practices — LCGC International](https://www.chromatographyonline.com/view/hplc-autosamplers-perspectives-principles-and-practices)
- [HPLC Methodology Manual — Distributed Pharmaceutical Analysis Laboratory (DPAL)](https://padproject.nd.edu/assets/385652/hplc_methodology_manual_2020.pdf)

## What's next

→ Next: [`03-manual-steps-today.md`](03-manual-steps-today.md) —
the steps a human still does by hand.
