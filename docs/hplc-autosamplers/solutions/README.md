# Solutions — automating the HPLC sample-prep workflow

The wider [`hplc-autosamplers/`](..) folder explains **what** the
project automates and **why**. This folder is the **how**: a
concrete, per-case solution for each step of the eight-step
sample-prep workflow at
[robotics-research / 03-hplc-workflow](https://github.com/RobinNagpal/robotics-research/tree/main/03-hplc-autosampler/03-hplc-workflow).

## Two running cases

The upstream workflow walks every step through **two real examples**.
This folder mirrors that split — one subfolder per case:

- **[`paracetamol/`](paracetamol/)** — the **easy** case. Dry powder,
  a pharma-style tablet assay, ~5 mg target weight, well-supported
  by existing lab automation.
- **[`ketchup/`](ketchup/)** — the **hard** case. Sticky paste, a
  food-chemistry assay (5-HMF), ~5 g target weight, plus a centrifuge
  step to deal with pulp.

## The headline answer (after looking at all 8 steps from a gripper's point of view)

| | Picked | Same for both cases? |
|---|---|---|
| **Arm** | **Universal Robots UR5e** (6-DOF cobot, wrist FT, 850 mm reach, first-party ROS 2 / Gazebo / MoveIt 2) | **Yes — same.** |
| **Gripper** | **Robotiq Hand-E** (0–50 mm adaptive parallel jaw, soft pads, force-control, ROS 2 driver) | **Yes — same.** |
| **Tool changer** | Not needed. | **n/a — same.** |
| **Step 1 dispenser** | Mettler XPR226 + Quantos QB1 powder doser (paracetamol) ◇ Watson-Marlow 323Dud + Mettler XPR1203S balance (ketchup) | **No — case-specific.** |
| **Extra clarification station** | None (paracetamol dissolves clean) ◇ Eppendorf 5424 centrifuge (ketchup, before filtering) | **No — case-specific.** |

The big finding: **one arm and one gripper cover all eight workflow
steps for both cases.** The case-specific hardware sits in *stationary
stations* (the dispenser, the centrifuge), not in the gripper.

That convergence was not obvious at first. The full reasoning — the
step-by-step table of gripper requirements and the two-competitor
rejections — is in:

- [`paracetamol/02-hardware-choice.md`](paracetamol/02-hardware-choice.md)
- [`ketchup/02-hardware-choice.md`](ketchup/02-hardware-choice.md)

Both files share the arm + gripper analysis (repeated in each so that
opening one folder is enough), then diverge on the Step 1 dispenser.

## How each case folder is laid out

Every case folder follows the same three-file layout:

```
<case>/
├── README.md                  # overview + headline picks
├── 01-existing-solutions.md   # short summary of what labs do today
├── 02-hardware-choice.md      # all-8-steps analysis + arm + gripper + dispenser, with 2 rejections each
└── 03-simulation-workflow.md  # Part 1: physical workflow; Part 2: ROS 2 / Gazebo / MoveIt 2 implementation
```

`03-simulation-workflow.md` is intentionally split into two halves:

- **Part 1 — What we are trying to do.** The physical actions a
  human technician performs, in plain English, mapped row-by-row to
  the eight upstream workflow files. No code.
- **Part 2 — How we implement it with the arm.** The same actions in
  ROS 2 + Gazebo + MoveIt 2 calls. Every code action traces back to
  one Part-1 row.

Reading order: Part 1 first, **always**. If a code action does not
map back to a Part-1 row, the code is wrong.

## Writing style

Follows the upstream HPLC-workflow primer: very simple English, short
sentences, every special word explained the first time it is used.
A reader who has never written a line of robotics code or set foot in
a lab should be able to follow it end-to-end.

## Where this fits in the rest of the docs

- **[`../research/`](../research/)** — the "understand the problem"
  background. Read first if you are new to HPLC.
- **[`../requirements/`](../requirements/)** — the v1 spec for the
  *tray-loading* task (Step 8 of the eight-step workflow). This
  folder picks up at Step 1 instead.
- **[`../research/05-existing-solutions.md`](../research/05-existing-solutions.md)** —
  the survey of commercial products (PAL, HTA, Andrew+, etc.). Each
  case's `01-existing-solutions.md` is a one-screen pointer into that.
- **[`../../learning-checklist.md`](../../learning-checklist.md)** —
  the general curriculum. Cross-referenced where a checklist exercise
  is the closest existing implementation of a workflow step.
