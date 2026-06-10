# Additional Requirements To Consider

The seven questions in
[01-understanding-the-problem.md](01-understanding-the-problem.md) cover the
basics. But many real projects fail in the first month because of things
that didn't show up in those answers.

This doc lists the **questions people skip in the first pass.** Go through
them once. Most will be "doesn't apply to us." A few will save the project.

## 1. How often does the task run? (Duty cycle)

Cycle time tells you how fast one task is. Duty cycle tells you how often
the robot is doing tasks at all.

- One task per day, on demand? → A hobby setup is fine.
- One task every few minutes, 8 hours a day? → You need a reliable cobot
  with good cooling and a maintenance plan.
- One task every few seconds, 24 hours a day? → You need an industrial arm,
  redundant power, and serious maintenance.

The same task on the same hardware fails very differently if it runs once
a week vs. once a second. Joints wear, motors heat up, cables flex
millions of times.

## 2. How long must the system last? (Lifespan)

- A research demo? A few months.
- A pilot in a factory? A year or two.
- A production line? Five to ten years, with parts swapped along the way.

Lifespan affects:

- The grade of arm (hobby arms aren't built for years of continuous use).
- The cabling (cheap cable cracks after a few hundred thousand flexes).
- The spare parts story (does the vendor still sell parts in five years?).

## 3. Who operates it day-to-day?

- A trained engineer? They can use a teach pendant and read logs.
- A factory worker who has not touched a robot before? They need simple
  buttons and clear status lights.
- Nobody — the robot runs itself? Then you need remote monitoring and
  alerts when something is wrong.

The answer changes what kind of **operator interface** you'll need (more on
that in Layer 2).

## 4. Who maintains it when it breaks?

Hardware breaks. Robots get hit. Cables snap. Plan ahead:

- Is the vendor's support good in your country? Can you call somebody?
- Do you have spare parts on a shelf, or do you order them when needed
  (long wait)?
- Can a regular technician fix small problems, or does every fix need a
  specialist?

The fanciest arm in the world is useless if it sits broken for two months
waiting for a part.

## 5. What other systems must it talk to?

A robot is almost never standalone. List what it must connect to:

- **Sensors and machines around it** — cameras, conveyors, weighing
  scales, barcode readers.
- **Higher-level systems** — a factory PLC, a warehouse management
  system, a cloud database.
- **User-facing systems** — a web dashboard, a phone app, a Slack bot.

For each connection, you'll later care about the protocol (Ethernet,
EtherCAT, Modbus, REST API, MQTT) — but at this layer, just *list* the
connections. You don't need to pick protocols yet.

## 6. What records must it keep? (Logging / data)

- Does someone need to prove the robot did the right thing? (regulated
  industries: food, medical, automotive)
- Does the data need to be kept for years? Months? Just for debugging?
- Do you need to log every motion? Just the failures? Every video frame?

If "yes, we must log everything" is the answer, you'll need bigger
storage, possibly a database, and a way to back it up. Decide that early —
adding logging later usually means rewriting the task code.

## 7. What happens when the task fails?

Real robots fail sometimes. Decide ahead of time what they should do:

- **Stop and call a human?** Simple. Requires a person within earshot.
- **Retry the task?** How many times before giving up?
- **Skip the current object and move on?** Fine for sorting tasks; bad for
  critical assembly.
- **Reset everything to a safe pose?** Always sensible as a fallback.

If you don't decide this now, the robot's first failure becomes a
discovery process during a customer demo.

## 8. Is there a regulator who cares?

Beyond safety standards (ISO 10218 etc.), some industries have their own
rules:

- **Food and beverage** — surfaces must be wash-down rated. Grease can't
  drip onto food. (FDA in the US.)
- **Medical / pharma** — sterilisable parts, traceability of every motion.
  (GMP, FDA.)
- **Automotive** — IATF 16949 quality standards.
- **Aerospace** — AS9100.
- **Electrical safety** — UL (US), CE (Europe), CCC (China).

Pick a target market early. Retrofitting a system for a regulator after the
fact is expensive and sometimes impossible.

## 9. When does it need to be running? (Timeline)

- Demo in two weeks? You can't build custom hardware; buy off the shelf.
- Production in six months? You have time to integrate but not to
  custom-engineer.
- Production in two years? You can co-design with a vendor, ask for
  custom features.

Timeline narrows your hardware choices as much as budget does.

## 10. One cell or many? (Scale)

Will you build one robot cell and stop there? Or roll out 50 of them?

- **One cell** — Pick whatever works best. Custom is fine.
- **Many cells** — Cost per unit matters. Spare parts must be easy.
  Software must be maintainable across versions. Operator training must
  scale.

Many of the "right" choices for a one-off prototype are wrong choices for
a fleet. Decide early.

## 11. Are there variations the robot must handle?

- **Different objects in the same task?** ("Pick any of the 12 SKUs on this
  shelf.")
- **Same object but different positions?** ("The cup might be anywhere on a
  1 m² table.")
- **Same object but different orientations?** ("The cup might be lying on
  its side.")
- **Lighting changes?** (Day shift sunlight vs. night shift fluorescents.)

The more variation, the more sensors, software, and AI you'll likely
need. A task with zero variation can sometimes be done without any
sensors at all.

## 12. Training and acceptance — how will you prove it works?

Before the system is "done," somebody has to agree it works:

- Who runs the acceptance test? You? The customer?
- What's the pass criterion? ("95% pick rate over 1,000 attempts." "No
  crashes for 48 hours.")
- How will operators be trained?
- What documentation must the system ship with?

If you've never thought about acceptance criteria, search for "Site
Acceptance Test (SAT)" and "Factory Acceptance Test (FAT)" — they are
standard names for this step in industry.

## 13. Security

Not safety — *security*, against people doing bad things on purpose:

- Is the robot on a network? Can someone outside the factory reach it?
- Are the controllers password-protected with a real password?
- Does the software get security updates from the vendor?

For most hobby and research setups, this is "not a concern." For a
production robot connected to the internet, it's a real worry.

## A second checklist (in addition to the first one)

Copy this and answer it. Most lines will be "N/A" — that's the point. The
ones that aren't N/A are the ones that will bite you later.

```
Duty cycle:                          ___ tasks/hour, ___ hours/day
Expected lifespan:                   ___ years
Operator profile:                    engineer / factory worker / unattended
Maintenance plan:                    in-house / vendor / both
Systems to connect to:               __________________________________
Logging required?:                   yes / no    Retention: ___
Failure behavior:                    stop / retry / skip / reset
Regulators that apply:               none / FDA / GMP / IATF / AS9100 / other
Deadline for live:                   ___ weeks / months
Scale:                               one cell / a few / a fleet
Variations to handle:                _________________________________
Acceptance test plan:                _________________________________
Network exposure / security:         standalone / LAN / internet
```

## Common mistakes at this step

1. **Treating duty cycle and cycle time as the same thing.** They aren't.
   A 5-second cycle that runs 50 times a day is very different from one
   that runs 50,000 times a day.
2. **Forgetting who has to operate it.** A teach pendant is fine for an
   engineer and a nightmare for a tired factory worker.
3. **Underestimating logging.** "We can add logs later" — yes, but you'll
   pay for it.
4. **Promising a deadline before listing the regulators.** A 6-month
   timeline becomes a 2-year timeline when "oh by the way, FDA" gets
   added later.
5. **Building one perfect cell, then trying to copy it 50 times.** The
   second copy reveals 100 things you didn't write down.

## What you finish with

A second short document — or just an extension of the one from the
previous file. Stapled together, these two answer the question **"what is
this robot supposed to do, in enough detail that I can pick hardware?"**

Take both into Layer 2.

→ Next: [`../02-hardware-selection/`](../02-hardware-selection/) — picking
all the hardware, one piece at a time.
