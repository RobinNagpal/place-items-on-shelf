# 03 — Success, Precision, And Speed

> Answers questions **4** and **5** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "What counts as success / failure?" and "How precise and how fast?"

## What counts as **success**?

A vial placement counts as success when **all** of the following are
true:

1. The vial ends up in the **correct numbered slot** of the tray —
   matching the barcode-to-slot mapping in the LIMS.
2. The vial is **upright** (long axis vertical, ±5° tilt).
3. The vial is **fully seated** in the slot (no resting on the rim,
   no cocked-at-an-angle).
4. The **cap is intact** and the septum is undisturbed.
5. **No liquid spilled** anywhere on the tray or the bench.
6. The **barcode-to-slot mapping is logged** in the LIMS with a
   timestamp and the robot's session ID.

A whole **run** counts as success when **every vial in the inbound
rack** has been correctly placed (or correctly reported as
unplaceable — see failure handling).

## What counts as **failure**?

Any of:

- Vial **dropped** anywhere outside the tray slot.
- Vial **broken**.
- Vial **placed in the wrong slot** (mismatch between read barcode
  and slot mapping).
- Vial placed **upside-down** or **at >5° tilt**.
- Cap dislodged or septum punctured by the gripper.
- A vial **moved without a log entry** (silent transport).
- The robot strikes the autosampler housing, the rack, the barcode
  reader, the tech, or itself.

## Acceptance numbers

These are the numbers the robot is held to during acceptance
testing. They are aggressive but realistic for a small cobot:

| Metric                            | Target (v1)          | Target (v2 / production) |
|-----------------------------------|----------------------|--------------------------|
| Correct placement rate            | ≥ **99 / 100**       | ≥ 999 / 1,000            |
| Vial breakage rate                | **0 in 1,000**       | 0 in 10,000              |
| Mis-slot rate (barcode/slot mix-up) | **0 in 1,000**       | 0 in 10,000              |
| Mean cycle time per vial          | **≤ 20 s**           | ≤ 12 s                   |
| 95th-percentile cycle time        | **≤ 30 s**           | ≤ 18 s                   |

> **Why 0 breakage:** broken glass in a chemistry lab is bigger
> than just a lost sample. It is a safety hazard (sharps, chemical
> spill) and triggers cleanup procedures. We design for **no**
> breakage, not "low" breakage.

## Precision required

The placement precision is set by the slot clearance, not by the
robot's catalog spec.

- Slot inner diameter: **~14 mm**.
- Vial outer diameter: **12 mm**.
- Radial clearance: **~1 mm**.
- Required placement precision: **±1 mm** at the slot surface.

For a small cobot like the **myCobot 280 Pi** with a published
**±0.5 mm repeatability** at 280 mm reach, this is achievable but
tight. We expect to need:

- **Camera-in-the-loop alignment** for the final approach (visual
  servoing on the slot).
- Per-shift **calibration** of the tray pose to compensate for
  drift.
- A **chamfered slot guide** (or accepting the tray's own chamfer)
  to help the vial drop in even if the gripper is off by a hair.

For a larger arm (e.g. UR3e at ±0.03 mm repeatability), this
becomes trivial and we may skip the visual servoing.

## Speed and cycle time

The cycle time target is set by **HPLC run length** and **lab
shift length**:

- A typical HPLC injection takes **15–30 minutes per sample**, so
  a 96-vial run takes **24–48 hours**.
- The instrument can load the next tray any time during that window,
  so loading speed is **not** the bottleneck of the run.
- But loading speed **is** the bottleneck for **how many trays a
  technician can prep per shift**.

Target: **10–20 seconds per vial**. At 15 seconds per vial:

- A 48-vial rack loads in **~12 minutes**.
- A 96-vial tray loads in **~24 minutes**.

Cycle time breakdown (rough budget):

| Phase                    | Time budget |
|--------------------------|-------------|
| Approach + grasp at rack | ~3 s        |
| Move to barcode reader   | ~2 s        |
| Barcode read + LIMS lookup | ~2 s     |
| Move to tray slot        | ~3 s        |
| Visual-servo + lower + release | ~4 s |
| Retreat + log            | ~1 s        |
| **Total**                | **~15 s**   |

## Repeatability

The robot must hit the **same position every time** (not random
inside a tolerance). A drift of more than ±0.5 mm over a session
should be caught by the camera-in-the-loop step and corrected.

A daily **calibration routine** at the start of each shift
re-zeros the tray pose, so cumulative drift between shifts does
not stack up.

## Sources

- [myCobot 280 Pi Specifications (payload 250 g, repeatability ±0.5 mm, reach 280 mm) — Elephant Robotics](https://www.elephantrobotics.com/en/mycobot-280-pi-2023-specifications/)
- [QVIRO myCobot 280-Pi specifications](https://qviro.com/product/elephant-robotics/mycobot-280-pi/specifications)
- [Leveraging Multi-modal Sensing for Robotic Insertion Tasks in R&D Laboratories — arXiv](https://arxiv.org/pdf/2307.00671) (vision-guided vial insertion)
- [HPLC Autosamplers: Perspectives, Principles, and Practices — LCGC](https://www.chromatographyonline.com/view/hplc-autosamplers-perspectives-principles-and-practices)

→ Next: [`04-workspace-and-reach.md`](04-workspace-and-reach.md)
