# Cable Management

A robotic arm moves. Cables don't like to move. That's the whole problem.

A cable that's fine for a desk PC will crack, short out, or rip free in
a few weeks on a robot. So a real robot cell has **cable management** —
all the brackets, drag chains, conduits, and clamps that keep cables
alive while the arm thrashes them around.

This is the unglamorous corner of robotics. It's also where a lot of
first systems break.

## Why this matters

A cable on a moving arm goes through three kinds of pain:

1. **Bending** — the cable bends every time the arm moves through a
   joint. A cable bent millions of times eventually cracks inside.
2. **Pulling** — if the cable isn't fixed properly, the arm tugs on it.
   Connectors pop out. Wires break inside.
3. **Twisting** — when an arm joint rotates, cables along it twist. Most
   cables tolerate this badly.

Plus: cables in the way of the arm get **caught, pinched, or snagged**.

Bad cabling causes:

- Intermittent sensor data (then the camera "randomly" disconnects).
- Sudden motor faults (the arm stops mid-task with a cryptic error).
- Live wires shorting (fire risk, in the worst case).
- A single broken wire that takes a day to find.

## The components

### Cable carriers (drag chains)

A plastic or steel chain that the cable lives inside. Bends at a fixed
**bend radius**, doesn't twist, slides smoothly when the arm extends.

Common brands:

- **Igus E-chain** — the dominant brand. Many sizes, plastic chains for
  everything.
- **Igus Triflex R** — the special chain designed for the *third axis*
  of an arm (which actually twists). Lives wrapped around the arm.
- **Tsubaki, Murr, KabelSchlepp** — alternatives.

**Best for:** any cable that has to go through a moving joint or run
along a moving axis.

### Continuous-flex cable

Cable rated for high cycles inside a drag chain. Stranded conductors
with very fine strands; special jacket material.

Common brands:

- **Igus chainflex** — sold to match Igus chains.
- **Lapp Ölflex Servo / Ölflex FD** — German industrial.
- **Helukabel** — alternative.
- **Belden** — premium, often used for Ethernet in drag chains.

A regular PVC PC cable from an office shop will crack in weeks. Always
use cable rated for the cycles you expect (suppliers publish guaranteed
flex cycles — e.g. "10 million bends at 50 mm radius").

**Best for:** any cable inside a drag chain or wrapped around a moving
arm.

### Strain relief

Clamps and grommets that anchor the cable so its weight or accidental
tugs don't reach the connector.

- **Cable glands** — threaded fittings that clamp around the cable as
  they enter an enclosure.
- **Strain relief boots / clips** — at the connector end.
- **Cable ties / P-clips** — for clamping the cable to a frame at fixed
  points.

Every cable should be anchored at least twice between its endpoints —
once near each end. This means a tug at one end doesn't reach the
other.

### Service loops

A deliberate loop of slack in the cable, near a joint that moves. When
the arm extends, the loop straightens out; when it retracts, the loop
re-forms.

A simple, free way to make a cable survive thousands of flexes — but
only if the loop is big enough to not exceed the cable's minimum bend
radius.

### Conduits and spiral wrap

Plastic tubing or wrap around the cable, to protect it from cuts,
abrasion, and oil.

- **Flexible split conduit** — like a slinky for cables.
- **Spiral cable wrap** — black plastic spiral that lets you add/remove
  cables.
- **Cable sleeve / braid** — fabric or polymer sleeve.

Common brands: **Adaptaflex, T&B, Igus, Murr**.

**Best for:** bundling messy cable groups, oily environments, places
where the cable runs through metal cutouts.

### Slip rings

A device that lets electrical signals pass through a rotating joint
without cables twisting. Has brushes (mechanical) or non-contact
(inductive / optical) versions.

Common brands: **Moog, Schleifring, Mercotac**.

**Best for:** rotating bases (turntables, AMRs) where cables would
otherwise twist endlessly. Less common on arm joints because arm joints
have limited rotation range.

### Cable trays and ducts

Fixed channels in or under the table that route static cables — the
power lines from the wall, the cables between the controller and the
IPC.

Common brands: **Panduit, Hellermann Tyton, Schneider**.

**Best for:** the static cabling. Keeps the cabinet tidy and the cables
labelled.

## How a typical cobot cell is wired

A small UR5e cell, roughly:

1. **Wall to controller** — heavy power cable in a wall conduit. Static.
   Strain relief at the controller end. Cable gland into the cabinet.
2. **Controller to arm base** — UR provides a thick cable bundle (power +
   signal) into the arm base. Static. Clamp it to the cell frame so it
   doesn't get stepped on.
3. **Controller to PC / network** — Ethernet from the controller to a
   small switch. Static. Static cable runs in a cable duct.
4. **Camera at the wrist (eye-in-hand)** — USB3 cable from camera, run
   along the arm in an Igus Triflex chain wrapped around the arm. Cable
   secured to each link with cable ties.
5. **Camera on a tripod (eye-to-hand)** — USB3 or GigE cable running down
   the tripod to the controller. Static. Cable management arm or
   spiral wrap.

A bigger cell adds drag chains for axes that extend (linear rails), more
cable groups, and dedicated channels for safety wiring.

## What to check when planning cable management

| Check | Why it matters |
|-------|---------------|
| **Bend radius** of the chosen cable, in mm | Don't bend below it. Cable cracks. |
| **Bend cycle rating** | Match against the arm's expected lifetime cycles. |
| **EMI shielding** needs | Motor cables radiate noise; signal cables nearby need shielding. |
| **Separation** | Power and signal cables in *separate* trays / chains where possible. |
| **Service loop length** | Bigger than the bend radius, smaller than the workspace allows. |
| **Connector orientation** | Connectors should face away from snag points. |
| **Labels** | Every cable end labelled. Always. |
| **Documentation** | A wiring diagram, even if it's just on paper. |

## Output of this file — your cable management plan

```
Cables that move with the arm:
  - Camera: USB3, Igus chainflex CF98, in Igus Triflex
  - F/T sensor: ___
  - Gripper signal: ___

Cables that stay still:
  - Mains in: Lapp Ölflex H07RN-F, 4 mm²
  - Controller to PC: Cat6 shielded, in cable duct
  - PLC I/O: ___

Drag chain brand / model:  ___
Service loops at:          ___
Cable labels?:             yes (every cable, every end)
Wiring diagram?:           yes (PDF / Visio / paper)
```

## Common mistakes

1. **Office cable on a moving arm.** Cracks fast. Replace with chainflex.
2. **Bend radius too tight.** Cable cracks inside the chain.
3. **No service loop.** Arm extends, cable rips out of connector.
4. **Power and signal in the same chain.** Power couples noise into the
   signal cable.
5. **No cable labels.** A year later, nobody knows what each cable does.
6. **Twisting cables instead of wrapping them.** Wrong tool for the job —
   use a Triflex chain or a slip ring.
7. **Skipping strain relief at the controller.** A pull on the cable
   yanks the connector and breaks pins.

## What's next

You have wires that won't break. Now: what makes the robot **stop** when
a human gets in the way?

→ Next: [09-safety-equipment.md](09-safety-equipment.md)
