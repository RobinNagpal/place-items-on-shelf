# Gripper

The gripper is the hand. It's what touches the object. Without a gripper,
the arm is just an expensive pointing stick.

Your gripper choice is decided almost entirely by the **object** —
specifically by its shape, weight, material, and how fragile it is. Go
back to Layer-1, question 2, before reading further.

## The main gripper families

Each family is good for some objects and useless for others. Pick the
family first, then the specific model.

### Parallel jaw (two-finger)

Two fingers move toward each other and pinch the object. The default
choice for boxes, cylinders, and rigid parts.

- Cheap, simple, very reliable.
- Bad at irregular shapes (bananas, fabric, anything without a flat side).
- Most common gripper in robotics, period.

**Pick this when:** the object has at least one pair of parallel sides
(boxes, blocks, cylinders, screw heads).

### Three-finger / multi-finger adaptive

Three or more fingers wrap around an object. Adapt to the shape better
than parallel jaws.

- Better for irregular shapes.
- More moving parts, more cost, more software effort.

**Pick this when:** the object is round, irregular, or you need to grip
many different shapes with one gripper.

### Vacuum / suction

A cup pulls a vacuum against a flat-ish surface. Strong, fast, very common
in logistics.

- Excellent for boxes, sheets, smooth product (cans, bottles, glass).
- Needs a vacuum pump or compressed air.
- Bad for porous (cardboard with holes), rough, or wet surfaces.

**Pick this when:** the object has a flat or smooth face. Especially for
parcel handling, food packaging, sheet-metal pick-up.

### Soft / compliant

Silicone or rubber fingers that gently conform to the object.

- Excellent for delicate items (fruit, baked goods, tissue samples).
- Lower payload than rigid grippers.
- Not as repeatable for precise placement.

**Pick this when:** "must not damage the object" is the top constraint.

### Magnetic

A magnet — sometimes electromagnet, sometimes permanent with a release
mechanism — picks up ferrous metal parts.

- Fast and strong.
- Only works on iron / steel. Useless for everything else.

**Pick this when:** all the parts are made of magnetic metal.

### Needle gripper

Needles dart into porous material (foam, fabric, mesh) and hold by
friction.

- Niche but unbeatable for textiles.

**Pick this when:** you're picking fabric or foam.

### Custom / task-specific tools

When no general gripper works, the "gripper" is the tool itself: a
screwdriver, a welding torch, a paint sprayer, a syringe, a pipette.

**Pick this when:** the task isn't "pick and place" at all.

## Popular gripper makers

These names show up across most cobot and industrial integrations.

### Robotiq (Canada)

The de facto cobot gripper brand. Their **2F-85** parallel gripper is the
single most common cobot end-effector in the world.

- **2F-85, 2F-140** — parallel jaw. The 85 mm-stroke and 140 mm-stroke
  versions. Industry standard.
- **Hand-E** — precise small parallel gripper for assembly.
- **3-Finger Adaptive** — three fingers, multiple grip modes.
- **EPick / AirPick** — vacuum.

**Best for:** cobot pick-and-place, UR cobots especially.

### OnRobot (Denmark)

Broad modular range — many gripper types under one brand.

- **RG2, RG6** — parallel jaw, two stroke sizes.
- **3FG15** — three-finger.
- **VG10, VGC10, VGP20** — vacuum grippers and vacuum arrays.
- **Soft Gripper** — silicone for food.

**Best for:** projects that want to swap gripper types without changing
the wrist interface.

### Schmalz (Germany)

The vacuum specialist. Founded 1910. Makes everything from a single suction
cup to full-pallet vacuum arrays.

**Best for:** vacuum applications, especially large-format (sheet metal,
cardboard boxes, full pallets).

### Piab (Sweden)

Another vacuum specialist, strong in food and pharma.

**Best for:** food handling, pharmaceutical pick-and-place.

### SCHUNK (Germany)

Broad industrial range — precise parallel grippers, force sensors,
quick-change tool couplers.

**Best for:** industrial-grade assembly and machine tending.

### Festo (Germany)

Pneumatic gripper specialist. Known for unusual bio-inspired designs.

**Best for:** projects that already have an air supply and want pneumatic
gripping.

### Soft Robotics Inc. (US)

Silicone "starfish"-style fingers for food and produce.

**Best for:** strawberries, bakery, fragile produce.

### Shadow Robot Company (UK)

The Shadow Hand — a highly human-like dexterous five-finger hand.
Research-grade, expensive.

**Best for:** research into dexterous manipulation. Not for production.

### RightHand Robotics (US)

A combined gripper + vision + grasp-policy stack for bin picking.

**Best for:** e-commerce order picking.

### Sake Robotics EZGripper

Cheap adaptive gripper used in many ROS research projects.

**Best for:** academic ROS demos on a budget.

### Barrett Technology — BarrettHand

Three-finger dexterous research hand.

**Best for:** research into multi-finger grasping.

## How to match the gripper to the arm

A gripper has to physically bolt to the arm's wrist. Two things must
match:

1. **The flange (bolt pattern).** Most cobots and many industrial arms use
   the **ISO 9409-1-50** flange. Most popular cobot grippers are sold
   with an ISO 9409 mounting kit. Always check the spec sheet.
2. **The electrical / pneumatic connection.** The gripper needs power and
   often a control signal. Some arms (UR e-series, for example) have a
   tool I/O port at the wrist; others need you to run a separate cable
   along the arm.

For vacuum grippers specifically, you also need:

- A **vacuum source** (a pump, or compressed air with a venturi).
- An air line down the arm (some arms have internal pneumatic routing,
  others don't).

## Output of this file — your gripper shortlist

For each candidate, write down:

```
Gripper model:           ___
Type:                    parallel / vacuum / soft / etc.
Stroke or cup size:      ___ mm
Payload:                 ___ kg
Compatible wrist flange: ___
Power / air supply:      ___
Price:                   ___
```

Now go back to the arm shortlist from [01-arm.md](01-arm.md) and **cross-check
compatibility**. Some pairs that look good independently won't actually
bolt together.

> Many arm vendors also sell or co-market a specific gripper. See
> [`arm-gripper-bundles.md`](arm-gripper-bundles.md) — it lists which
> arm+gripper pairings ship together, whether the gripper is first-party
> or a partner brand, and whether the driver is included in the arm's
> SDK out of the box. Taking the bundle usually saves a couple of days
> of integration work.

## Common mistakes

1. **Picking the gripper after the arm.** They are decided together. The
   gripper changes the payload budget, the cabling story, and sometimes
   the arm choice itself.
2. **Forgetting the gripper's own weight.** A Robotiq 2F-85 weighs about
   1 kg. On a myCobot 280 with a 0.25 kg payload, that already overflows
   the arm.
3. **Choosing vacuum without checking the air supply.** "We have
   compressed air" is sometimes true, sometimes not, sometimes "yes but
   the line is in the next building."
4. **Picking a multi-finger gripper for boxes.** Overkill. A parallel jaw
   is cheaper, faster, and more reliable.

## What's next

You have an arm + gripper shortlist. The next decision is **sensors** —
how the robot sees, feels, and measures.

→ Next: [03-sensors.md](03-sensors.md)
