# Mounting And Mechanical Structure

The arm has to bolt to **something.** That something is what this file is
about: the table, frame, or base the whole cell sits on.

People often treat this as an afterthought. Then their precise robot moves
precisely... onto a wobbling table, and nothing is precise any more.

## Why mounting matters

When the arm moves, it pushes on its base. A big arm flinging a heavy
payload generates **reaction forces** — sometimes hundreds of Newtons. If
the base isn't stiff enough, three bad things happen:

1. **Vibration.** The base wobbles. The arm wobbles. The camera wobbles.
   Precision drops.
2. **Drift.** A flexing base means the arm's "zero" position moves around.
   Calibration goes stale.
3. **Failure.** Loose bolts, cracked welds, tipping over. Sometimes within
   the first week.

A common rule of thumb in robotics: **the base should be at least 10
times stiffer than the arm itself,** and weigh at least as much as the
arm's max payload moved at its full reach.

## The main mounting options

### Heavy steel table or welded steel frame

A thick steel plate (15–25 mm) on a steel frame, bolted to the floor.

- **Best for:** industrial production. Permanent installs. Anything that
  runs 24/7 with heavy payloads.
- **Downside:** heavy, immobile, expensive. Needs a forklift to install.

### Aluminum extrusion frame (80/20, Misumi, Bosch Rexroth)

T-slot aluminum profiles bolted into a custom frame. Modular, easy to
modify.

- **Best for:** prototypes, research cells, small production. Lightweight
  cobots up to ~10 kg payload. Education labs.
- **Downside:** less stiff than steel. Joints loosen over time if not
  torqued correctly. Not suitable for big industrial arms.
- **Popular brands:** 80/20 Inc., Misumi (Japan), Bosch Rexroth, Item.

### Regular workbench

Just a sturdy carpenter's bench.

- **Best for:** the cheapest possible hobby setup. myCobot 280 demos. The
  first month of a research project.
- **Downside:** wobbles. Not really suitable for anything precise. Don't
  bolt a 5 kg-payload cobot to a Home Depot folding table.

### Mobile cart

A wheeled cart (usually aluminum extrusion + casters), so the cell can
be moved around.

- **Best for:** demos, shows, classrooms, multi-station rotation.
- **Downside:** wheels add flex. Brake the wheels before running. Always
  level the cart with adjustable feet.

### Wall or ceiling mount

The arm hangs from above or sticks out from a wall.

- **Best for:** when floor space is tight. Pick-and-place from above a
  conveyor. Inverted arms in factories.
- **Downside:** more complex install. Reaction forces pull on the
  mounting structure differently. Not all arms are rated for inverted
  mounting — **always check the spec**.

### Mobile robot base

The arm sits on a wheeled mobile robot (an AMR — autonomous mobile robot).

- **Best for:** warehouse pick-and-place, mobile manipulation research,
  service robotics.
- **Downside:** much more complex. Adds a whole new vehicle, battery,
  navigation system. Topic for a different doc.

## What to check when picking a mounting solution

| Check | What to look for |
|-------|------------------|
| **Stiffness** | The base flex under load should be a small fraction of your repeatability target. (If repeatability is 0.1 mm, base flex must be a few µm.) |
| **Weight** | A heavy base damps vibration. Heavier is better, up to a limit. |
| **Footprint** | Match against the workspace dimensions from Layer 1. |
| **Access** | Can a person reach the e-stop? Can a technician open the cabinet underneath? Can you walk around the cell? |
| **Floor mounting** | Bolted to a concrete floor? Sitting on a rubber mat? Wheels? |
| **Level** | Is the floor flat? An out-of-level arm has accumulating drift across its workspace. |
| **Reaction forces** | Does your arm vendor publish max reaction force / torque? Frame must handle them with a safety factor. |
| **Service room above** | Some arms need overhead clearance for installation cranes. Check the install manual. |

## Common combinations

| Project type | Mount |
|--------------|-------|
| myCobot 280 hobby demo | Workbench or small aluminum extrusion frame. |
| UR5e research lab | Aluminum extrusion cart with brakes, or a 1m × 1m welded steel table. |
| UR10e production cell | Heavy steel frame, bolted to concrete. Optional fenced safety enclosure. |
| Large industrial arm (Fanuc M-20, KUKA KR16) | Welded steel base. Often anchored into the floor with anchor bolts. |
| Mobile pick robot (warehouse) | Custom AMR base from MiR, Fetch, OTTO, or custom build. |

## Vibration: a few words

Stiff mounting is your first defense. If you still have vibration:

- **Vibration-damping feet** — rubber feet or polymer pads under the legs.
- **Mass damping** — bolt a heavy steel slab to the base.
- **Active isolation** — air-bearing tables, usually only in metrology
  labs.

In a normal cobot cell, the first two are enough.

## Output of this file — your mount choice

Write down:

```
Mount type:              workbench / aluminum extrusion / welded steel / other
Base material:           ___
Base dimensions:         ___ × ___ × ___ mm
Floor anchored?:         yes / no
Approx weight:           ___ kg
Vibration damping?:      none / rubber feet / mass / active
Wheels?:                 yes / no
Cost (incl. install):    ___
```

## Common mistakes

1. **Skipping the math on stiffness.** "It looks heavy enough" is not an
   answer. Cobot vendors publish reaction forces — use them.
2. **Forgetting to level the base.** A 1° tilt across a 1 m workspace is
   millimetres of drift.
3. **Bolting to a hollow table.** The bolts pull through, the arm tilts.
4. **Mobile cart without brakes.** The cell drifts during operation. The
   arm hits things.
5. **Not leaving access for service.** A great base that buries the
   controller under it is a maintenance nightmare.

## What's next

The arm is mounted on something solid. Next: how do you power it?

→ Next: [actuation-and-power-systems.md](actuation-and-power-systems.md)
