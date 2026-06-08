# 01 — How labs automate viscous-paste weighing today

Ketchup is on the **food-and-beverage** side of the lab world. The HPLC
question is "how much 5-HMF has formed in the bottle" — 5-HMF being a
chemical marker that builds up when sugars are heated. To answer that,
the lab needs a known starting mass of ketchup. Around 5 grams,
accurate to about 1 milligram.

The unhappy truth, up front: **most food labs still weigh ketchup by
hand.** There is no widely-deployed off-the-shelf machine that
gravimetrically dispenses thick pastes to a 1 mg target. So this file
is shorter than the paracetamol version — there is less commercial
prior art to copy.

What follows is what *does* exist, and what we borrow.

## 1. Watson-Marlow peristaltic pumps + an analytical balance

A **peristaltic pump** works like fingers walking along a soft tube. A
rotor with rollers squeezes a length of silicone or Marprene tubing,
pushing whatever is inside the tube forward in a slow, steady wave. No
valves, no seals — the liquid only ever touches the inside of the
tube. That makes peristaltic pumps the standard pick in food labs:
they handle juices, syrups, sauces, and even slurries with chunks.

The classic setup pairs a Watson-Marlow pump with a Mettler analytical
balance. Sartorius sells the same idea pre-integrated as the
**Cubis II MCA** with a [Watson-Marlow 323Dud-2 head](https://shop.sartorius.com/us/p/peristaltic-pump-323dud2-for-24-wt-tubes-for-cubis-ii-lab-balance-us/YDU-31).
The setup runs in closed loop:

```
balance reports mass every 100 ms
       │
       ▼
   target mass  hit?  ──► STOP the pump
       │
       ▼ no
   keep pumping
```

Resolution is ~1 mg at a 5 g target with the right tubing diameter
and a slow-down ramp toward the end. The pump can dispense pastes up
to about **viscous fruit jam** (~10,000 cP); ketchup at room temp is
~50,000 cP, which is at or beyond the easy range. In practice food
labs warm ketchup to ~30 °C first to thin it.

Catch: a peristaltic pump cannot start and stop instantly because the
roller has to clear the tube. There is always a small **after-drip**
— a few hundred milligrams of overshoot. Working around that drip is
the actual interesting engineering problem in this case.

**What we copy:** the closed-loop pattern (mass feedback drives the
dispenser, not a timer) and the pump choice. We also copy the
"warm-the-ketchup-first" trick into the v2 plan.

## 2. Chemspeed SWING "Viscous Liquids" head

Chemspeed builds modular chemistry workstations. One of their 70+
swappable heads is specifically designed for viscous liquids — it is a
positive-displacement syringe with a heated nozzle. The host machine
moves the **balance** under the head (not the head over the balance)
on a Cartesian XYZ gantry. The system gravimetrically targets the
mass.

This is the one commercial system that fully solves our problem, and
it costs **$200k+ as part of a complete SWING workstation**. The
viscous-liquid head alone is not sold standalone.

Product overview: <https://www.chemspeed.com/technology/>

**What we copy:** the principle that positive-displacement (a piston
pushing the paste) handles thicker stuff than peristaltic, and that
gravimetric feedback is non-negotiable.

## 3. preeflow eco-PEN piston dispenser

[preeflow eco-PEN](https://www.preeflow.com/en/products/dispensers/eco-pen/)
is a small (~5 cm diameter, ~15 cm long) industrial piston dispenser
that mounts on a robot wrist. Originally built for glue and silicone
dispensing in electronics manufacturing. Handles 100,000 cP fluids
easily; ketchup is well within range. Costs around $3,000.

You don't see it in food labs because nobody markets it there — it
lives in the automotive and consumer-electronics worlds. But the
mechanics are exactly right for ketchup.

**What we copy:** a candidate end-effector. If the Watson-Marlow's
after-drip becomes a deal-breaker, swap to a preeflow head with valve
shut-off — the rest of the workflow stays the same.

## 4. Manual "tare-and-add" with a syringe — the food-lab default

The honest current state of the art in most food QC labs:

1. Tech tares a beaker on a balance.
2. Tech draws ketchup into a wide-bore syringe.
3. Tech presses the plunger slowly while watching the balance.
4. Tech stops when the reading is close to 5 g.
5. Tech twists the syringe tip off the surface to break the string.
6. Tech writes the actual mass into a notebook.

That is what we are improving on. Step 3 ("press slowly while
watching") and step 5 ("twist to break the string") are exactly the
two things a force-sensing robot does well.

## 5. Hamilton STAR / Tecan Fluent / Beckman Biomek — wrong tool

Same as the paracetamol case: these are pipetting workstations. They
**cannot** handle ketchup. The viscosity is far beyond the syringes
they ship with, and the nozzle clogs immediately. A 5 g aliquot of
ketchup would take many tens of minutes if it worked at all.

Listed only so you do not waste time evaluating them.

## 6. The closest research paper

**"TARMAC: Tactile Awareness via Robotic MAnipulation for Chemistry
labs"** (arXiv 2510.19289, 2025). A Franka Research 3 with a
six-axis FT wrist sensor dispensing **viscous chemistry samples**
into beakers on a balance. The paper's main contribution is using
tactile feedback to detect the **bead break** — exactly the ketchup
problem. Same arm, same problem, different sample. Worth reading
when implementing the gravimetric loop.

This paper is also our main evidence that **Franka FR3 is the
research-community default for tactile-feedback dispensing** in
liquid-handling and chemistry contexts.

## The lesson

For viscous paste dispensing, two things have to be true at once:

1. **A positive-displacement or peristaltic pump dispenses the paste.**
   The robot does not "scoop" it.
2. **A balance closed-loops on the mass.** The pump does not stop on a
   timer; it stops on a measured mass reading.

Item 2 is the same as the paracetamol case. Item 1 changes the
end-effector and changes the **force-sensing requirements** for the
arm. The arm holds the pump nozzle inches above the beaker for tens of
seconds while the pump runs; when the pump stops the arm must lift the
nozzle and **break the string** without dragging excess into the
beaker. That is what makes the Franka FR3 the better pick than the
UR3e — its joint torque sensors detect the string-break long before a
wrist-only sensor does.

See [`02-hardware-choice.md`](02-hardware-choice.md) for the full
hardware reasoning.
