# 08 — Safety Validation

The cell has worked through bring-up, pilot, and acceptance. Before
it operates around people without a robotics engineer present, you do
a **formal safety review**.

This file is not a substitute for a real safety engineer or for the
actual ISO / OSHA / CE / UL standards. It's the **map of questions**
you must answer, and the documents you must end up with.

Take it seriously. A robot incident with a human is the project-
ending kind of bad.

## What you need before this step

- A fully bring-up cell ([05](05-bring-up-checklist.md)).
- Layer 2's [`09-safety-equipment.md`](../02-hardware-selection/09-safety-equipment.md)
  reviewed.
- A trained safety reviewer or robotics integrator. For anything
  beyond a desktop demo, **hire one** if you don't have one in-house.

## The standards you'll hear about

These appear in almost every robotics safety conversation. Read at
least the introductions:

- **ISO 12100** — General risk assessment for machinery. The "what
  could go wrong, how badly, how often" framework.
- **ISO 10218-1 / -2** — Safety for industrial robots. -1 covers the
  robot itself, -2 covers the integrated cell.
- **ISO/TS 15066** — Specifically for **collaborative robots**
  (cobots) sharing space with humans. Lists permissible force /
  pressure limits per body region.
- **ISO 13849** — Performance levels for safety-related control
  systems. ("How reliable does the e-stop have to be?")
- **IEC 62061** — Functional safety of electrical control systems.
  Adjacent to 13849, used in some sectors.
- **OSHA 29 CFR 1910** (US) and **Machinery Directive 2006/42/EC** (EU)
  — the regulatory frameworks the above standards live under.

You don't memorise them. You **consult them** (or someone who knows
them) for the questions below.

## The five questions every safety case answers

### 1. Who is exposed to risk?

- Trained robotics engineers only?
- Trained operators (untrained on robotics)?
- Untrained bystanders?

Each tier raises the safety bar.

### 2. What's the worst-case injury?

Use the risk-assessment matrix from ISO 12100:

- **Severity** — scratch / fracture / death.
- **Frequency of exposure** — once a year / once a shift / continuous.
- **Possibility of avoidance** — yes / sometimes / no.

These multiply into a risk rating. The rating tells you which
safety measures are needed.

### 3. What stops the robot when it's about to hurt someone?

The hierarchy of protective measures, in order of preference:

1. **Inherent safe design.** Light arms, soft surfaces, low payload —
   incapable of severe harm.
2. **Engineered guards.** Light curtains, safety scanners, fenced
   workspaces.
3. **Safety-rated motion limits.** Cobot speed / force limits
   conformant to ISO/TS 15066.
4. **Administrative controls.** Procedures, signage, training.
5. **PPE.** As a last resort. Almost never relied on alone.

You need a written argument for *why* the chosen measures are
sufficient for the risk rating.

### 4. Is the safety system itself reliable?

ISO 13849 Performance Levels (a–e) and IEC 62061 SILs measure how
*trustworthy* the safety logic is. Common targets:

- **PL d / SIL 2** — typical for cobot speed-and-force limits.
- **PL e / SIL 3** — required for e-stop in some sectors.

This is mostly the safety relay / safety PLC vendor's job. You
inherit the rating from the device's datasheet. Your job is to wire
it correctly, prove it works, and document it.

### 5. What happens when it fails?

- **Fail-safe.** Failure puts the system into a safe state (motion
  stops, brakes engage).
- **Fault detection.** A broken e-stop wire is *detected*, not
  silently ignored.
- **Reset procedure.** A defined sequence the operator follows to
  re-enable motion after any stop.

## The functional safety tests

Beyond the smoke tests in [05](05-bring-up-checklist.md), the formal
safety validation runs:

- **Each e-stop, 3 times each.** Measure time-to-stop. Compare to
  ISO 10218 / vendor spec.
- **Light curtains:** break the beam; arm stops. Repeat at 3 points
  along the curtain.
- **Safety scanner:** walk into each zone (warn, slow, stop) at
  three approach angles.
- **Door interlock:** open the door; arm stops. Try to enable with
  the door open — must refuse.
- **Cobot force limits** (if applicable): apply a controlled force
  to the arm in motion. It must stop within the ISO/TS 15066 limits.
- **Wiring fault simulation:** with the cell off, disconnect one wire
  of a redundant safety circuit. Power on; the system must detect
  and refuse to enable.

Every test is logged with the time-to-stop or pass/fail and signed
by the safety reviewer.

## The risk assessment document

The output of all this is a **risk assessment** document, typically
structured as:

```
Cell name:                              ___
Standards referenced:                   ISO 12100, ISO 10218-2, ISO/TS 15066
Exposed personnel categories:           ___
Identified hazards:                     1. Pinch at gripper, 2. Crush against table, 3. ...
Per-hazard risk before measures:        severity × frequency × avoidability
Protective measures applied:            inherent design / guards / motion limits / admin / PPE
Per-hazard risk after measures:         residual risk rating
Safety-system performance level (PL / SIL): ___
Functional test results:                 ___
Operator training plan:                  ___ (cross-ref [09](09-runbooks-and-operator-training.md))
Sign-offs:                               integrator / customer / safety engineer
```

This document is what an auditor, an inspector, or your insurer
will ask for. It's also what makes the project survive a near-miss
without losing the cell.

## When in doubt: hire someone

For:

- Customer-facing cells.
- Cells beyond a desktop arm with hard guarding.
- Cells in regulated environments (food, medical, automotive).
- Cells operated by anyone other than the building team.

…**hire a safety integrator.** It costs less than a single incident.

The docs in this layer get you to the right questions. A trained
safety engineer answers them definitively.

## Output of this step

```
Risk assessment document path:    ___
Standards followed:                ___
Exposed personnel categories:      ___
Hazards identified:                ___ (count)
Highest residual risk:             ___
Safety-system PL / SIL:            ___
Functional tests passed:           ___ / ___
E-stop time-to-stop (max):         ___ ms
Hired safety reviewer?:            yes / no — name: ___
Sign-offs:                         integrator ___, customer ___, safety ___
Insurance / regulatory body notified?: yes / no / not applicable
```

## Common mistakes

1. **"Cobots are safe by default."** They're *capable* of being safe.
   That's different. ISO/TS 15066 still requires force / pressure
   limits to be tuned and tested.
2. **No risk assessment.** When something happens, you have no defence.
3. **Single e-stop wire.** Most safety standards require redundant
   wiring. Check the standard, check the wiring.
4. **Skipping the "wiring fault" test.** A safety system that doesn't
   detect its own faults isn't safety-rated.
5. **Re-using a generic risk assessment from another cell.** Each
   cell is different. Re-do it.
6. **Signing the document yourself.** The integrator can't be the
   safety reviewer. Two different people.

## What's next

The cell is safe to operate. Now make sure the operator knows how to
operate it.

→ Next: [09-runbooks-and-operator-training.md](09-runbooks-and-operator-training.md)
