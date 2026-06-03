# Safety Equipment

If a human can step into the area where the arm moves, **safety equipment
is not optional.** It is legally required in most places, and it is a
moral requirement everywhere.

This file is about the physical safety hardware. The rules behind it
(ISO 10218, ISO/TS 15066) are referenced where they matter, but a real
safety design needs a safety engineer — not just docs.

> ⚠️ This file gives an overview. **Do not use it as the only reference
> for a real safety design.** Local laws apply. Consult a safety expert
> or your robot vendor's safety guide before deploying near humans.

## Why safety hardware exists

A 5 kg cobot moving at full speed has the energy of a hammer swing. An
industrial 100 kg arm has the energy of a small car. Without safety
gear:

- An operator reaches in to clear a jam and gets hit.
- A maintenance technician forgets the arm can move and gets pinned.
- A nearby worker walks into the workspace at the wrong moment.

Safety hardware is what makes the arm **stop** (or slow down, or refuse
to start) when any of those happen. The rules are written in blood —
literally; every clause in ISO 10218 traces back to a real injury.

## The two safety strategies

You will pick one of two approaches:

1. **Fence it off.** Put a physical guard around the arm. Anyone inside
   the fence is in danger; anyone outside is safe. The arm runs fast.
   Used for industrial arms and high-speed cobots.
2. **Power and force limiting (collaborative).** No fence. The arm runs
   slowly enough and softly enough that if it hits a human, no serious
   injury can result. Used for true cobot operation.

A cell can use **both** — fast inside a fence, slow when a human is
detected nearby.

## The hardware pieces

### Emergency stop (E-stop) buttons

The big red button. Pressing it cuts power to the arm.

- **Every cell must have at least one.**
- Must be **mushroom-head**, must twist or pull to release, must be
  reachable from anywhere in the operator area.
- Wired through a **safety relay** or **safety PLC** — not into the
  regular controller. A regular controller crashing is not allowed to
  block the e-stop.

Common brands: **Schmersal, IDEM, Bernstein, Pilz, Banner, Allen-Bradley
800F, Siemens 3SU**.

**Best for what:** every cell. No exceptions.

### Safety light curtains

A row of infrared beams across the opening of the cell. Anything
crossing them triggers a stop.

- **Beams every few mm to a few cm**, depending on resolution category.
- **Finger-resolution** (~14 mm) for close work; **hand-resolution**
  (~30 mm) for walk-through detection.

Common brands: **SICK, Banner, Omron, Keyence, Pilz**.

**Best for what:** cells with a fixed opening (loading bays, conveyor
gaps).

### Safety laser scanners

A laser sweeps across an area. You define safe zones and warning zones.
A human in the warning zone slows the arm; in the safe zone stops it.

- More flexible than light curtains — you draw the zones in software.
- More expensive.

Common brands: **SICK microScan3, Keyence SZ-V, Omron OS32C, SICK
nanoScan3** (small format).

**Best for what:** open cells where humans can approach from many sides.
Mobile robots. Cells without fixed walls.

### Safety mats

A pressure-sensitive floor mat. Step on it, arm stops.

Common brands: **Tapeswitch, ASO, SICK**.

**Best for what:** simple "is someone standing in front of the cell"
detection. Cheaper than a scanner.

### Two-hand controls

Two big buttons spaced so an operator must use both hands at once. As
long as both are held, the arm runs; release either, it stops.

- Used so the operator's hands can't be in the danger zone while the
  arm runs.
- Common in press / stamping work.

**Best for what:** any "operator must hold position to trigger motion"
task.

### Safety relays / safety PLCs

The little box that takes signals from e-stops, light curtains, etc.,
and decides whether to enable the arm. Designed to fail safely (a
broken wire stops the arm, doesn't enable it).

Common brands:

- **Pilz PNOZ** — premium German safety relays. Very common.
- **Sick Flexi Soft** — modular safety PLC.
- **Schmersal PROTECT-PSC** — safety PLC.
- **Siemens SIRIUS** — Siemens's safety relays / PLC.
- **Allen-Bradley GuardLogix** — Rockwell's safety PLC.

**Best for what:**

- Pilz PNOZ — simple wiring, one box, fixed function.
- Pilz / Sick / AB safety PLCs — bigger cells with multiple zones and
  modes.

### Safety guards (fences, barriers)

Physical fences keep humans out of the danger zone.

- **Welded mesh panels** — common industrial.
- **Polycarbonate panels** — when you want to see through.
- **Roller shutters / safety doors** — controlled entry points.

Common brands: **Troax, Folding Guard, Procter**.

**Best for what:** any cell where humans should be physically blocked
from the arm.

### Status lights (stack lights / signal towers)

A tower of coloured lights on top of the cell that shows the state at a
glance — green (running), yellow (warning), red (stopped), blue
(operator action needed).

Common brands: **Banner TL50, Patlite, Werma, Allen-Bradley 855T**.

**Best for what:** every cell. The cheapest signal to operators that
something needs attention.

## The standards (very brief)

The relevant standards if humans share the workspace:

- **ISO 10218-1 / 10218-2** — safety requirements for industrial robots
  and the cell around them.
- **ISO/TS 15066** — specifically about collaborative robot operation
  (force, power, biomechanical limits).
- **ISO 13849** — safety of control systems generally. Defines
  **Performance Levels (PL a–e)**.
- **IEC 61508 / 62061** — same idea, in electrical safety language. Uses
  **Safety Integrity Levels (SIL 1–4)**.
- **OSHA** (US) and equivalent national regulations — the law that says
  you must do it.

For each safety function (e-stop, light curtain, etc.), you'll need to
pick a target Performance Level. Cobot safety functions typically need
**PLd Category 3** or higher.

## Are cobots safe by themselves?

**Sometimes.** Cobots have built-in torque limits and slow-down
behaviour that satisfy *some* requirements of ISO/TS 15066. They are
**not** automatically safe in every configuration.

Specifically:

- Cobots become unsafe if you add a sharp tool (knife gripper, welder).
- Cobots become unsafe at higher speeds.
- Cobots become unsafe carrying heavy or pointy payloads.

If any of those apply, you need external safety hardware **even with a
cobot**.

A risk assessment (mandatory under ISO 12100) decides this — not the
cobot vendor's marketing page.

## Output of this file — your safety plan

```
Approach:                fenced / collaborative / mixed
E-stop buttons:          ___ (qty), locations: ___
Light curtains:          ___ (model), at: ___
Safety scanners:         ___ (model), zones: ___
Safety mat:              yes / no
Two-hand control:        yes / no
Safety relay / PLC:      ___
Status light:            ___
Risk assessment done?:   yes (date: ___) / no
Target Performance Level: PL ___
Standards to comply with: ISO 10218 / ISO/TS 15066 / others: ___
```

## Common mistakes

1. **"It's a cobot, so it's safe."** Only at low speeds, light payloads,
   and with no sharp tools. Otherwise: external safety.
2. **No risk assessment.** Required by law in most places.
3. **E-stop wired into the regular PLC, not a safety relay.** Won't pass
   inspection.
4. **Safety device with wrong Performance Level.** A PLb light curtain on
   a PLd application doesn't meet the rules.
5. **No documentation.** Inspectors and lawyers ask for it. Have it.
6. **Adding a knife / welder to a cobot without re-doing the
   assessment.** The cell is now an industrial cell, not a collaborative
   cell.

## What's next

The cell is safe. Now: how does a human **tell the robot what to do**?

→ Next: [10-operator-interface.md](10-operator-interface.md)
