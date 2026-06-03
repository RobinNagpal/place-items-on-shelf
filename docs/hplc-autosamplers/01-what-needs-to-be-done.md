# 01 — What Needs To Be Done (in one page)

> **Read this first.** If you read only one file in this folder, this
> is the one. It tells you, in plain English, what the project is.

## The task, in one sentence

> Build a robot arm that **picks small glass sample vials from a
> rack, reads the barcode on each, and places each one in the right
> slot of an HPLC autosampler tray** — accurately, repeatably, and
> with a full audit log of which vial went where.

## In one short paragraph

A chemistry lab runs an HPLC instrument that automatically tests one
liquid sample at a time. The instrument is fed a tray of small glass
vials. Today, a human technician spends hours every day loading those
vials by hand, one at a time, in a specific order, while writing down
which sample went where. **That hand-loading step is what our robot
takes over.** The robot does not prepare the samples, does not cap
the vials, and does not run the HPLC itself — just the loading.

## What is in scope (the first version of the project)

The robot must:

1. **See** an inbound rack of ready vials on a lab bench.
2. **Pick** a vial from the rack without dropping or cracking it.
3. **Move** it past a barcode reader to read its label.
4. **Look up** which tray slot this vial belongs in (in a list /
   database / LIMS).
5. **Place** it upright in the correct slot of the autosampler tray.
6. **Log** the barcode-to-slot mapping.
7. **Repeat** until the rack is empty or the tray is full.

## What is out of scope (for now)

Out of scope keeps the project small enough to actually finish:

- **Sample preparation** (weighing, dissolving, diluting, filtering).
  Vials arrive ready and full.
- **Capping or crimping vials.** Caps are already on.
- **Microlitre pipetting** of liquids.
- **Operating the HPLC itself.** Vendor software still runs the run.
- **Disposing of vials after the run.** Technician removes the tray.
- **Multi-tray / 24-hour unattended operation.** v1 is one tray at
  a time, with a human in the room.

These can all be added later, but each adds new hardware
(a liquid handler, a crimper tool, a tray shuttle). v1 is just the
arm and one gripper.

## Why this is worth doing

Three plain reasons:

1. **It saves people from boring work.** A QC lab loads hundreds of
   vials a day. The act of loading them is mechanical and repetitive.
2. **It removes a common source of error.** Human-loaded trays have
   real mistake rates — wrong vial in wrong slot — and one mistake
   can invalidate a long HPLC run.
3. **It produces a clean audit trail.** In regulated labs (pharma,
   clinical) you must prove, after the fact, which vial went where
   and who placed it. A robot does this automatically; a human
   notebook is much harder to defend.

Full reasoning, with numbers, lives in
[`04-why-automate-tray-loading.md`](04-why-automate-tray-loading.md).

## Why the HPLC autosampler in particular?

The HPLC is one of the most common lab instruments on Earth. Almost
every drug batch made anywhere is tested with HPLC before it ships.
Most major brands (Agilent, Waters, Shimadzu, Thermo Fisher) use the
**same standard 12 × 32 mm vial**, and most autosamplers use **the
same kind of tray** — usually with 96 slots in a grid.

That standardisation makes the task **portable**: a robot that
loads one brand's tray can usually load another's with very small
changes. Few other lab tasks are that universal.

> Sources: see [`02-what-is-hplc-and-an-autosampler.md`](02-what-is-hplc-and-an-autosampler.md)
> for full background and citations.

## What this project will look like, end-to-end

A picture of the finished v1, in words:

- A small 6-axis collaborative arm (e.g. **myCobot 280 Pi**) sits on
  a lab bench, bolted to a base plate.
- To the **left** of the arm: an inbound rack with up to 24–48 ready
  vials, capped, with barcode labels.
- To the **right** of the arm: an HPLC autosampler with its drawer
  open and a standard tray sitting in it.
- **Between them**: a fixed-position barcode reader.
- A **camera mounted overhead** (or on the wrist) sees the rack and
  the tray.
- A small **PC** runs the perception, motion planning, and the LIMS
  link.
- A **technician** is in the room. The cell has a clear "Start" and
  "Stop" button and visible status lights.

## What's next

Read on in order — the next file is background on what HPLC is and
why labs use it.

→ Next: [`02-what-is-hplc-and-an-autosampler.md`](02-what-is-hplc-and-an-autosampler.md)
