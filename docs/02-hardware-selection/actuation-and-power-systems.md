# Actuation And Power Systems

"Actuation" means the motors and the things that make the arm move.
"Power systems" means everything that feeds those motors with electricity
or air.

For almost every arm you buy, **the motors are already inside the arm**.
You don't pick them separately. What you DO pick is:

- The **wall power** that feeds the arm's controller box.
- Any **extra power supplies** (for sensors, lights, computers).
- A **compressed air supply** if you have pneumatic grippers or vacuum.
- A **backup power supply** (UPS) for production setups.

This file walks through each one in plain English.

## Wall power (mains)

Where in the world are you, and what's coming out of the wall?

| Region | Standard | Common voltage / phases |
|--------|----------|--------------------------|
| North America | NEMA | 120 V single-phase (wall socket), 208 V three-phase (industrial) |
| Europe | IEC | 230 V single-phase, 400 V three-phase |
| Asia | Mix | 100–240 V single-phase, 380–415 V three-phase |

What this means in practice:

- **Small cobots** (UR3e, UR5e, Franka FR3, myCobot, Niryo) run on
  **single-phase wall power**. Plug into a normal socket.
- **Bigger industrial arms** (Fanuc M-20, ABB IRB 4600, KUKA KR16) often
  need **three-phase power**. You may need an electrician to install a
  three-phase circuit. Don't assume the building has one.
- **Hobby setups** (myCobot 280 Pi) can even run from a USB-C charger or
  a small DC supply. Check the spec sheet.

Always check the arm's "input power" line in the data sheet. Don't guess.

## Power supplies (DC)

The arm's controller turns wall AC into the DC voltages the motors and
electronics need. You usually don't see this — it's inside the
controller box.

You DO need separate DC supplies for:

- **Sensors that aren't bus-powered** — some F/T sensors, some lights.
- **Industrial PCs (IPCs)** if you use one — usually 24 V DC.
- **External lights, fans, relays** — usually 24 V DC.

Common brands of industrial DC supplies:

- **Mean Well** — by far the most common cheap-and-reliable industrial
  PSU brand. The "Mean Well 24V" is the default DC supply in most cells.
- **Siemens SITOP** — premium industrial, paired with Siemens PLCs.
- **Phoenix Contact QUINT** — premium too, German industrial.
- **TDK-Lambda, Cosel, Omron** — solid industrial alternatives.

**Best for what:**

- Mean Well — almost everything, especially small budget systems.
- SITOP / QUINT / TDK-Lambda — production systems where reliability and
  certifications matter.

## Pneumatic systems (compressed air)

If you have a vacuum gripper, a pneumatic parallel gripper, or anything
that uses compressed air, you need an air supply.

The pieces:

1. **Air compressor** — produces compressed air. Belt-driven or screw.
2. **Air tank** — buffers the supply so the compressor doesn't run
   constantly.
3. **Air dryer** — removes water. Wet air ruins pneumatic actuators.
4. **Filter, regulator, lubricator (FRL)** — cleans, sets pressure,
   sometimes adds oil mist.
5. **Air lines** — usually polyurethane tubing.
6. **Solenoid valves** — switch air on/off under electrical control.

Typical pressure for cobot pneumatics: **6 bar (87 psi)**.

Common compressor brands:

- **Atlas Copco, Kaeser, Ingersoll Rand, Sullair** — industrial. Reliable.
- **California Air Tools, Makita, Hitachi** — workshop / hobby.

Common pneumatic-component brands:

- **SMC, Festo, Parker, Norgren** — valves, regulators, fittings. All
  industry standard.

**Best for what:**

- Hobby vacuum demo — a small portable compressor or even a Venturi
  vacuum generator off a CO₂ tank. Crude but works.
- Production cell — a real factory air compressor with proper drying.

## Backup power (UPS)

If a power blip kills your robot mid-task, what happens?

- **Demo / lab** — usually nothing bad. Power comes back, robot reboots,
  you re-run.
- **Production** — a half-finished pick can drop a part, jam the arm,
  damage product. Some controllers don't like sudden power loss.

A UPS (uninterruptible power supply) keeps the system running for a few
minutes through a blip, or shuts it down cleanly during a real outage.

Common brands:

- **APC (Schneider Electric)** — most common everyday UPS.
- **Eaton, Tripp Lite, Vertiv** — alternatives.
- **CyberPower** — cheap consumer UPS, fine for small cells.

**Best for what:**

- Hobby — skip.
- Research lab — small APC Back-UPS for the PC, not the arm.
- Production cell — sized UPS for the controller, sized to your shutdown
  procedure.

## Cables for power

Power cables are different from data cables. They have to handle higher
current and are usually thicker.

- **Cable cross-section** — sized by the current the arm draws. Industrial
  arms often need 4 mm² or thicker.
- **Cable type** — for moving / flexing applications, you need
  **continuous-flex-rated** cable. Cheap PVC cable cracks after a few
  thousand flexes.
- **Grounding** — every metal part of the cell must be grounded properly.
  This is an electrical safety requirement, not optional.

Common cable brands: **Lapp, Helukabel, Igus chainflex, Belden**.

## Output of this file — your power list

```
Wall power:              120V single / 230V single / 400V three-phase
Arm controller draws:    ___ A peak
Extra DC supplies:       ___ × Mean Well ___V ___A
Compressed air?:         yes / no
  - Pressure:            ___ bar
  - Compressor:          ___
Backup power (UPS)?:     yes / no
  - Sizing:              ___ VA / runtime ___ min
Total power budget:      ___ kW
Grounding plan:          ___
```

## Common mistakes

1. **Assuming three-phase exists.** It often doesn't, and installing it
   means an electrician and a permit.
2. **Cheap PSU for everything.** A no-brand $5 PSU dies, and now your
   whole cell is down.
3. **No air dryer.** Three months in, the vacuum gripper is rusted
   solid.
4. **No UPS in production.** First brownout takes out the controller.
5. **PVC power cable on a moving arm.** Cracks. Shorts. Fire risk in the
   worst case.
6. **No grounding.** Static buildup damages sensors and computers, and
   it's an electrical safety violation.

## What's next

You have a powered, mounted arm. Next: the **computer or box that
actually runs it**.

→ Next: [control-hardware.md](control-hardware.md)
