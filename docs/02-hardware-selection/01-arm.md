# Arm

The arm is the moving thing. It's the metal skeleton with motors at every
joint. It does not include the hand (that's the gripper, next file), the
cameras (sensors), the table it sits on (mounting), or the box that runs
it (control hardware).

This file is just about which arm to buy.

## What you check, before anything else

Match each candidate arm against the numbers in your Layer-1 task spec.
The five numbers that matter most:

- **Degrees of freedom (DOF)** — How many joints. More joints = more
  flexible poses.
  - 4 joints (SCARA) — fine for "approach from the top, grip, lift, put
    down". Cannot tilt the hand sideways.
  - 6 joints — can reach any pose in the work area. The standard pick.
  - 7 joints — adds extra wiggle room. Useful in tight spaces and around
    humans.
- **Payload** — How much weight the arm can hold at the wrist. Always
  include the gripper, the wiring, *and* the object. Add a safety factor
  of about 2×.
- **Reach** — How far the wrist can get from the base. Match against your
  workspace dimensions.
- **Repeatability** — How exactly the arm returns to the same point twice.
  Note: this is *not* the same as how exactly it goes to a specific world
  position. (That's accuracy, which is usually worse than repeatability.)
- **Safety / collaborative?** — Can the arm safely share its workspace
  with humans? If "humans nearby" is "yes" in your spec, you need a
  collaborative arm (cobot) or an industrial arm with safety scanners.

Other things to check, but lower priority for the first pass:

- **Max speed** (matters if cycle time is tight)
- **Mounting orientation** (some arms only work upright; others can hang)
- **Power requirement** (some need 230V three-phase; cobots usually 110/230V single-phase)
- **SDK / API** (ROS 2 driver? Vendor SDK? Web API? None?)
- **AI included?** (some arms ship with a camera and grasp software bundled)

A rough rule: **filter on budget and safety class first** (these kill 70%
of the options), then on reach + payload + repeatability, then on
software and AI.

## The four tiers of arms

Arms split into four buckets by price and what they're built for. Pick the
right bucket before comparing models inside it.

### Hobby / education / desktop (under $5,000)

For learning, prototyping, classroom labs, small demos. Most ROS tutorials
use one of these.

| Arm | DOF | Payload | Reach | Best for |
|-----|-----|---------|-------|----------|
| **Elephant Robotics myCobot 280 Pi** | 6 | ~0.25 kg | ~280 mm | The cheapest serious 6-DOF arm. What this repo uses. Raspberry Pi controller, open ROS 2 packages. |
| **Elephant Robotics myCobot 320** | 6 | ~1 kg | ~320 mm | The bigger sibling. Still cheap, still hobby-grade. |
| **Niryo Ned2** | 6 | ~0.3 kg | ~440 mm | School and university labs. Friendly Python and Blockly interfaces. |
| **Annin Robotics AR4 / AR5** | 6 | ~0.5–1 kg | ~600–800 mm | DIY-friendly. Open hardware. Active community. ~$2–3k as a kit. |
| **Dobot Magician / MG400** | 4 (SCARA) | ~0.5 kg | ~320 mm | Simple top-down pick-and-place. Less flexible than 6-DOF. |

**Pick these when:** you're learning, demoing, or running small lab
experiments. **Avoid for:** anything that has to run 8+ hours a day in
production.

### Mid-range industrial / cobot research ($10,000 – $50,000)

The workhorse tier. Heavy enough to do real work, gentle enough for
research labs. Big software ecosystems.

| Arm | DOF | Payload | Reach | Best for |
|-----|-----|---------|-------|----------|
| **Universal Robots UR3e / UR5e / UR10e / UR16e / UR20** | 6 | 3–20 kg | 500–1750 mm | The "default" cobot pick. Biggest installed base in the world. Huge ecosystem (UR+). |
| **Franka Robotics FR3** | 7 | ~3 kg | ~855 mm | Research darling. Torque sensors on every joint = best-in-class feel. |
| **Kinova Gen3 / Gen3 lite** | 6 or 7 | 2–4 kg | ~700–900 mm | Medical, lab, assistive use. Lightweight. Good ROS 2 support. |
| **Doosan H / M / A series** | 6 | 5–25 kg | 900–1700 mm | Fast-growing cobot brand. Strong in Asia. |
| **Techman TM5 / TM12 / TM25 / TM30** | 6 | 4–30 kg | 700–1900 mm | Built-in camera and TMflow vision SDK. Closer to "AI-included" than most cobots. |
| **Aubo i5 / i10 / i16** | 6 | 5–16 kg | 880–1750 mm | Chinese cobot brand, cheaper than UR for similar specs. |
| **JAKA Zu / S series** | 6 | 3–18 kg | 500–1300 mm | Same idea — cheaper-than-UR Chinese cobot. |
| **Elite EC / CS series** | 6 | 3–25 kg | 500–1800 mm | Same tier again. The cobot market is fragmenting fast. |

**Pick these when:** you need a real production-grade arm, you have humans
in the workspace, and you want a mature SDK to write software on.

### Industrial / production ($30,000+, often $100,000+ once integrated)

For real factory work. High payload, high duty cycle, certified safety,
designed to run for years.

| Arm | DOF | Payload | Reach | Best for |
|-----|-----|---------|-------|----------|
| **FANUC LR Mate / CRX / R-2000iC** | 4–6 | 4 kg – 250 kg | varied | LR Mate = small industrial. CRX = green cobot. Top-3 industrial robot maker worldwide. |
| **ABB IRB series / GoFa / YuMi** | 6 | 0.5 kg – 800 kg | varied | IRB = heavy industrial. GoFa = cobot. YuMi = dual-arm assembly cobot. |
| **KUKA KR series / LBR iiwa** | 6 or 7 | 3 kg – 1300 kg | varied | KR = industrial. LBR iiwa = 7-DOF torque-sensing cobot, popular in research and medical. |
| **Yaskawa Motoman GP / HC series** | 6 | 4 kg – 600 kg | varied | GP = industrial workhorse. HC = cobot. |
| **Kawasaki RS / duAro** | 6 | 3 kg – 700 kg | varied | RS = industrial. duAro = dual-arm cobot. |

The "big four" — FANUC, ABB, KUKA, Yaskawa — dominate the high end. If your
task is "production line, large payload, many years of duty", you will end
up with one of them.

**Pick these when:** the system runs 24/7, you have an integration partner
or in-house robotics engineer, and the cost of downtime is high.

### SCARA arms (a special case)

SCARA arms have a different shape — they move in a horizontal plane and
push down vertically. Faster than 6-DOF arms at top-down pick-and-place,
but they can't tilt.

| Arm | Payload | Reach | Best for |
|-----|---------|-------|----------|
| **Epson G6 / G10 / G20** | 6–20 kg | 450–1000 mm | High-speed assembly. |
| **Yamaha YK** | 4–20 kg | 350–1200 mm | Same. Strong in electronics manufacturing. |
| **IAI IXP** | 3–6 kg | 250–800 mm | Smaller-footprint SCARA. |

**Pick these when:** the task is purely top-down (no tilting), you want
speed, and you're in a fixed workspace.

## "AI-included" arms

A small but growing group of arms ships with a camera and grasp-detection
software bundled. You describe what to pick at a higher level instead of
writing perception code yourself.

- **Techman TM cobots** — eye-in-hand camera + TMflow vision SDK.
- **Standard Bots RO1** — US-market 6-DOF cobot with an "AI operator"
  interface.
- **Mech-Mind, Photoneo, RightHand Robotics bundles** — not standalone
  arms; they pair a vision + grasp stack with a UR or similar.

**Pick these when:** Layer 1 says "pick whatever the camera sees" rather
than "pick from a fixed jig." See [`../latest-robots.md`](../latest-robots.md)
for the newer humanoid + foundation-model end of this category.

## Output of this file — your arm shortlist

For each candidate, write down:

```
Arm model:         ___
DOF:               ___
Payload (kg):      ___
Reach (mm):        ___
Repeatability:     ___ mm
Safety class:      ___
SDK / API:         ___
AI included?:      yes / no
Price:             ___
```

You should end up with **2–3 candidates**, not one. The gripper choice in
the next file may rule one out (because of wrist flange or payload).

## Common mistakes

1. **Picking on DOF count alone.** 7-DOF is not "better than 6" unless your
   workspace is cluttered.
2. **Confusing repeatability with accuracy.** A 0.1 mm repeatable arm can
   still be off by 5 mm in world coordinates if it's not calibrated.
3. **Forgetting the controller cost.** Cobot prices usually include the
   controller box; industrial arm prices often don't.
4. **Buying for production, prototyping in your head.** If you've never
   built a robot system before, start in the hobby tier. You'll throw your
   first attempt away anyway.
5. **Hype-driven choices.** A foundation-model humanoid is exciting. It is
   not the right choice for "pick a coke can off a fixed shelf."

## What's next

You have an arm shortlist. The gripper choice may force a change — some
grippers don't fit some wrist flanges, and a vacuum gripper needs a
pneumatic line some arms don't have.

→ Next: [02-gripper.md](02-gripper.md)
