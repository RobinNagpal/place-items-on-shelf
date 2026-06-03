# 05 — Practical Limits

> Answers question **7** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "What are the practical limits?" — budget, power, safety,
> connectivity, maintenance.

These are the **boring but project-killing** constraints. Each one
can rule out hardware that looks perfect on paper.

## Budget

| Item                                  | Target (v1)            |
|---------------------------------------|------------------------|
| Robotic arm                           | **~$700 – $2,000**     |
| Gripper / end-effector                | **~$100 – $400**       |
| Camera (RGB or RGB-D)                 | **~$100 – $500**       |
| Lighting (diffuser, ring light)       | **~$50 – $150**        |
| Barcode reader                        | **~$50 – $200**        |
| Compute (Raspberry Pi 5 or small PC)  | **~$100 – $500**       |
| Mount, brackets, base plate           | **~$200**              |
| Cables, e-stop, status light          | **~$150**              |
| **Total v1 (hobby / educational)**    | **~$1,500 – $4,000**   |

For comparison, the industrial equivalent (Hamilton STAR or similar
liquid handler) is **$100k+**. We sit at roughly **2 %** of that
cost, with a much narrower scope.

A production deployment in a regulated lab would be in the
**$10k–30k** band — better arm, better gripper, validated software.
That is out of scope for v1.

## Power supply

- **Standard wall socket**, 110 V or 230 V, single-phase.
- Continuous draw under **200 W** at peak (myCobot 280 Pi draws ~24
  V × a few A).
- An ordinary IEC C13/C14 connector. No three-phase, no UPS for v1.
- The compute box (Raspberry Pi 5 or mini-PC) shares a power strip.

Production deployments would add a **UPS** (uninterruptible power
supply) so a power blip mid-cycle does not drop a vial.

## Safety

- **Collaborative arm** required (force-limited, rated under
  **ISO 10218-1 / 10218-2 (2025)** and **ISO/TS 15066**) — or a
  guarded cell with light curtains. v1 prefers the cobot path.
- **Hard-wired emergency stop** within arm's reach of the
  technician, mounted on the bench (not in software only).
- **Status light** (or coloured screen) at the cell: green = idle,
  blue = running, yellow = waiting, red = fault.
- **Speed and separation monitoring**: when a human is within ~30
  cm of the arm tool, the arm slows to ≤ 250 mm/s.
- **Force limit**: ≤ 80 N at the tool (low enough to be safely
  inherent for a 250 g-payload arm).
- **Documented risk assessment** even for v1, so the lab tech
  understands what the arm can and cannot do.

## Software systems to connect to

Three external systems matter:

1. **LIMS** (Laboratory Information Management System) — provides
   the *barcode → tray slot* mapping and receives the *placement
   log*. Typical interfaces: **REST API** or **HL7** (clinical).
2. **Barcode reader** — typically **USB-HID** (acts as a keyboard)
   or **serial / RS-232**. Easy.
3. **HPLC vendor software** — Agilent OpenLab, Waters Empower,
   Shimadzu LabSolutions, etc. v1 **does not integrate** with these.
   The technician copies the loaded-tray mapping in by hand or via
   a CSV import.

A long-term goal is integration with the HPLC vendor software so
the run can autostart, but that is a v2+ feature.

## Maintenance

- **Daily**, by the lab technician:
  - Wipe down the arm with isopropyl alcohol (lab hygiene).
  - Inspect gripper pads for wear.
  - Run a 5-vial calibration cycle and check placement.
- **Monthly**, by a robotics-trained engineer:
  - Tighten mounting bolts.
  - Replace gripper pads if worn.
  - Re-zero the arm against its fiducial.
- **Annually**, by the vendor (or a contractor):
  - Joint inspection.
  - Cable replacement if frayed.
  - Software updates.

Spare-parts strategy: keep **two complete spare gripper-pad sets**
and **one spare power supply** on a shelf. Anything bigger is
ordered when needed.

## What this means for the next layers

| Layer-2 topic         | Constraint from this doc                              |
|-----------------------|-------------------------------------------------------|
| Arm                   | ~$700–2,000, ISO 10218-1 / TS 15066 collaborative     |
| Power                 | Wall socket, < 200 W                                  |
| Safety equipment      | Hard E-stop, status light, force ≤ 80 N               |
| Operator interface    | Green/blue/yellow/red light + simple Start button     |
| Networking            | LAN-only LIMS access; no internet exposure            |
| Cabling               | Strain-relieved drag chain; lab-grade insulation      |

## Sources

- [myCobot 280 Pi specifications and pricing — Elephant Robotics shop](https://shop.elephantrobotics.com/products/mycobot-pi-worlds-smallest-and-lightest-six-axis-collaborative-robot)
- [ISO 10218-1 / 10218-2 (2025) and ISO/TS 15066 — AMD Machines summary](https://amdmachines.com/blog/robot-safety-standards-iso-10218-and-ts-15066-explained/)
- [Collaborative robot safety standards — Standard Bots](https://standardbots.com/blog/collaborative-robot-safety-standards)
- [FDA 21 CFR Part 11 and Importance of Regulatory Compliance in GMP / GLP Labs — Molecular Devices](https://www.moleculardevices.com/lab-notes/microplate-readers/fda-21-cfr-part-11-and-importance-of-regulatory-compliance-in-gmp-glp-labs)

→ Next: [`06-additional-considerations.md`](06-additional-considerations.md)
