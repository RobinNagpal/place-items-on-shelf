# HPLC Autosampler — Requirements

This folder is **the requirements for the project**. Every later
hardware and software choice gets filtered through these numbers, so
**the requirements are the starting point** — not the arm, not the
gripper, not the camera.

The format mirrors the general framework in
[`../../01-finalize-requirements/`](../../01-finalize-requirements/).
Two source files there:

- [`01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md)
  — the **7 core questions** every project must answer.
- [`02-additional-requirements-to-consider.md`](../../01-finalize-requirements/02-additional-requirements-to-consider.md)
  — the **second checklist** of things people miss in the first pass.

This folder fills both in, specifically for the HPLC autosampler
tray-loading task.

## Read these in order

1. **[`01-task-and-objects.md`](01-task-and-objects.md)** — the task
   one-liner plus the **objects** the robot touches (vials, racks,
   trays) with real dimensions from public datasheets.
2. **[`02-environment.md`](02-environment.md)** — where the task
   happens (lab bench, humans nearby, lighting, clutter).
3. **[`03-success-precision-speed.md`](03-success-precision-speed.md)** —
   what counts as success / failure, how exact the placement must
   be, how fast each cycle must run.
4. **[`04-workspace-and-reach.md`](04-workspace-and-reach.md)** —
   the physical reach envelope and obstacles.
5. **[`05-practical-limits.md`](05-practical-limits.md)** — budget,
   power, safety, software to connect to, who maintains it.
6. **[`06-additional-considerations.md`](06-additional-considerations.md)** —
   the second-checklist topics: duty cycle, lifespan, operator
   profile, logging, failure behaviour, regulators, scale.

## How to read the numbers

The numbers are **realistic ballparks** from public datasheets and
typical lab practice. They are good enough to pick hardware against,
but they are **not contractual**. When the project commits to a
specific HPLC model, a specific lab, and a specific budget owner,
these numbers should be tightened.

Where a number comes from a vendor datasheet or a public reference,
the link is in the **Sources** section at the bottom of each file.

## Output of this folder

Once these six files are agreed on, the project has the **task
specification** that Layer 2 (hardware) needs. From here, the
hardware selection in
[`../../02-hardware-selection/`](../../02-hardware-selection/) is
the next thing to work through, in order.
