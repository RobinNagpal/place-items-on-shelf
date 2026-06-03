# 02 — Choosing The Arm And The Gripper

> **Who this is for:** You have a filled-in task spec from
> [Layer 01](01-understanding-the-problem.md). Now you need to pick a real arm
> (and end-effector) that can do that task. Still no code in this doc — just
> matching requirements to hardware.

## Why this is "Layer 2"

Layer 1 told you *what* the robot must do. Layer 2 turns those requirements
into a shopping list: **which arm** and **which end-effector** can actually
execute the task within your budget and constraints.

You do not "pick the arm first and figure out the task later." You also do not
pick the arm in isolation from the gripper — a great arm with the wrong
gripper fails just as badly as the wrong arm.

## A note before you pick hardware: software is not a separate phase

> "Do we also need to figure out the software requirements? In parallel? The
> reason being: if the task is 'pick up a colored product', we should pick an
> arm that's *designed* for that and already has the AI feature."

That intuition is correct, and important enough to call out at the top of this
layer rather than save it for later.

Modern robotic arms exist on a spectrum:

- **"Dumb" arms** — they move precisely to coordinates you tell them, and
  nothing else. You build the perception, planning, and "what to do next"
  software yourself (or pull it from ROS / MoveIt / OpenCV etc.).
- **"AI-included" arms / platforms** — they ship with vision, object detection,
  and sometimes a learned policy that lets them grasp varied objects out of
  the box. You spend less time on perception code and more time on the task
  description ("pick the red cup").

Which side of the spectrum is right for you depends on Layer 1's task spec:

- If the task is **repeatable, structured, known objects** ("pick a part from a
  fixed jig and place it in a fixed bin") → a dumb arm + classical software is
  cheaper and more reliable. This is the path our `place-items-on-shelf`
  project takes with the myCobot 280 + MoveIt + classical perception.
- If the task is **varied or unstructured** ("pick whatever-colored item the
  user points at") → strongly consider an arm that already bundles AI
  perception. Re-implementing that stack yourself is a project, not a feature.

The next layer (Layer 03) will cover *what software you need* in detail. For
now: keep "what AI / perception is included?" as one column in your hardware
comparison table. Don't treat it as an afterthought.

## How to choose the arm: the criteria

For each candidate arm, match it against the numbers in your Layer 1 task
spec:

| Criterion | What it means | How to read it from the spec |
|-----------|---------------|------------------------------|
| **Degrees of Freedom (DOF)** | Independent joint axes the arm can move. More = more flexible orientations. | 4-DOF is enough for "approach top-down, grip, lift" (SCARA-style). 6-DOF can reach any pose in its workspace. 7-DOF adds redundancy for cluttered scenes / human-safe motion. |
| **Payload** | Max weight the arm can move (object + gripper combined). | Use the object weight from "Object(s) handled" + the gripper weight. Add a safety factor of ~2×. |
| **Reach** | Distance from base to fully-extended end-effector. | Match against "Workspace dimensions". |
| **Repeatability** | How exactly the arm returns to the same point twice. | Match against "Precision required" — but note repeatability is *not* absolute accuracy; see the glossary entry in `robots/mycobot-280-pi/docs/reference/glossary.md`. |
| **Speed (max joint velocity, cycle time)** | How fast the arm can complete a typical move. | Match against "Cycle time". |
| **Safety class / collaborative?** | Whether it can safely share workspace with humans (ISO 10218, ISO/TS 15066). | If "Humans nearby? Yes" in your spec, a cobot or rated industrial arm with safety scanners is mandatory. |
| **Software / SDK** | What you talk to the arm with — ROS 2, vendor SDK, web API, none. | Strongly tied to Layer 03. If you want to write code, you need an open interface. |
| **AI / perception included?** | Does it ship with a camera, object detector, grasp policy? | Cuts your software work dramatically when the task allows it. |
| **Budget** | Total cost incl. controller, software licenses, accessories. | A hard filter — drops most options on most projects. |

A rough rule of thumb: **filter on budget and safety class first** (they
eliminate ~70% of options), then on reach + payload + repeatability (the
"physical fit"), then on software + AI features (which mostly affects
*development cost*, not whether the arm physically can do the task).

## A market map of common, popular arms (early 2026)

This is not an exhaustive list — it's the "names you will keep hearing"
grouped by the bucket of projects they typically end up on. Prices are very
rough and exclude controller, training, and accessories.

### Hobby / education / desktop research (≤ $5k)

For learning, prototyping, classroom labs, and small-scale demos. These are
what most ROS tutorials use.

- **Elephant Robotics myCobot 280 Pi** — 6-DOF, ~250 g payload, ~280 mm reach,
  Raspberry-Pi-based controller, open ROS 2 packages. **What this repo
  targets.**
- **Elephant Robotics myCobot 320** — bigger sibling: ~1 kg payload, ~320 mm
  reach. Same software story.
- **Niryo Ned2** — 6-DOF educational cobot, ~300 g payload, Python / Blockly
  / ROS-friendly. Common in schools.
- **Annin Robotics AR4 / AR5** — 6-DOF open-hardware desktop arm, ~$2-3k DIY.
  Strong community.
- **Dobot Magician / MG400** — 4-DOF SCARA-style desktop arm. Simple,
  reliable, less flexible orientation-wise.

### Mid-range industrial / cobot research (~$10k–$50k)

The "workhorse" tier: heavy enough to do real work, gentle enough for
research labs, mature software ecosystems.

- **Universal Robots UR3e / UR5e / UR10e / UR16e / UR20** — 6-DOF cobots,
  ~3–20 kg payload, ~500–1750 mm reach. Largest installed base in the
  collaborative-robot market by a wide margin
  ([EVS, 2026](https://www.evsint.com/top-collaborative-robot-brands/)).
  The "default" cobot pick.
- **Franka Robotics Production 3 (FR3)** (successor to the original Franka
  Emika Panda) — 7-DOF, ~3 kg payload, torque-sensing on every joint. Hugely
  popular in research because of its sensitivity.
- **Kinova Gen3** — 7-DOF, ~4 kg payload, ROS 2 + Python SDKs. Lightweight,
  used in medical and lab settings.
- **Doosan Robotics M / H series** — 6-DOF cobots, ~5–25 kg payload. A
  fast-growing cobot brand globally.
- **Techman Robot TM5 / TM12 / TM25** — 6-DOF cobots with an integrated
  camera and vision SDK (TMflow). Closer to the "AI-included" end of the
  spectrum than most cobots.

### Industrial / production (≥ $30k, often ≥ $100k once integrated)

For real factory work — high payload, high duty cycle, certified safety.

- **FANUC LR Mate / CRX series** — yellow industrial arms (LR Mate) and green
  cobots (CRX). FANUC is one of the top-three industrial-robot makers
  worldwide.
- **ABB IRB / GoFa / YuMi** — IRB are heavy industrial; GoFa is a cobot; YuMi
  is a dual-arm "human-collaborative" assembly robot.
- **KUKA KR series / LBR iiwa** — KR for industrial; LBR iiwa is the 7-DOF
  torque-sensing cobot popular in research and surgical adjacents.
- **Yaskawa Motoman GP / HC series** — GP industrial, HC cobot.
- **Kawasaki RS / duAro** — RS industrial, duAro dual-arm cobot.

The "big four" of industrial robotics — FANUC, ABB, KUKA, Yaskawa — dominate
the high end of the market. If your task is "production line, large payload,
many years of duty," you will almost certainly end up with one of them.

### "AI-included" arms and platforms

These bundle vision + a learned manipulation policy so you describe the task
at a higher level instead of writing perception/planning code from scratch.

- **Techman TM cobots** — built-in eye-in-hand camera + TMflow vision SDK
  (classical CV + light ML). Lowest-effort entry to "see, grasp, place" in
  the cobot tier.
- **Standard Bots RO1** — 6-DOF cobot bundled with an "operator" interface
  and increasingly AI-driven task setup.
- **Mech-Mind / Photoneo bin-picking systems** — these are vision + software
  systems you bolt onto any of the above arms; together they form an
  "AI-included" stack.

## How to choose the gripper (end-effector)

The gripper is the part that actually touches the object. Its choice depends
almost entirely on Object Q2 from Layer 1 ("Shape, Size, Weight, Material,
Fragility").

### The main gripper families

- **Parallel jaw (two-finger)** — two fingers move toward/away from each
  other. The default for boxes, cylinders, rigid parts. Cheap, predictable.
- **Three-finger / multi-finger adaptive** — fingers wrap around irregular
  shapes. Better for objects without a flat side; pricier.
- **Vacuum / suction** — a cup grabs flat / smooth surfaces by pulling a
  vacuum. Excellent for boxes, sheets of paper, glass, smooth product.
  Requires a pump.
- **Soft / compliant** — silicone fingers that gently conform to the object.
  Used for delicate or oddly-shaped items (fruit, baked goods, tissue
  samples).
- **Magnetic** — for ferrous metal parts only. Fast and strong.
- **Needle gripper** — needles dart into porous material (foam, textile).
  Niche but unbeatable for fabrics.
- **Custom / task-specific** — screwdriver, welder, paint sprayer, syringe,
  pipette. Whenever a generic gripper can't do the job, you mount the tool
  itself.

### Popular gripper manufacturers (early 2026)

These names show up across most cobot and industrial integrations
([Standard Bots, 2026](https://standardbots.com/blog/the-top-5-robot-gripper-manufacturers-for-any-budget),
[Market Research Future, 2026](https://www.marketresearchfuture.com/reports/robotic-end-effector-market/companies)):

- **Robotiq** (Canada) — adaptive parallel grippers (2F-85, 2F-140, Hand-E)
  and 3-finger grippers. The 2F-85 is a de facto industry standard for cobot
  pick-and-place.
- **OnRobot** (Denmark) — broad modular range: RG2, RG6 (parallel),
  3FG15 (3-finger), VG10/VGC10 (vacuum), VGP20 (vacuum array), Soft Gripper.
- **Schmalz** (Germany) — the vacuum specialist; everything from small cups
  to multi-zone vacuum arrays for full-pallet handling.
- **Piab** (Sweden) — vacuum technology, especially for food and pharma.
- **SCHUNK** (Germany) — broad industrial range, including precision parallel
  grippers and force/torque sensors.
- **Festo** — pneumatic specialty grippers, including their well-known
  bio-inspired designs.
- **Soft Robotics Inc.** — silicone fingers for food and produce handling.
- **Shadow Robot Company** (UK) — highly anthropomorphic dexterous hand,
  research-grade.
- **RightHand Robotics** — bin-picking-focused gripper + vision stack.
- **Barrett Technology** — BarrettHand, three-finger dexterous research hand.
- **Sake Robotics EZGripper** — low-cost adaptive gripper used in many ROS
  projects.

The grippers you'll see in most ROS / cobot tutorials are the **Robotiq 2F-85
or 2F-140**, and **OnRobot RG2 / VG10**. Start there unless your task
specifically rules them out.

### Tip: the gripper drives the mounting interface

Each arm has a flange at the wrist with a specific bolt pattern and an
electrical / pneumatic interface. Most major arms publish an "ISO 9409-1-50"
flange that fits the popular cobot grippers above — but always cross-check the
arm's wrist spec against the gripper's mounting kit before buying.

## How to use this layer (the output)

For each candidate, build a table like this and fill it in:

```
                     Option A    Option B    Option C
Arm model:           ___         ___         ___
DOF:                 ___         ___         ___
Payload (kg):        ___         ___         ___
Reach (mm):          ___         ___         ___
Repeatability (mm):  ___         ___         ___
Safety class:        ___         ___         ___
SDK / API:           ___         ___         ___
AI included?:        ___         ___         ___
Arm price:           ___         ___         ___

Gripper model:       ___         ___         ___
Gripper type:        ___         ___         ___
Compatible flange:   ___         ___         ___
Gripper price:       ___         ___         ___

Meets task spec?     yes / no    yes / no    yes / no
Total cost:          ___         ___         ___
```

The narrowed list (usually 2–3 rows) becomes the input for Layer 03 (software
and AI capabilities), where you ask "given this hardware, what do I need to
build vs. what's already there?".

## Common mistakes at this layer

1. **Buying the arm before the gripper.** You discover the cobot's wrist
   doesn't have the right pneumatic line and now you can't use the vacuum
   gripper you needed.
2. **Confusing repeatability with accuracy.** "0.1 mm repeatable" only means
   "returns to the same taught point" — not "lands exactly where you specify
   in world coordinates". For absolute positioning you also need calibration.
3. **Underspecifying payload.** Remember to include the gripper, the wiring,
   *and* the object. Many gripper specs alone weigh 1 kg.
4. **Ignoring the controller.** The arm controller can cost as much as the
   arm. Cobot prices usually include it; industrial-arm prices often do not.
5. **Treating AI as "I'll add it later".** If the project genuinely needs
   "pick whatever the user points at", retro-fitting that onto a dumb arm is
   a multi-month engineering effort. Pick the right tier of platform up
   front.
6. **Picking based on hype, not spec.** Hot humanoids and foundation-model
   demos are exciting; that does not mean one of them is the right pick for
   *your* spec. Use Layer 1's filter first.

## "Are there libraries or frameworks for this layer?"

Not really — this is still mostly a procurement and spec-matching step. A few
things genuinely help:

- **Manufacturer comparison pages** like the EVS / Standard Bots / Robotics
  Center round-ups (see Sources below) for current prices and feature
  matrices.
- **`robotsguide.com`** and **`robots.ieee.org`** for browsing categories.
- **Distributor configurators** (RobotShop, Generation Robots) — handy for
  bundling a specific arm + gripper + accessories with known compatibility.

## What's next

Once you have a shortlist of arm + gripper combinations that physically meet
your task spec, Layer 03 will look at the **software side**: what perception,
planning, and control stack each combination implies — and how much of that
work the platform already does for you.

## Sources

- [Top 10 Collaborative Robot Brands by Market Share 2026 — EVS](https://www.evsint.com/top-collaborative-robot-brands/)
- [Top 10 Industrial Robot Manufacturers by Market Share 2026 — EVS](https://www.evsint.com/top-industrial-robot-manufacturers/)
- [The top 5 robot gripper manufacturers for any budget — Standard Bots](https://standardbots.com/blog/the-top-5-robot-gripper-manufacturers-for-any-budget)
- [Robotic End Effector Companies — Market Research Future](https://www.marketresearchfuture.com/reports/robotic-end-effector-market/companies)
- [Robot Gripper Guide 2026 — Silicon Valley Robotics Center](https://www.roboticscenter.ai/blog/robot-gripper-guide)
