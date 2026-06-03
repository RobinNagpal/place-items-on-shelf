# 06 — Additional Considerations

> Covers the second checklist from
> [`../../01-finalize-requirements/02-additional-requirements-to-consider.md`](../../01-finalize-requirements/02-additional-requirements-to-consider.md):
> duty cycle, lifespan, operator, maintenance, other systems,
> logging, failure behaviour, regulators, timeline, scale,
> variations, acceptance, security.

Most of these are quick — but each one decides whether a project
ships in three months or eighteen.

## 1. Duty cycle — how often does it run?

| Setting               | Target               |
|-----------------------|----------------------|
| Vials per day         | **~100–200**         |
| Working hours per day | 8 (one tech shift)   |
| Working days per week | 5                    |
| Mean utilisation      | < 30 % of the day    |

This is a **moderate duty cycle**. It rules in hobby-grade cobots
that would not survive 24/7 service.

## 2. Lifespan — how long must it last?

- **v1 (research / pilot):** ~1 year of moderate use.
- **v2 (small lab production):** 3–5 years with gripper-pad
  replacement and joint maintenance.

This rules out the cheapest plastic-only arms (which crack at the
gear teeth after a few months) but does not require an industrial
arm.

## 3. Operator — who runs it day-to-day?

- **Lab technician.** Comfortable with lab software (LIMS,
  Empower, etc.), not with robotics.
- Needs:
  - A **single Start button** to begin a tray load.
  - A **single Stop button** to pause / abort.
  - A **status light** to tell whether the arm is idle, running,
    or in fault.
  - A **plain-English log** of the last 100 placements visible on
    a small screen.
- Does **not** need: a teach pendant, a CLI, or any G-code
  knowledge.

## 4. Maintenance plan

- **In-house technician:** daily wipe-down, gripper-pad swap,
  5-vial calibration.
- **In-house engineer (us, for v1):** monthly checks; vendor
  support contract once the project is in real-lab use.
- **Vendor:** annual joint inspection or warranty repair.

See [`05-practical-limits.md`](05-practical-limits.md) for the spare
parts strategy.

## 5. Other systems to connect to

| System                      | Direction   | Protocol (v1)          |
|-----------------------------|-------------|------------------------|
| **LIMS** (sample tracker)   | Both ways   | REST API over LAN      |
| **Barcode reader**          | Read        | USB-HID                |
| **Status display**          | Write       | Local I²C / GPIO       |
| **HPLC vendor software**    | Read (v2+)  | Vendor-specific (out of scope v1) |

For v1, the LIMS link is the most important — the robot **cannot
place a vial without confirming the slot mapping**.

## 6. Logging — what records must it keep?

Per vial placement, log:

- **Timestamp** (UTC, ISO-8601).
- **Robot session ID.**
- **Operator name** (whoever pressed Start).
- **Barcode read** from the vial.
- **Slot placed in** (tray + position).
- **Outcome** (success / failure code).
- **Gripper force during release** (sanity check).

These map onto the **ALCOA** data-integrity principles required by
21 CFR Part 11 (Attributable, Legible, Contemporaneous, Original,
Accurate). v1 stores logs locally as JSONL with daily rotation; v2
ships them to the LIMS or a central audit store.

- **Retention:** local logs for 30 days; LIMS / audit store for
  **at least 7 years** in a regulated pharma lab.
- **Tamper-proof:** v2 must use append-only storage; v1 can rely
  on file-system permissions.

## 7. Failure behaviour — what happens when the task fails?

The default is **stop and call a human**:

- **Vial pick failure** (perception did not find the vial, or the
  gripper closed on nothing) → retry once, then stop and flag.
- **Barcode read failure** (no code or unreadable) → stop the
  individual vial, return it to the source rack if possible, flag.
- **Slot placement failure** (vision says the vial is not in the
  slot) → stop the whole run, do not move on. The next vial could
  collide with the still-held one.
- **Drop or break** → stop everything, sound an alarm, log the
  spill location, **do not move the arm** until cleared.

Retries are limited. Samples are too valuable to retry blindly.

## 8. Regulators

- **For v1 (hobby / educational):** no regulators apply. Treat as
  an unregulated benchtop demo.
- **For pharma / clinical production:**
  - **21 CFR Part 11** (US FDA) — electronic records, audit trail,
    electronic signatures.
  - **EU Annex 11** — the European equivalent.
  - **GMP / GLP** — depends on which lab function.
  - **CLIA** — for clinical labs in the US.
  - **CE / UL** — electrical safety for the cell as a whole.
  - **ISO 10218-1 / 10218-2 (2025)** and **ISO/TS 15066** —
    robot safety.

These do not block v1, but every architecture choice in v1 should
be **upgrade-friendly** toward them — e.g. logs already in
ALCOA-friendly format, even if we don't sign them yet.

## 9. Timeline — when does it need to be running?

| Phase                        | Target            |
|------------------------------|-------------------|
| Gazebo simulation up         | 1–2 months        |
| First real-hardware pickup   | 3 months          |
| End-to-end demo (rack→tray)  | 5–6 months        |
| Pilot in a friendly lab      | 9–12 months       |
| Production-ready             | Out of scope v1   |

This is a **buy-off-the-shelf** timeline. No custom hardware.

## 10. Scale — one cell or many?

- **v1:** one cell.
- **v2:** potentially 2–5 cells in one lab, sharing the same LIMS.
- **Many copies (10+):** out of scope. That would force a software
  rewrite for fleet management.

## 11. Variations the robot must handle

| Variation                | v1 support? | Notes                                    |
|--------------------------|-------------|------------------------------------------|
| 2 mL vials, screw cap    | **Yes**     | Default case                              |
| 2 mL vials, crimp cap    | **Yes**     | Same body geometry                        |
| 1 mL low-volume vials    | Later       | Same outer 12 × 32 mm, smaller volume    |
| Amber glass              | Later       | Camera changes needed                     |
| Partial racks            | **Yes**     | Perception finds whichever vials are there |
| Multiple tray sizes      | Later       | One tray geometry per calibration         |

## 12. Acceptance test — how do we prove it works?

A **scripted 1,000-vial acceptance run** in the target lab:

- 10 trays × 96 vials + a few partial racks.
- Real vials, real barcodes, real LIMS.
- Pass criteria:
  - **≥ 99 % correct placements**.
  - **0 broken vials.**
  - **0 mis-slot errors.**
  - **No human intervention except clearing a flagged vial.**
- Documented in a short SAT (Site Acceptance Test) report.

This is the v1 ship-criterion. Until it passes, the project is in
development.

## 13. Security

- **v1:** standalone on the lab LAN; no direct internet exposure.
- The LIMS link uses a service account with **read-only** access to
  the slot map and **append-only** access to the placement log.
- The compute box receives **OS security updates** monthly,
  ideally automatically.
- No SSH from outside the lab. No remote desktop without VPN.

For v2, a **signed software supply chain** and **role-based access
control** become real requirements; v1 just needs to not be
embarrassing.

## Sources

- [21 CFR Part 11 audit-trail requirements — Molecular Devices](https://www.moleculardevices.com/lab-notes/microplate-readers/fda-21-cfr-part-11-and-importance-of-regulatory-compliance-in-gmp-glp-labs)
- [21 CFR Part 11 Audit Trails: Definition, Requirements, Compliance — SimplerQMS](https://simplerqms.com/21-cfr-part-11-audit-trail/)
- [ALCOA and ALCOA+ data integrity overview — IntuitionLabs](https://intuitionlabs.ai/articles/21-cfr-part-11-compliance-requirements)
- [ISO 10218-1 / 10218-2 (2025) and ISO/TS 15066 — AMD Machines](https://amdmachines.com/blog/robot-safety-standards-iso-10218-and-ts-15066-explained/)
- [SAT / FAT (Site / Factory Acceptance Test) general guidance — ISPE summary](https://ispe.org/) (general industry term)

## What comes after this folder

With these six files agreed on, the project has the **task
specification**. Layer 2 ([`../../02-hardware-selection/`](../../02-hardware-selection/))
takes this spec and picks every piece of hardware — arm, gripper,
sensors, mount, power, control hardware, networking, safety,
operator interface — against the numbers above.
