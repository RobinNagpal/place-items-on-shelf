# Actuation And Power Systems

"Actuation" = the motors. "Power" = what feeds them.

The motors are already inside the arm. What you pick is:

- **Wall power** for the arm's controller.
- **Extra DC supplies** for sensors, PCs, lights.
- **Compressed air** — only if you have a pneumatic or vacuum gripper.
- A **UPS** for production cells.

## Wall power

| Region | Common voltage |
|--------|---------------|
| North America | 120 V single-phase (wall), 208 V three-phase (industrial) |
| Europe | 230 V single-phase, 400 V three-phase |
| Asia | 100–240 V single-phase, 380–415 V three-phase |

- **Small cobots** (UR3e–UR10e, Franka FR3, myCobot, Niryo) run on
  single-phase wall power.
- **Bigger industrial arms** (FANUC M-20, KUKA KR16) often need
  three-phase — call an electrician before you commit.
- **Hobby setups** (myCobot 280 Pi) can run from USB-C or a small DC brick.

Always read the arm's "input power" line. Don't guess.

## DC supplies

The arm's controller makes its own DC internally. You need *extra* DC
supplies for:

- Non-bus-powered sensors (some F/T sensors, lights).
- Industrial PCs and edge AI boxes — usually 24 V DC.
- External relays, fans.

Common brands:

- **Mean Well** — cheap, reliable, the default in most cells.
- **Siemens SITOP, Phoenix Contact QUINT, TDK-Lambda** — premium
  industrial when reliability and certifications matter.

## Pneumatics (only if you use air)

Skip this section if your gripper is electric.

You need:

1. **Compressor + tank** to make and store the air.
2. **Air dryer** — removes water. Skip it and the gripper rusts.
3. **FRL** (filter, regulator, lubricator) — cleans and sets pressure.
4. **Lines + solenoid valves** — switch air on and off.

Typical cobot pressure: **~6 bar / 87 psi**.

Common brands:

- **Atlas Copco, Kaeser** — industrial compressors.
- **SMC, Festo, Parker, Norgren** — valves and fittings.

## UPS (backup power)

A power blip mid-task can drop a part or jam the arm.

- **Hobby / lab** — skip.
- **Production** — APC, Eaton, or CyberPower. Size for the controller
  plus your shutdown procedure.

## Power cables

Different from data cables — higher current, thicker, and:

- **Right cross-section** for the current.
- **Continuous-flex-rated** if the cable moves with the arm. Office PVC
  cable cracks in weeks.
- **Proper grounding** at every metal part — not optional.

Common brands: **Lapp, Helukabel, Igus chainflex, Belden**.

## Output of this file — your power list

```
Wall power:              120V single / 230V single / 400V three-phase
Arm controller draws:    ___ A peak
Extra DC supplies:       ___ × Mean Well ___V ___A
Compressed air?:         yes / no — ___ bar — compressor: ___
Backup power (UPS)?:     yes / no — ___ VA, runtime ___ min
Total power budget:      ___ kW
Grounding plan:          ___
```

## Common mistakes

1. **Assuming three-phase exists.** Often it doesn't.
2. **No-brand PSU.** It dies, the whole cell goes down.
3. **No air dryer.** Gripper rusts in months.
4. **No UPS in production.** First brownout takes out the controller.
5. **PVC power cable on a moving arm.** Cracks and shorts.
6. **No grounding.** Damages sensors; safety violation.

## What's next

The arm is powered. Next: the computer that runs it.

→ Next: [06-control-hardware.md](06-control-hardware.md)
