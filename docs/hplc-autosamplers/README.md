# HPLC Autosamplers — Project Task Folder

This folder is the **project-specific task description** for our robot
arm. The wider [`docs/`](..) tree is the *general* learning curriculum
(layer 1 — finalize requirements, layer 2 — hardware). This folder is
the **first real task** we apply that curriculum to.

**Short version of the task:**

> Build a small robot arm that **loads sample vials into the tray of
> an HPLC autosampler**. The HPLC instrument is already automatic for
> injection. The boring, error-prone, manual part — getting vials into
> the tray in the right order — is what we automate.

## Structure

Three sibling subfolders, plus this README.

- **[`research/`](research/)** — The "understand the problem" stage:
  what the task is, what HPLC actually is, what is still manual today,
  why this particular step is worth automating, and which companies
  already work in the space. **Read this first.**
- **[`requirements/`](requirements/)** — The "what the robot must do"
  stage: concrete answers to the Layer-1 questions with specific
  reference products (vial, rack, tray) pinned. **Requirements are
  the starting point** for every hardware and software choice in
  Layer 2.
- **[`solutions/`](solutions/)** — The "how we actually build it"
  stage, broken out **per use case** (paracetamol and ketchup) and
  **per workflow step** (starting with Step 1 — weighing). Each case
  picks its own hardware (a different robot arm and a different
  dispenser) and lays out the ROS 2 / Gazebo / MoveIt 2 simulation
  plan.

## What's in research/

Six files, read in order:

1. [`01-what-needs-to-be-done.md`](research/01-what-needs-to-be-done.md) — the whole task in one page.
2. [`02-what-is-hplc-and-an-autosampler.md`](research/02-what-is-hplc-and-an-autosampler.md) — vial standard, tray standard, where labs use HPLC, what's in the vials, how the technician sets up the machine, what fills the other slots when you verify one batch, and why different tests can't share a tray.
3. [`03-manual-steps-today.md`](research/03-manual-steps-today.md) — sample prep, capping, tray loading, drawer. Includes the **rationale for loading on the bench** (not inside the instrument).
4. [`04-why-automate-tray-loading.md`](research/04-why-automate-tray-loading.md) — why this step in particular, vs. the rest of the workflow.
5. [`05-existing-solutions.md`](research/05-existing-solutions.md) — short, opinionated survey of the four commercial products closest to our problem (PAL RTC, HTA HT4000L, CTC HTS PAL, Andrew+) plus a couple of cobot demos and the one closest research paper.
6. [`06-how-vials-are-prepared.md`](research/06-how-vials-are-prepared.md) — deep-dive on vial preparation: every common step, the equipment per step, and five worked recipes (dissolved tablet, content uniformity, plasma drug monitoring, groundwater pesticide, beverage caffeine, calibration standard).

## What's in solutions/

One subfolder per case (matching the two running examples used in the
upstream [HPLC workflow primer](https://github.com/RobinNagpal/robotics-research/tree/main/03-hplc-autosampler/03-hplc-workflow)),
each with three short markdown files:

- **[`solutions/paracetamol/`](solutions/paracetamol/)** — the **easy**
  case (dry powder, ~5 mg target). UR5e + Robotiq Hand-E + Mettler
  Quantos QB1 powder doser.
- **[`solutions/ketchup/`](solutions/ketchup/)** — the **hard** case
  (sticky paste, ~5 g target). **Same UR5e + Hand-E**, plus a
  Watson-Marlow peristaltic pump and an Eppendorf centrifuge.

The all-eight-steps gripper analysis in each case folder converges on
the **same arm and the same gripper** for both cases — only the
Step 1 dispenser and the Step 4 clarification (centrifuge) differ.

Each folder follows the same three-file layout:

1. `README.md` — overview and headline picks.
2. `01-existing-solutions.md` — how labs do this step today.
3. `02-hardware-choice.md` — which robot + dispenser + balance + why.
4. `03-simulation-workflow.md` — ROS 2 + Gazebo + MoveIt 2 plan.

Start with [`solutions/README.md`](solutions/README.md) for the case
split and how the two folders relate.

## What's in requirements/

Seven short files plus a README:

- **[`requirements/00-spec-summary.md`](requirements/00-spec-summary.md)** —
  the **one-page task specification**. The actual Layer-1 deliverable
  — every other file in `requirements/` is the rationale and sources
  behind a number in this summary. **Read this first.** (Status: v1
  **finalized** 2026-06-05.)
- Files `01-` through `06-` — the long-form answers to each slice of
  the Layer-1 questions. See
  [`requirements/README.md`](requirements/README.md) for the order
  and the format.

## Where this fits in the rest of the docs

- **[`../01-finalize-requirements/`](../01-finalize-requirements/)** —
  General framework: how to write *any* robot task spec.
- **[`requirements/`](requirements/)** — That framework, *filled in*
  for the HPLC autosampler problem.
- **[`../02-hardware-selection/`](../02-hardware-selection/)** —
  General framework: how to choose hardware once requirements are
  fixed.
- **[`../../robots/mycobot-280-pi/docs/`](../../robots/mycobot-280-pi/docs/)** —
  The specific arm we are starting with, and the existing simulated
  pick-and-place demo we will adapt.

## A note on numbers

The numbers in the requirements (vial size, tray slots, payload,
repeatability, budget) are pinned to **specific reference products**
named inline. They are good enough to pick hardware against, but they
are not contractual — when the project commits to a specific HPLC
model and a specific lab, expect to tighten them. Sources are linked
inline in each doc.
