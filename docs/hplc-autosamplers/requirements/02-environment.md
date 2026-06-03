# 02 — Environment

> Answers question **3** from
> [`../../01-finalize-requirements/01-understanding-the-problem.md`](../../01-finalize-requirements/01-understanding-the-problem.md):
> "Where does the task happen?"

## The setting in one line

> A small **lab bench** next to an HPLC instrument, indoors, with
> **a human technician sharing the workspace**.

## Tidy or messy?

**Tidy.** Every important position is fixed:

- The HPLC instrument is bolted to a bench (or on a wheeled cart
  that does not move during the run).
- The autosampler drawer opens in the same place every time.
- The inbound rack sits in a known mount on the bench (we will
  build a small alignment plate).
- The barcode reader is mounted in a known spot.

This means **the robot can rely on calibrated home positions** —
perception is mostly checking that the world matches the calibrated
layout, not searching for things in a cluttered scene.

## Indoor or outdoor?

**Indoor.** Lab climate-controlled — temperature roughly 18–24 °C,
humidity 30–60 %. No wind, no rain, no dust storms.

What lab conditions still affect us:

- **Vibration.** A noisy HVAC, a centrifuge, or someone slamming a
  door nearby can shake the arm. The mount must be rigid.
- **Temperature drift.** A cold morning can shift the bench by
  fractions of a millimetre. Calibration must happen at least once
  per shift, ideally daily.

## Lighting

Standard lab lighting — **white fluorescent or LED** ceiling
panels, 300–500 lux at the bench. Some labs supplement with desk
lamps.

What this means for perception:

- **Light is reasonably consistent**, but reflections off the
  clear glass vials are a real headache. A diffused light source
  or a polarising filter on the camera helps.
- **Amber vials** (sometimes used for light-sensitive samples) are
  dark and harder to detect with an RGB camera.
- We avoid windows that get direct sunlight — sun changes
  exposure too much through the day.

## Cluttered?

**Moderately cluttered** — the bench is shared with:

- The HPLC instrument and its open drawer.
- The inbound rack of ready vials.
- The barcode reader on a small stand.
- Possibly a waste bin for failed vials.
- The technician's notebook / tablet.

The robot must plan motions that **avoid the HPLC housing, the
drawer rails, the barcode reader stand**, and **already-placed
vials in the tray** (these grow during a load cycle).

A useful trick: keep all hardware **inside the arm's reach
envelope but outside its `home` pose**, so the arm can return to
home and never collide.

## Are humans nearby?

**Yes — and often.** The technician is in the room and may:

- Replace the inbound rack with a new one mid-run.
- Press an emergency stop.
- Reach in to retrieve a fallen vial.

This is the single most important environmental fact, because it
forces:

- A **collaborative arm** (force-limited, rated under **ISO 10218-1
  / ISO 10218-2** and **ISO/TS 15066**) — or a guarded cell with
  light curtains. v1 strongly prefers the collaborative-arm path
  because the cell is far cheaper and friendlier to lab work.
- A visible **status indicator** (light or screen) so the tech
  knows whether the arm is paused, running, or in fault.
- An accessible **physical emergency stop** within arm's reach of
  the technician.
- Slow speeds when the technician is in the work envelope.

## Where is the arm mounted?

**Bench-mounted, fixed base.** No mobility.

A small mounting plate bolted to the bench, with the arm screwed
into it. The mount is on the **operator-facing side** of the
autosampler so the arm is between the technician and the inbound
rack — the arm's body shields the rack from accidental knocks.

## What this means for the next layers

| Layer-2 topic       | Constraint from this doc                                |
|---------------------|---------------------------------------------------------|
| Arm choice          | Must be **collaborative (cobot)**                       |
| Mount design        | **Rigid bench plate**, vibration-tolerant               |
| Camera + lighting   | **Diffused light**, avoid direct sun, plan for glass    |
| Safety              | E-stop, status indicator, **ISO 10218 / TS 15066** path |

## Sources

- [ISO 10218 & ISO/TS 15066 Explained — AMD Machines](https://amdmachines.com/blog/robot-safety-standards-iso-10218-and-ts-15066-explained/)
- [Collaborative Robots — ABB safety FAQ](https://new.abb.com/products/robotics/robots/collaborative-robots/faqs/safety)
- [Evolution of safety requirements in industrial robotics — ScienceDirect (ISO 10218 2025)](https://www.sciencedirect.com/science/article/pii/S2590123026015203)
- [Collaborative robot safety standards — Standard Bots](https://standardbots.com/blog/collaborative-robot-safety-standards)

→ Next: [`03-success-precision-speed.md`](03-success-precision-speed.md)
