# 00 — Task Specification (One-Page Summary)

> The **Layer-1 deliverable** — a single page that fits the answers to
> every question in
> [`../../01-finalize-requirements/`](../../01-finalize-requirements/)
> into one place. Files
> [`01-task-and-objects.md`](01-task-and-objects.md) through
> [`06-additional-considerations.md`](06-additional-considerations.md)
> are the long-form sources behind each line below.
>
> **Status:** v1 finalized 2026-06-05. Numbers are pinned to specific
> reference products and a reference HPLC instrument. They are good
> enough to drive every Layer-2 hardware decision and to filter every
> Layer-3 software choice.

## The task, in one sentence

Pick a **2 mL, 12 × 32 mm HPLC sample vial** from a **50-position
polypropylene rack**, read its barcode, and place it in the correct
slot of a **100-position Agilent autosampler tray** sitting in a
benchtop alignment plate.

## Reference products (the v1 pin)

| Object               | Reference product / model                                                                                                   |
|----------------------|------------------------------------------------------------------------------------------------------------------------------|
| **Vial**             | 9 mm HPLC autosampler vial — hplcvials.com — 12 × 32 mm, 1.5–2.0 mL, USP Type I borosilicate glass, PP screw cap, PTFE / silicone septum |
| **Source rack**      | MicroSolv MV9502R-02B — polypropylene, **50 indexed wells**, accepts 12 × 32 mm vials                                       |
| **Destination tray** | Agilent **100 × 2 mL "classic" tray** — straight 10 × 10 grid, ~14 mm slot ID, ~1 mm radial clearance                        |
| **HPLC instrument**  | Agilent 1290 Infinity II Vialsampler (G7129B / G7129C) — 324 × 396 × 468 mm, 19 kg                                          |

## Spec sheet

### Task & objects ([`01-task-and-objects.md`](01-task-and-objects.md))

| Item                         | Value                                                  |
|------------------------------|--------------------------------------------------------|
| Vial OD × height             | **12 mm × 32 mm**, 9 mm neck                            |
| Vial weight (filled)         | ~5–10 g                                                 |
| Vial material / fragility    | Borosilicate glass — cracks if pinched too hard         |
| Gripper jaw opening          | ~14 mm, soft (silicone) pads, force-limited             |
| Source rack capacity         | **50 wells**, 5 × 10 grid, ~25 mm vial above rack       |
| Destination tray capacity    | **100 slots**, 10 × 10 grid, ~14 mm slot ID, **±1 mm** placement tolerance |
| Tray location during loading | **On the bench**, in alignment plate — NOT inside HPLC |

### Environment ([`02-environment.md`](02-environment.md))

| Item              | Value                                                          |
|-------------------|----------------------------------------------------------------|
| Setting           | Indoor lab bench, climate-controlled (18–24 °C, 30–60 % RH)    |
| Tidy / messy      | **Tidy** — every important position is fixed and calibrated     |
| Lighting          | Standard lab LED / fluorescent, ~300–500 lux, no direct sun     |
| Clutter           | Moderate — HPLC body, rack, barcode reader, possible waste bin  |
| Humans nearby     | **Yes, often** — drives cobot + E-stop + status light + slow-on-proximity |
| Arm mount         | Fixed bench base, between technician and inbound rack           |

### Success, precision, speed ([`03-success-precision-speed.md`](03-success-precision-speed.md))

| Metric                              | v1 target          | v2 target          |
|-------------------------------------|--------------------|--------------------|
| Correct placement rate              | ≥ **99 / 100**     | ≥ 999 / 1,000      |
| Vial breakage rate                  | **0 / 1,000**      | 0 / 10,000         |
| Mis-slot rate                       | **0 / 1,000**      | 0 / 10,000         |
| Mean cycle time per vial            | **≤ 20 s**         | ≤ 12 s             |
| 95th-percentile cycle time per vial | **≤ 30 s**         | ≤ 18 s             |
| Required placement precision        | **±1 mm** at slot surface (set by ~1 mm radial slot clearance) |
| Implied tray-load time              | ~25 min for 100 vials @ 15 s/vial (loading is not the run bottleneck) |

### Workspace & reach ([`04-workspace-and-reach.md`](04-workspace-and-reach.md))

| Item                       | Value                                                  |
|----------------------------|--------------------------------------------------------|
| Cell working volume        | ~40 × 40 × 20 cm (rack, bench-tray plate, barcode reader within reach) |
| Farthest reach required    | ~250 mm horizontal, ~150 mm vertical from arm base     |
| Arm reach (preferred)      | **≥ 300 mm**; myCobot 280 Pi at 280 mm is tight        |
| HPLC body                  | **Outside** arm reach envelope by design — no in-instrument reaches |
| End-effector length budget | Keep short — every mm of gripper steals reach          |
| Mount                      | Rigid bench plate, levelled to ±0.5 mm, ArUco fiducial near base |

### Practical limits ([`05-practical-limits.md`](05-practical-limits.md))

| Item                  | Value                                                       |
|-----------------------|-------------------------------------------------------------|
| **Total v1 budget**   | **~$1,500 – $4,000** (arm, gripper, camera, lighting, barcode reader, compute, mount, safety) |
| Power                 | Wall socket, < 200 W continuous                              |
| Safety standards      | **ISO 10218-1 / 10218-2 (2025)** + **ISO/TS 15066** — cobot path |
| Tool force limit      | ≤ 80 N at the tool                                           |
| Speed near humans     | ≤ 250 mm/s when human within ~30 cm of tool                  |
| E-stop                | Hard-wired, within tech's reach                              |
| Status indicator      | Green = idle / blue = running / yellow = waiting / red = fault |
| Connectivity          | LIMS (REST over LAN), barcode reader (USB-HID), local status I²C / GPIO. No HPLC software integration in v1. |
| Maintenance           | Daily wipe + 5-vial cal (tech), monthly checks (engineer), annual vendor service |

### Additional considerations ([`06-additional-considerations.md`](06-additional-considerations.md))

| Item                  | Value                                                       |
|-----------------------|-------------------------------------------------------------|
| Duty cycle            | ~100–200 vials / day, 1 tech shift (8 h), 5 days / week (<30 % utilisation) |
| Lifespan target       | **v1:** ~1 year moderate use; **v2:** 3–5 years              |
| Operator              | Lab technician — Start / Stop button, status light, plain-English placement log |
| Failure behaviour     | **Stop and call a human.** Limited retry on pick / barcode; full stop on slot-placement or drop / break |
| Logging               | Per-placement JSONL (timestamp, session, operator, barcode, slot, outcome, gripper force) — ALCOA-aligned; v2 ships to LIMS / audit store, 7-yr retention |
| Regulators (v1)       | **None apply** — treat as unregulated benchtop demo. Architecture must stay **upgrade-friendly** to 21 CFR Part 11, EU Annex 11, GMP / GLP, CLIA, CE / UL, ISO 10218. |
| Timeline              | Gazebo sim 1–2 mo · first real pickup 3 mo · end-to-end demo 5–6 mo · friendly-lab pilot 9–12 mo |
| Scale                 | **v1:** 1 cell. **v2:** 2–5 cells / one LIMS. Fleet (10+) is out of scope. |
| v1 variations         | Screw + crimp cap, partial racks. **Later:** 1 mL low-volume, amber glass, multiple tray sizes. |
| Acceptance test       | Scripted **1,000-vial SAT** in target lab — ≥ 99 % correct, 0 broken, 0 mis-slot, no human intervention beyond clearing flags |
| Security              | Standalone on lab LAN — no direct internet, read-only LIMS slot map, append-only placement log, monthly OS updates |

## What this lets the next layers do

| Layer                                                  | What it picks, filtered through this spec                  |
|--------------------------------------------------------|------------------------------------------------------------|
| [Layer 2 — hardware](../../02-hardware-selection/)     | Cobot arm (~$700–$2,000, ≥ 300 mm reach, ISO 10218 / TS 15066), 14 mm soft-pad force-limited gripper, RGB camera + diffused light, barcode reader, Raspberry Pi 5 / mini-PC, bench plate, E-stop, status light |
| [Layer 3 — software](../../03-software-stack/)         | MoveIt 2 for motion, vision pipeline for slot localisation (visual servoing on the ±1 mm tolerance), LIMS REST client, local JSONL logger |
| [Layer 4 — integration](../../04-integration-and-bring-up/) | Bench calibration routine, per-shift fiducial re-zero, 5-vial daily-cal cycle, SAT script for 1,000-vial run |

## Sign-off

- **Version:** v1.
- **Finalized:** 2026-06-05.
- **What "finalized" means here:** all six long-form requirement files
  agree on the same v1 reference products and numbers, and Layer 2 can
  start picking hardware against the spec sheet above.
- **What "finalized" does NOT mean:** the numbers are not contractual.
  When the project commits to a specific HPLC model in a specific lab
  with a specific budget owner, expect to tighten the precision,
  cycle-time, and budget bands, and to re-confirm the tray and rack
  geometry against the lab's actual inventory.
