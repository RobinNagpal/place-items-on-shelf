# Operator Interface

The operator interface is the **hardware a human uses to talk to the
robot.** Buttons, screens, teach pendants, status lights — anything a
person touches or looks at to control or monitor the cell.

Software UIs (web dashboards, ROS rqt panels) belong in a later layer.
This file is about the *physical* hardware.

## Why this matters

Pick the wrong interface and:

- An engineer struggles with a bad teach pendant for the next year.
- A factory worker can't figure out how to start the cell, calls
  maintenance, the line stops.
- The operator can't see the status from across the room and walks into
  the cell unaware.

A good operator interface is matched to **who actually uses it**, not to
what's technically possible.

## Who is the operator?

This decides everything. Re-read Layer 1's "who operates it day-to-day"
answer.

| Operator | Interface they want |
|----------|---------------------|
| Robotics engineer | Teach pendant + Linux terminal + full SDK access. |
| Production technician | Simple HMI panel with 3 buttons: Start, Stop, Reset. |
| Untrained factory worker | Stack lights + a single big "go" button. Maybe none — automatic. |
| Nobody (unattended) | Remote monitoring + alerts. No physical interface, just status lights. |

The same cell often needs **two interfaces** — one rich one for setup
and debugging, one simple one for daily operation.

## The hardware pieces

### Teach pendants

The handheld tablet-with-buttons that comes with most cobots. You use
it to:

- Move the arm by hand or in jog mode.
- Record poses.
- Edit and run programs.
- See status, errors, logs.

The pendant is the engineer's main tool. It's almost never the right
tool for a daily operator.

Vendor-specific pendants:

- **Universal Robots PolyScope (CB3 / e-series tablet)** — touchscreen
  tablet on a tether. The most operator-friendly cobot pendant.
- **FANUC iPendant** — physical buttons + small screen. Industrial,
  ruggedized.
- **ABB FlexPendant / OmniCore pendant** — touchscreen.
- **KUKA smartPAD** — touchscreen with hardware buttons.
- **Franka Desk** — web-based, runs in any browser pointed at the arm.
- **Techman pendant** — touchscreen with TMflow software.

**Best for what:**

- UR PolyScope — fastest to teach for new users.
- Franka Desk — easiest to use from a normal laptop.
- FANUC iPendant — when you need a pendant rated for harsh environments.

### HMI panels (operator panels)

A flat panel with a screen, often plus physical buttons. Mounted on the
cell or on a swing arm. Runs vendor HMI software (or your own).

Common brands:

- **Siemens SIMATIC HMI** — premium, integrates tightly with Siemens PLCs.
- **Allen-Bradley PanelView** — same idea, for Rockwell.
- **Beijer iX** — multi-vendor.
- **Pro-face, Wonderware, Beckhoff CP6xxx** — alternatives.
- **Industrial touchscreens (RasPi + 7" touch, Advantech, OnLogic)** — when
  you want to build your own HMI software.

**Best for what:**

- Siemens / AB HMI — production cells already standardised on those PLCs.
- Custom Raspberry Pi touchscreen — research, demos, when you want full
  control of the UI.

### Push buttons, selector switches, indicators

Physical buttons mounted on the cell or operator panel.

- **Push button (momentary)** — pressed, releases. "Start cycle."
- **Push button (maintained)** — stays in. "Auto mode on."
- **Mushroom e-stop** — separate file ([safety](09-safety-equipment.md)).
- **Selector switches** — 2 or 3 position. "Manual / Auto / Off."
- **Pilot lights** — green, red, amber, blue indicators next to buttons.

Common brands: **Schneider Harmony, Allen-Bradley 800F, Siemens 3SU,
EAO, Bernstein**.

**Best for what:** any cell that runs without a touchscreen daily.
Production lines, packaging, assembly.

### Stack lights (signal towers)

Tower of coloured lights and a buzzer on top of the cell. Read it from
across the room.

Common brands: **Banner TL50, Patlite LR / LA, Werma, Allen-Bradley
855T, Schneider XVB**.

Typical colour code:

- **Green** — running normally.
- **Amber** — warning / needs attention soon.
- **Red** — stopped / fault.
- **Blue** — operator action needed.
- **White** — power on (no other meaning).

**Best for what:** every cell that ever runs unattended for a few
minutes.

### Tablets / mobile devices

A regular iPad / Android tablet running a custom app. Sometimes used as
the operator HMI.

- **Best for:** demos, light-duty cells, mobile robots. NOT for cells
  where dropping the tablet stops production.
- **Watch out for:** WiFi reliability, battery, dropping, and the IT
  team who doesn't want random tablets on their network.

### Voice / web / chat interfaces

Newer category. Operator speaks ("pick the red cup"), or types into a
web dashboard.

- **Best for:** R&D, demos, accessibility, and AI-powered cells where
  the operator's intent is high-level.
- **Not yet best for:** production, where deterministic input matters.

### Keyboards and screens

A regular keyboard + monitor on the IPC running ROS 2.

**Best for:** engineers setting up the system. Not for daily operators.

## How to pick

1. **Will the same person set up AND operate the cell?** → A teach
   pendant is enough.
2. **Different people setting up vs. operating?** → Teach pendant for
   setup + simple HMI / buttons for daily use.
3. **High-volume production, untrained operator?** → Minimal physical
   interface (a few buttons), stack light, automated cycling.
4. **Unattended cell?** → Stack light + remote monitoring (Slack alerts,
   web dashboard).
5. **Research demo?** → Teach pendant + laptop on the desk. Don't
   over-engineer.

## Output of this file — your operator interface plan

```
Setup interface:         vendor teach pendant (model: ___ )
Daily operator interface: HMI panel / buttons / tablet / none
Stack light:             yes / no, model: ___
Push buttons / switches: ___ (qty and labels)
Remote monitoring?:      yes (Slack / web / SMS / email) / no
Documentation for operators: yes (location: ___) / no
Languages supported:     ___
```

## Common mistakes

1. **Teach pendant as the daily interface.** Engineers love them.
   Operators hate them.
2. **No stack light.** Nobody knows the cell faulted until they walk
   over.
3. **Touchscreen in a greasy environment.** Wear it out in three months.
   Use protected or membrane switches.
4. **Critical button buried in a sub-menu.** Operator can't find Start
   under stress. Put it on a physical button.
5. **No documentation.** Operator runs the wrong program, breaks the
   product.
6. **Internet-only HMI in a factory.** WiFi drops, daily operator
   can't run the cell, production stops.

## What's next

That's all the hardware. With this file, your **bill of materials** for
Layer 2 is complete:

- Arm
- Gripper
- Sensors
- Mount
- Power
- Control hardware
- Network
- Cables
- Safety equipment
- Operator interface

Cross-check it against the Layer-1 requirements. Add up the prices.
That's your hardware quote.

The next layer (to be written) covers the **software side** — what
runs on top of this hardware. ROS 2, MoveIt, vendor SDKs, perception
code, AI models, the build-vs-buy decisions.

Until that lands: you have everything you need to actually buy hardware
and put it on a table.
