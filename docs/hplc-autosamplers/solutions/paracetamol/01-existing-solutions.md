# 01 — How labs automate the weighing step today (short version)

A one-screen summary. The wider survey of HPLC-adjacent commercial
products lives in
[`../../research/05-existing-solutions.md`](../../research/05-existing-solutions.md).

Every commercial system that actually weighs powder to a target mass
follows the **same pattern**: a dedicated *dosing balance* does the
milligram-level dispensing, and whatever robot is around it only
shuttles labware. No commercial system uses a generic robot arm to
scoop powder, because dispensing a fraction of a milligram is the
balance's job, not the arm's.

| System | What it does for weighing | Use it ourselves? |
|---|---|---|
| **Mettler Toledo XPR + Quantos** | Dosing balance with swappable RFID-tagged powder heads. ±0.1 mg at 5 mg. ~$30–50k. | **Yes — copy the pattern.** |
| **Chemspeed SWING / FLEX** | Cartesian gantry workstation, balance moves under heads. $200k+. | Pattern OK; price too high. |
| **Hamilton STAR / Tecan Fluent / Beckman Biomek** | Pipetting workstations; optional on-deck balance for *gravimetric verification* of pipetted liquids. **No powder dispensing.** | No — wrong tool for Step 1. |
| **PAL System (RTC / PAL3)** | Autosampler with an optional balance module for tare/weigh of *vials*. **No powder dispensing.** | No — wrong tool for Step 1. |

**The one line we take away:** copy Mettler's pattern. Use a real
Quantos for the dispensing. Then our job is just to pick the arm and
gripper that handle the *rest* of the eight workflow steps too. That
is what [`02-hardware-choice.md`](02-hardware-choice.md) does next.
