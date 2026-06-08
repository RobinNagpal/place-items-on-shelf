# Paracetamol — Step 1 (Weighing) solution

> **In one line:** for the easy case (a clean, dry powder), a small
> SCARA-style robot arm carries vials and weighing boats in and out of a
> commercial **dosing balance**. The dosing balance does the precise
> powder dispensing; the arm just handles labware.

This folder is the solution for the **paracetamol** case of
**Step 1 — Weighing** in the eight-step workflow at
[robotics-research / 03-hplc-workflow / 01-weighing.md](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md).
If you have not read that file, read it first — this folder assumes
you know what the step is supposed to produce.

## What we are automating, in one paragraph

A lab technician needs to weigh out about **5 milligrams** (5 mg) of
ground paracetamol powder onto a weighing boat or directly into a
small glass flask, with the answer accurate to **a tenth of a
milligram**. The technician would do this by hand, scoop by scoop,
inside an analytical balance's glass draft shield. Our solution lets a
robot do it instead, so the same job can run for **five products in a
row** (the tested brand plus four competitors) without a human
standing over each weighing.

## Why this case is the "easy" one

Compared to ketchup, paracetamol is the friendly sample:

- **Dry, free-flowing powder.** Nothing sticks. Gravity does the work.
- **Small target weight.** ~5 mg — well inside the range of every
  commercial powder doser.
- **The full off-the-shelf answer already exists.** A Mettler Toledo
  **Quantos** module clipped onto an XPR analytical balance dispenses
  powders down to 0.1 mg by itself. The robot arm has nothing fine to
  do — it just carries empty containers in and the filled ones out.
- **Static is the only annoyance.** The Quantos head solves this with a
  built-in ionising bar (small high-voltage wires that neutralise the
  static charge on the powder).

That is why we do **not** need a $30k industrial 6-axis arm here. A
small SCARA arm with millimetre-level repeatability is more than
enough.

## The three files in this folder

Read them in order. Each one is short.

1. **[`01-existing-solutions.md`](01-existing-solutions.md)** — how
   real labs (Mettler, Chemspeed, Hamilton, PAL) automate the weighing
   step today, and which parts of those solutions we copy.
2. **[`02-hardware-choice.md`](02-hardware-choice.md)** — which robot
   arm we recommend, which dosing balance it talks to, why we picked
   them, and what the alternatives are.
3. **[`03-simulation-workflow.md`](03-simulation-workflow.md)** — the
   exact ROS 2 / MoveIt 2 / Gazebo plan: which packages, which nodes,
   which topics, and the step-by-step motion the arm performs in
   simulation.

## The headline picks (so you do not have to read further)

| What | We picked | Why |
|---|---|---|
| **Dosing instrument** | Mettler Toledo XPR226 analytical balance + **Quantos QB1** powder-dosing module with QH-series powder heads | Industry standard. ±0.1 mg accuracy at 5 mg. RFID-tagged dosing heads. Closed-loop on balance reading. |
| **Robot arm (production)** | **Epson G6-553S SCARA** (550 mm reach, ±0.015 mm repeatability) | Right geometry for a flat 40 cm bench cell. Repeatability beats any cobot. Fast and cheap (~$15k). |
| **Robot arm (simulation + project)** | **Universal Robots UR3e** (500 mm reach, ±0.03 mm) | Same job, slightly worse precision, but its ROS 2 driver, MoveIt 2 config, and Gazebo SDF are first-party and beginner-friendly. The Quantos sets the mass, so the arm precision loss does not matter. |
| **Gripper** | UR's **2F-85** Robotiq parallel jaw, soft silicone pads | Holds a 100 mL volumetric flask and a 2 mL HPLC vial. Soft pads protect glass. |
| **Sensors** | Wrist-mounted RGB-D camera + draft-shield door switch | Camera reads the vial barcode and confirms the flask is on the pan. Door switch confirms the draft shield is open before the arm enters. |

Full reasoning — including what we considered and rejected — is in
[`02-hardware-choice.md`](02-hardware-choice.md).

## What this does **not** cover (and why)

- **Sample homogenisation** — grinding 20 tablets into a fine powder.
  That is a kitchen-blender-style pre-step the tech still does by
  hand. Out of scope for v1.
- **The next seven workflow steps** (dissolution onward). Each gets its
  own folder when we implement it.
- **Real hardware bring-up.** This folder is sim-only for now. Layer 4
  (integration on real hardware) follows the same workflow but adds
  real-world calibration, safety, and LIMS hooks — see
  [`../../../04-integration-and-bring-up/`](../../../04-integration-and-bring-up/).
