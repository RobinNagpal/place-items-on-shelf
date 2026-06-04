# 02 — What Is HPLC, And What Is An Autosampler?

> **Who this is for:** Anyone who has never seen an HPLC. This doc
> stays short on the chemistry — we only need enough to know what
> the robot is feeding and why standards matter.

## HPLC in one line

**HPLC** = **High-Performance Liquid Chromatography**. A machine
that takes a small volume of liquid sample and tells you what
chemicals are in it. Used everywhere — pharma QC, food, water,
clinical, R&D — and one of the most common analytical instruments
in the world.

We don't need to understand the chemistry. We only need to know:

- It is **automatic** for the testing part — once samples are
  loaded, it runs by itself, often overnight.
- It eats samples from a **tray of small glass vials**.

Everything below is just about the tray and the vials, because
that is what the robot touches.

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

## What's next

→ Next: [`03-manual-steps-today.md`](03-manual-steps-today.md) —
the steps a human still does by hand.
