# Cable Management

The arm moves. Cables don't like to move. That's the whole problem.

A cable that's fine on a desk PC will crack, short, or rip free in
weeks on a robot. So a real cell has **cable management** — chains,
conduits, clamps, and labels that keep the cables alive.

## Why it matters

A cable on a moving arm goes through:

1. **Bending** at every joint motion — conductors crack over time.
2. **Pulling** if not anchored — connectors pop out, wires break.
3. **Twisting** as joints rotate — most cables hate this.

Failures look like: random sensor dropouts, sudden motor faults, and in
the worst case a short and fire risk. A broken wire inside a drag chain
can take a day to find.

## The components

### Cable carriers (drag chains)

A plastic or steel chain the cable lives inside. Bends at a fixed
**bend radius**, doesn't twist, slides as the arm extends.

- **Igus E-chain** — dominant brand.
- **Igus Triflex R** — special chain for the *third axis* of an arm
  (the one that twists). Wraps around the arm.
- Alternatives: Tsubaki, Murr, KabelSchlepp.

### Continuous-flex cable

Cable rated for high bend cycles in a chain. Fine stranded conductors,
special jacket.

- **Igus chainflex** — sold to match Igus chains.
- **Lapp Ölflex FD, Helukabel, Belden** — alternatives.

Office PVC cable cracks in weeks. Always pick cable with a published
flex-cycle rating (e.g. "10 million bends at 50 mm radius").

### Strain relief

Anchors that stop tugs from reaching the connector.

- **Cable glands** at enclosure entries.
- **Strain relief boots** at connectors.
- **P-clips / cable ties** clamping the cable to the frame.

Anchor every cable at least twice between its ends.

### Service loops

A loop of slack near a moving joint. The arm extends → the loop
straightens; the arm retracts → it re-forms. Free, simple, works — as
long as the loop is bigger than the cable's minimum bend radius.

### Conduits and spiral wrap

Plastic tubing or wrap to protect from cuts, abrasion, oil. Use
**flexible split conduit**, **spiral wrap**, or **cable sleeve**.
Brands: Adaptaflex, Igus, Murr.

### Slip rings

Pass signals through an endlessly rotating joint without twisting
cables. Brushes (mechanical) or non-contact (inductive). Brands:
Moog, Schleifring, Mercotac. Rare on arm joints (limited rotation);
common on turntables and AMR bases.

### Cable trays and ducts

Channels under the table for static cables. Keeps power, signal, and
safety separated and labelled. Brands: Panduit, Hellermann Tyton.

## A typical cobot cell

1. **Wall → controller** — heavy static power cable, conduit, gland
   into the cabinet.
2. **Controller → arm base** — vendor cable bundle. Static. Clamped so
   it can't be stepped on.
3. **Controller → PC / network** — static Ethernet in a duct.
4. **Eye-in-hand camera** — USB3 along the arm in an Igus Triflex,
   secured to each link.
5. **Eye-to-hand camera** — static USB3 / GigE down a tripod, in
   spiral wrap.

Bigger cells add drag chains for linear axes and dedicated channels
for safety wiring.

## What to check

| Check | Why |
|-------|-----|
| **Bend radius** of the cable, in mm | Stay above it or the cable cracks. |
| **Bend-cycle rating** | Match the arm's expected lifetime cycles. |
| **EMI shielding** | Motor cables radiate noise into nearby signal cables. |
| **Power / signal separation** | Separate trays or chains where possible. |
| **Service-loop length** | Bigger than the bend radius. |
| **Connector orientation** | Facing away from snag points. |
| **Labels** | Every cable end. Always. |
| **Wiring diagram** | On paper if nothing else. |

## Output of this file — your cable plan

```
Cables that move with the arm:
  - Camera:        USB3, Igus chainflex CF98, in Igus Triflex
  - F/T sensor:    ___
  - Gripper:       ___

Static cables:
  - Mains in:      Lapp Ölflex H07RN-F, 4 mm²
  - Controller→PC: Cat6 shielded, in cable duct
  - PLC I/O:       ___

Drag chain brand:   ___
Service loops at:   ___
Cable labels?:      yes (every end)
Wiring diagram?:    yes (PDF / paper)
```

## Common mistakes

1. **Office cable on a moving arm.** Cracks fast.
2. **Bend radius too tight.** Cable cracks inside the chain.
3. **No service loop.** Arm extends, connector rips off.
4. **Power and signal in the same chain.** Power noise couples into
   signal.
5. **No cable labels.** A year later, nobody knows what each is for.
6. **Twisting cables instead of wrapping them.** Use a Triflex chain
   or a slip ring.
7. **No strain relief at the controller.** A tug yanks pins out.

## What's next

The wires won't break. Now: what makes the robot **stop** when a human
gets in the way?

→ Next: [09-safety-equipment.md](09-safety-equipment.md)
