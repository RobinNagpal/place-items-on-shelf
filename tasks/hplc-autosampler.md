# Task — Load Sample Vials Into an HPLC Autosampler

> A worked example of the Layer 1 problem statement, filled in for the
> project's medium-term target task: a robot arm that loads sample vials
> into an HPLC autosampler tray. See
> [`../docs/01-finalize-requirements/`](../docs/01-finalize-requirements/)
> for the framework this fills in.

## Background — what is an HPLC autosampler?

HPLC = **High-Performance Liquid Chromatography**, a workhorse analytical
technique in pharma, food, environmental, and clinical labs. A small volume
of liquid sample is pushed through a column of packed particles and the
machine measures what comes out the other end.

An **autosampler** is the loader on the front of the HPLC instrument. It
holds a tray (typically a 6 × 9 = 54-slot or 8 × 12 = 96-slot grid) of
small glass vials. The instrument's needle dips into one vial at a time,
draws a few microlitres, and injects it for analysis. Once the run is over,
the operator has to swap out the tray and load the next batch of samples.

**Why a robot here?** A typical analytical lab loads hundreds of vials a
day. The work is mind-numbingly repetitive, must be logged precisely for
chain-of-custody (regulated industries), and mistakes (wrong vial in wrong
slot, broken vial, spill) are expensive. It's a clean fit for a small
collaborative arm.

## Task one-liner

> Pick a labelled sample vial from an inbound rack, read its barcode, and
> place it in the correct slot of an HPLC autosampler tray.

## The 7 core questions

### 1. Task, in one sentence
Pick a 2 mL HPLC sample vial from an inbound rack and place it in the
correct slot of the HPLC autosampler tray, recording the
barcode-to-slot mapping in the lab system.

### 2. Objects handled

- **HPLC sample vial (2 mL standard)**
  - Shape: cylinder (often with a small flat-top crimp or screw cap)
  - Size: 12 mm diameter × 32 mm tall (vial body)
  - Weight: 5–10 g filled
  - Material: clear borosilicate glass, smooth — slippery when chilled or
    wet from condensation
  - Fragility: yes — glass can crack if pinched too hard; crimp caps can
    pop off if the vial is shaken
  - Variations: 1 mL "low-volume" vials and screw-cap variants also
    appear, but 2 mL crimp-cap is the dominant standard

- **Inbound rack** (source of vials) — typically a polypropylene rack with
  a 6 × 12 grid of round holes sized for the vials. Sits on the bench.

- **Autosampler tray** (destination) — a metal-or-plastic tray with
  numbered slots in a fixed grid, slotted inside the HPLC autosampler
  drawer. Tray geometry depends on instrument (Agilent, Waters, Shimadzu,
  Thermo all use slightly different formats).

### 3. Environment

- Tidy / messy?           **Tidy** — fixed bench, fixed instrument position
- Indoor / outdoor?       **Indoor** — climate-controlled lab
- Cluttered?              **Yes** — HPLC, racks, barcode reader, waste bin
                          all share a small bench
- Humans nearby?          **Yes** — lab technician shares the workspace;
                          collaborative-rated arm or safety enclosure is
                          required
- Arm mounted where?      **Bench-mounted** next to the autosampler, fixed
                          base, no mobility

### 4. Success and failure

**Success**
- Vial placed **upright** in the **specified slot** of the tray.
- Cap intact, no fluid spill.
- Barcode read and the `barcode → tray slot` mapping written to the LIMS
  (Laboratory Information Management System).
- ≥ 99 successful placements per 100 attempts (one missed pick is
  recoverable; broken glass is not).

**Failure**
- Vial dropped or broken.
- Vial mis-slotted (wrong slot, wrong tray, wrong orientation).
- Cap dislodged.
- Any motion that isn't recorded against a specific vial barcode.
- Arm contact with the autosampler housing or lab tech.

### 5. Precision, repeatability, speed

- Precision: **~2 mm** at the tray slot — slots are typically 14 mm wide
  for a 12 mm vial, so the gripper must place within roughly ±1 mm to
  drop cleanly without scraping the rim.
- Repeatability: **same position every time** — the slot grid is fixed.
- Cycle time: **10–20 seconds per vial**. At ~15 s, a 96-vial tray loads
  in about 24 minutes, which matches a single HPLC analytical run.

### 6. Workspace and reach

- Workspace cube: roughly **40 cm × 40 cm × 40 cm** — the inbound rack on
  one side, the open autosampler drawer on the other, the barcode reader
  in between.
- Mounting: bench mount, fixed.
- Obstacles inside the workspace: the autosampler drawer rails, the
  barcode-reader stand, the inbound rack's own walls. Vials in adjacent
  slots are also obstacles once partially loaded.

### 7. Practical limits

- Budget: small academic / contract lab, **~$1k–5k** for the arm — a
  hobby-grade educational cobot (e.g. myCobot 280 Pi) fits this. A
  production pharma lab would budget much more for an industrial cobot.
- Power: **standard wall socket**, single-phase.
- Safety: **humans share the workspace** — choose a collaborative arm
  rated for human collaboration, or build a guarded cell with light
  curtains.
- Software to connect to:
  - **LIMS** (sample tracking) via REST or HL7
  - **Barcode reader** (USB-HID or serial)
  - **HPLC vendor software** (optional, to coordinate tray-ready signals)
- Maintenance: lab technician for routine cleaning; vendor support
  contract for hardware faults.

## Additional considerations (Layer 1, part 2)

| Item                       | Answer                                                                 |
|----------------------------|------------------------------------------------------------------------|
| Duty cycle                 | ~100 vials per day, 8 hours, 5 days/week                               |
| Lifespan                   | 3–5 years                                                              |
| Operator profile           | Lab technician (familiar with lab software, not with robotics)          |
| Maintenance plan           | In-house cleaning + vendor support for hardware                        |
| Systems to connect to      | LIMS, barcode reader, HPLC instrument software                         |
| Logging required?          | Yes — every vial transfer, retention ≥ 7 years for GMP labs            |
| Failure behaviour          | **Stop and alert** — samples are precious; do not blindly retry        |
| Regulators that apply      | GLP / GMP if pharma; CLIA if clinical; CE / UL for electrical safety   |
| Deadline for live          | 6–12 months for a pilot, longer for a regulated production deployment  |
| Scale                      | One cell to start; potentially many copies across a lab network         |
| Variations to handle       | 1 mL vs 2 mL vials; crimp-cap vs screw-cap; partially filled racks      |
| Acceptance test plan       | 1,000-vial run with ≥ 99% success and zero breakage                    |
| Network exposure           | LAN inside the lab; no direct internet exposure                        |

## Why this task is a good fit for this project

- **Shapes are simple.** Vials are cylinders, racks and trays are grids.
  Perception can stay at the geometric level (no AI required for the
  first version); see
  [`../robots/mycobot-280-pi/docs/deep-dives/how-perception-works.md`](../robots/mycobot-280-pi/docs/deep-dives/how-perception-works.md).
- **Motion is mostly vertical.** Pick from above, transport, place from
  above. MTC's `approach → grasp → lift → carry → lower → release`
  template (see
  [`../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md`](../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md))
  maps onto this almost line-for-line.
- **Precision target (~2 mm) is within reach of a hobby-grade cobot.** A
  myCobot 280 Pi with a well-calibrated camera can hit this with care.
- **The task scales naturally** from "demo with three vials" to "real
  tray of 96", which means we can grow the project gradually without
  rewriting the world.

## What's next (after this Layer 1 doc)

- Take this spec into Layer 2
  ([`../docs/02-hardware-selection/`](../docs/02-hardware-selection/)) and
  pick the actual hardware: arm, gripper, sensors, mount, power, control
  hardware, networking, safety, operator interface.
- In parallel, build a Gazebo world that models the autosampler tray and
  an inbound rack, so we can test motion plans in simulation before
  touching real glass.
- Eventually, replace addison's stock MTC task with a custom one whose
  sequence is "pick vial → scan barcode → place in correct slot → log".
