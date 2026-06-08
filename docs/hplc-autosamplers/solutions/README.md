# Solutions — automating the HPLC sample-prep workflow

The wider [`hplc-autosamplers/`](..) folder explains **what** the project
automates and **why**. This folder is the **how**: a concrete, per-case
solution for each step of the eight-step sample-prep workflow described
upstream in
[robotics-research / 03-hplc-workflow](https://github.com/RobinNagpal/robotics-research/tree/main/03-hplc-autosampler/03-hplc-workflow).

## Two running cases

The upstream workflow walks every step through **two real examples**.
This folder mirrors that split — one subfolder per case, so that the
hardware and software answers can differ if they need to:

- **[`paracetamol/`](paracetamol/)** — the **easy** case. Dry powder, a
  pharma-style tablet assay, ~5 mg target weight, well-supported by
  existing lab automation.
- **[`ketchup/`](ketchup/)** — the **hard** case. Sticky, viscous paste,
  a food-chemistry assay (5-HMF), ~5 g target weight, almost no
  off-the-shelf automation answer.

The two cases use **different robot arms** on purpose. See the picks
and the reasoning in
[`paracetamol/02-hardware-choice.md`](paracetamol/02-hardware-choice.md)
and [`ketchup/02-hardware-choice.md`](ketchup/02-hardware-choice.md).

## What is covered so far

Only **Step 1 — Weighing** for both cases. Weighing is the first and
arguably the hardest step in the workflow (see the upstream
[01-weighing.md](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md)).
Later steps (dissolution, dilution, filtering, transfer-to-vial, capping,
labeling, autosampler placement) will get their own files in this folder
as the project moves through them.

## How each case folder is laid out

Every case folder follows the same three-file layout, so they are easy
to compare side by side:

```
<case>/
├── README.md                  # high-level overview of the case
├── 01-existing-solutions.md   # how labs do this today (and why off-the-shelf is not enough)
├── 02-hardware-choice.md      # which robot arm + which dosing instrument + why
└── 03-simulation-workflow.md  # how to simulate it in ROS 2 + Gazebo + MoveIt 2
```

Writing style follows the upstream convention: very simple English,
short sentences, every special word explained the first time it is
used. A reader who has never written a line of robotics code or set
foot in a lab should be able to follow it end-to-end.

## Where this fits in the rest of the docs

- **[`../research/`](../research/)** — the "understand the problem"
  background. Read first if you are new to HPLC.
- **[`../requirements/`](../requirements/)** — the v1 spec for the
  *tray-loading* task (Step 8 of the eight-step workflow). This folder
  picks up at Step 1 instead.
- **[`../research/05-existing-solutions.md`](../research/05-existing-solutions.md)** —
  the survey of commercial products (PAL, HTA, Andrew+, etc.).
  The `01-existing-solutions.md` in each case folder narrows that
  survey to **weighing automation** specifically.
- **[`../../learning-checklist.md`](../../learning-checklist.md)** —
  the general curriculum. Cross-referenced where a checklist exercise
  is the closest existing implementation of a workflow step.
