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

Two sibling subfolders, plus this README.

- **[`research/`](research/)** — The "understand the problem" stage:
  what the task is, what HPLC actually is, what is still manual today,
  why this particular step is worth automating, and which companies
  already work in the space. **Read this first.**
- **[`requirements/`](requirements/)** — The "what the robot must do"
  stage: concrete answers to the Layer-1 questions with specific
  reference products (vial, rack, tray) pinned. **Requirements are
  the starting point** for every hardware and software choice in
  Layer 2.

## What's in research/

Five short files, read in order:

1. [`01-what-needs-to-be-done.md`](research/01-what-needs-to-be-done.md) — the whole task in one page.
2. [`02-what-is-hplc-and-an-autosampler.md`](research/02-what-is-hplc-and-an-autosampler.md) — minimum background: vial standard, tray standard, what the autosampler does and does not do.
3. [`03-manual-steps-today.md`](research/03-manual-steps-today.md) — sample prep, capping, tray loading, drawer. Includes the **rationale for loading on the bench** (not inside the instrument).
4. [`04-why-automate-tray-loading.md`](research/04-why-automate-tray-loading.md) — why this step in particular, vs. the rest of the workflow.
5. [`05-existing-solutions.md`](research/05-existing-solutions.md) — short, opinionated survey of the four commercial products closest to our problem (PAL RTC, HTA HT4000L, CTC HTS PAL, Andrew+) plus a couple of cobot demos and the one closest research paper.

## What's in requirements/

Six short files plus a README, each answering a slice of the Layer-1
questions for this specific project. See
[`requirements/README.md`](requirements/README.md) for the order and
the format.

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
