# Paracetamol — full 8-step automated cell

> **In one line:** a single Universal Robots UR5e cobot with a
> Robotiq Hand-E gripper carries labware between **stationary
> stations** (analytical balance with Mettler Quantos doser,
> sonicator, pipette, syringe-filter clamp, capper, labeler,
> autosampler tray) and runs the entire eight-step HPLC sample-prep
> workflow on a paracetamol tablet sample.

This folder is the solution for the **paracetamol** case of the
eight-step workflow at
[robotics-research / 03-hplc-workflow](https://github.com/RobinNagpal/robotics-research/tree/main/03-hplc-autosampler/03-hplc-workflow).
Read those eight files first — the simulation plan in this folder
reproduces them one for one.

## Why this is the "easy" case

Paracetamol is a clean tablet:

- **Dry, free-flowing powder.** Gravity does the dispensing work.
  A Mettler Quantos QB1 reaches ±0.1 mg at the 5 mg target on its own
  — no special arm skill needed.
- **Dissolves cleanly in methanol.** Step 2 produces a clear liquid
  with nothing to filter out separately.
- **No centrifuge needed.** Step 4 is a single push through a
  0.45 µm syringe filter.
- **Small vial count.** A typical paracetamol assay run is ~8 vials
  (4 brands + reference + blank + 2 standards). Bookkeeping risk is
  low.

That is what makes this the **first** case worth automating — the
fewest things go wrong, so the cell can be brought up step by step.

## The three files in this folder

1. **[`01-existing-solutions.md`](01-existing-solutions.md)** — a
   one-screen summary of how commercial systems handle weighing
   today, and which pattern we copy.
2. **[`02-hardware-choice.md`](02-hardware-choice.md)** — the
   **main reasoning** file. Walks all eight workflow steps from the
   gripper's point of view, picks the arm (UR5e), picks the gripper
   (Hand-E), picks the Step-1 dispenser (Mettler Quantos QB1), and
   names two rejected competitors for each pick.
3. **[`03-simulation-workflow.md`](03-simulation-workflow.md)** —
   **(Part 1)** what the arm physically does at every step, in the
   same plain English the upstream workflow uses. **(Part 2)** how
   that maps to ROS 2 + Gazebo + MoveIt 2 calls.

## Headline picks

| | Pick | Why |
|---|---|---|
| **Arm** | Universal Robots UR5e | 5 kg payload, wrist FT, 850 mm reach, first-party ROS 2 / Gazebo / MoveIt 2. See [`02-hardware-choice.md`](02-hardware-choice.md) for the FR3 and Kinova Gen3 rejections. |
| **Gripper** | Robotiq Hand-E | 50 mm stroke spans 10 mm cap → 50 mm flask. Force-controlled. ROS 2 driver. Soft pads for glass. |
| **Step 1 dispenser** | Mettler XPR226 + Quantos QB1 powder doser | Industry standard. ±0.1 mg at 5 mg. RFID-tagged dosing heads. |
| **Stations** | Sonicator, pipette holster, syringe-filter clamp, cap dispenser, label printer + wrapper, autosampler tray | All stationary — the arm shuttles labware between them. |

The arm and gripper picks are **the same** in the ketchup case (see
[`../ketchup/`](../ketchup/)) — the all-8-steps analysis converges on
the same answer. The two cases differ only in the **Step 1 dispenser**
(Quantos QB1 powder for paracetamol; Watson-Marlow 323Dud peristaltic
for ketchup) and in a few intermediate stations (a centrifuge replaces
the sonicator for ketchup's Step 4 clarification).

## What this does **not** cover (and why)

- **Sample homogenisation.** Grinding 20 tablets into a fine powder
  is still a manual pre-step. Out of scope for v1.
- **Real hardware bring-up.** This folder is sim-only for now.
- **Other workflow variations.** v1 is the standard tablet assay.
  Crimp caps, amber vials, and partial racks are deferred to v2.
