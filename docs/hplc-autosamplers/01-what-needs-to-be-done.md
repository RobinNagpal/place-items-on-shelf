# 01 — What Needs To Be Done: HPLC Autosampler Tray Loading

> **Who this is for:** Anyone new to the project who wants to understand
> *which exact piece of lab work we are trying to automate* with a robot
> arm, and *why that piece is still done by hand today*.
>
> This is the **task description** for the project. It is the kind of
> document the framework in
> [`../01-finalize-requirements/01-understanding-the-problem.md`](../01-finalize-requirements/01-understanding-the-problem.md)
> and
> [`../01-finalize-requirements/02-additional-requirements-to-consider.md`](../01-finalize-requirements/02-additional-requirements-to-consider.md)
> tells you to write before picking any hardware.

## The very short version

Labs that test what is inside a liquid — drug labs, food labs, water
labs, hospital labs — use a machine called an **HPLC**. The HPLC has a
front piece called the **autosampler**. The autosampler is a tray with
many small holes. A small glass tube (a **vial**) sits in each hole.
Each vial holds a tiny amount of one sample.

The HPLC itself is already automatic: a needle drops into each vial,
sips a drop, and tests it. **One vial after another, all night, no
human needed.**

But getting to that point is **not** automatic. A human has to:

1. **Prepare each sample** — weigh, dissolve, dilute, filter, pour into a
   vial.
2. **Cap and label each vial.**
3. **Place each vial into the right hole in the tray.**
4. **Slide the tray into the autosampler.**

Steps 1 to 4 are slow, boring, and error-prone. **This is the part we
want a robot to do.** For the first version of this project we focus
mostly on **steps 3 and 4** — picking vials and placing them in the
tray — because that fits a small pick-and-place arm.

## What is HPLC, in one paragraph?

**HPLC** stands for **High-Performance Liquid Chromatography**. You have
a liquid mixture and you want to know what is in it. You push the liquid
through a long thin tube packed with tiny particles. Different chemicals
in the liquid stick to the particles by different amounts, so they come
out the other end at different times. A detector at the end counts what
comes out, when. From the times and amounts, the software tells you
which chemicals were in the mixture and how much of each.

It is one of the most-used machines in chemistry labs. Almost every drug
batch made in the world is checked with HPLC before it ships.

## What is an autosampler?

An **autosampler** is the part of the HPLC that holds many samples and
feeds them in one by one. Think of it like a small lazy Susan inside a
box. The box has a sliding tray. The tray has a grid of round holes —
often 6 by 9 (54 holes), or 8 by 12 (96 holes). A small glass vial sits
in each hole.

When the HPLC starts a run, a robot needle inside the autosampler:

1. Moves to vial 1.
2. Pokes through the cap.
3. Sucks up a tiny amount (a few microlitres).
4. Squirts it into the column.
5. Moves to vial 2.
6. Repeats, until every vial in the tray has been tested.

A 96-vial tray can take **all night** to run. That part is already
automatic. Nothing in this project changes that.

## So what is still done by hand?

Everything *before* the tray gets slid into the autosampler. In a normal
lab, a technician spends hours every day doing this:

### Step A — Sample prep

The technician has the raw samples — pills, powders, liquids, food
extracts, blood, water — and turns each one into the small clear
liquid the HPLC needs:

1. **Weigh** the sample on a balance.
2. **Add solvent** (methanol, water, buffer) to dissolve it.
3. **Mix** (vortex, sonicate).
4. **Dilute** to the correct strength.
5. **Filter** the liquid (so tiny bits don't clog the HPLC).
6. **Pour** the filtered liquid into an empty HPLC vial.

This is the **most varied** part. Different samples need different
solvents, different dilutions, different filters. It is also the
hardest to fully automate because it needs **liquid handling** (very
accurate pipettes), not just pick-and-place.

> **For our project:** we treat sample prep as **out of scope for the
> first version**. We assume the technician has already finished it and
> the vials are full and capped. This is the same trade-off that the
> giant lab-automation companies make at the low end.

### Step B — Cap and label

The technician:

1. **Puts a cap on** each vial. Two common kinds:
   - **Crimp caps** — a thin metal seal that gets squeezed on with a
     special tool.
   - **Screw caps** — easier; just twist on by hand.
2. **Labels** the vial with a barcode sticker or hand-written number,
   so it can be matched back to the original sample.

For our project, **capping is mostly out of scope** in the first
version (the cap is on already). **Reading the label barcode** is in
scope, because the robot must know which vial it is holding.

### Step C — Load the tray

Now the technician has, say, 96 ready vials in a rack on the bench. He
or she:

1. Picks up vial 1.
2. (Optionally) scans the barcode.
3. Places it in slot 1 of the autosampler tray.
4. Picks up vial 2, places it in slot 2.
5. … repeat 94 more times.

Each placement must be **exact** — the slot is only a couple of
millimetres wider than the vial. Each placement must be **logged** —
which vial went where — because that mapping is what the HPLC software
uses to label the results.

> **This is the heart of what our robot does.** Pick-and-place with a
> barcode read in the middle.

### Step D — Slide the tray in and start

1. Open the autosampler drawer.
2. Slide the loaded tray in.
3. Close the drawer.
4. Tell the HPLC software the barcode-to-slot mapping.
5. Press "Start".

For our project, **steps 1, 2, 3 might be in scope** depending on the
drawer mechanism. Step 4 is software, not robot work. Step 5 can be
done by the technician.

## Why automate steps B/C/D at all?

This is the part new people often ask about. The HPLC itself is already
automatic — so why bring a robot in for the loading step? A few reasons:

1. **Volume.** A busy QC lab loads **hundreds of vials a day**. The
   loading takes hours, every day, every shift. That is paid technician
   time spent on a boring task.
2. **Errors.** A tired human at hour six of a shift puts vial #47 in
   slot #48. Now every result after that is **wrong**, and someone has
   to investigate. In regulated pharma this can mean recalling a batch.
3. **Audit trail.** Pharma rules (GMP, GLP) say you must prove which
   vial went where, when, and who did it. A robot can log this
   perfectly. A human writing it in a notebook can't.
4. **24/7 operation.** The HPLC can run all night. If a robot loads the
   next tray at 2 a.m., the instrument never sits idle.
5. **Hazard reduction.** Some samples are toxic or biohazardous. A robot
   inside an enclosed cell handles them safely.

These are the same reasons the big lab-automation companies (Hamilton,
Tecan, Beckman, Andrew Alliance) sell loading robots for **tens of
thousands of dollars**. We are aiming much lower: a small educational
cobot like the **myCobot 280 Pi** doing the same job, well enough for a
small lab or a learning project.

## What our robot must do, in plain words

Putting all of the above together, here is the task for our robot, in
order:

1. **See** an inbound rack of ready vials on the bench.
2. **Pick** the next vial from the rack without dropping or breaking it.
3. **Move** the vial to a barcode reader and **read** the label.
4. **Look up** in the lab system which tray slot this vial belongs in.
5. **Move** the vial above the right slot of the autosampler tray.
6. **Lower** it gently into the slot, upright.
7. **Release** and back off.
8. **Log** the barcode-to-slot mapping.
9. **Repeat** until the rack is empty or the tray is full.

That's the whole loop.

## What we are **not** trying to do (yet)

To keep the project doable on a small arm, we draw a line. **Out of
scope for the first version:**

- **Sample preparation.** No weighing, dissolving, pipetting, filtering.
  Vials arrive ready, full, and capped.
- **Capping and crimping.** No special tools on the gripper for this.
- **Liquid handling.** Anything that needs precise microlitre pipetting
  is for a different machine.
- **Operating the HPLC itself.** The HPLC vendor's own software runs
  the injection. We just deliver the loaded tray to it.
- **Sample disposal after the run.** Out of scope for v1; the
  technician removes the tray.

These all become possible **later**, with extra hardware (liquid handler
end-effector, crimper tool, etc.), but they are not what this project
is solving.

## A first-cut answer to the Layer-1 questions

Below is a short pass over the seven questions from
[`../01-finalize-requirements/01-understanding-the-problem.md`](../01-finalize-requirements/01-understanding-the-problem.md).
The answers are rough on purpose — exact numbers come later as the
project grows.

1. **Task, one sentence.**
   *Pick a sample vial from an inbound rack, read its barcode, and
   place it in the correct slot of an HPLC autosampler tray.*

2. **Objects handled.**
   - **2 mL HPLC vial.** Small glass cylinder, about 12 mm wide and 32
     mm tall. Light (5–10 g). Slippery glass. Breaks if squeezed too
     hard. Cap on top.
   - **Inbound rack.** Plastic, with a grid of round holes the right
     size for the vials.
   - **HPLC autosampler tray.** Metal or plastic, with numbered slots
     in a fixed grid. Sits inside the autosampler drawer.

3. **Environment.**
   - Tidy lab bench, fixed positions.
   - Indoor, climate-controlled, lab lighting.
   - A bit cluttered — the HPLC, the rack, the barcode reader all share
     a small bench.
   - **Humans nearby** — a lab technician is in the room. The arm must
     be a collaborative cobot or live inside a guarded cell.
   - Arm is **bench-mounted**, fixed base, no driving around.

4. **Success / failure.**
   - **Success:** vial placed upright in the correct slot, cap intact,
     no spill, and the barcode-to-slot mapping logged.
   - **Failure:** vial dropped, broken, mis-slotted, placed upside down,
     or moved without being logged.
   - Target: 99+ successes per 100 placements. No breakage.

5. **Precision and speed.**
   - **Precision:** about 2 mm at the slot — the vial is 12 mm wide and
     the slot is roughly 14 mm wide, so the arm can be off by about a
     millimetre and still drop the vial in cleanly.
   - **Speed:** about 10–20 seconds per vial. A 96-vial tray then loads
     in roughly half an hour.

6. **Workspace and reach.**
   - Working area roughly 40 cm wide, 40 cm deep, 40 cm tall.
   - Inbound rack on one side, autosampler drawer on the other,
     barcode reader in between.
   - Obstacles: the autosampler housing, the rack walls, the barcode
     reader, and any vials already loaded into the tray.

7. **Practical limits.**
   - **Budget:** small lab — a few hundred to a few thousand dollars
     for the arm.
   - **Power:** ordinary wall socket.
   - **Safety:** humans share the room, so we need either a
     collaborative cobot or a guarded cell with light curtains.
   - **Software to talk to:** a LIMS (sample tracking system), a
     barcode reader, and ideally the HPLC vendor software.
   - **Maintenance:** a lab technician for daily cleaning, vendor
     support for hardware faults.

## A first-cut answer to the additional questions

Same idea, but for
[`../01-finalize-requirements/02-additional-requirements-to-consider.md`](../01-finalize-requirements/02-additional-requirements-to-consider.md).
Rough numbers only.

- **Duty cycle:** about **100 vials a day**, 8 hours, 5 days a week.
- **Lifespan:** **3–5 years.**
- **Operator:** **lab technician.** Knows lab software, not robotics.
  Needs a simple "Start" button and clear status lights.
- **Maintenance:** in-house cleaning, vendor support for hardware
  problems.
- **Other systems to connect to:** LIMS, barcode reader, HPLC vendor
  software.
- **Logging:** **every vial transfer must be logged.** In a pharma lab
  this data is kept for years.
- **Failure behaviour:** **stop and call a human.** Samples are
  precious — don't blindly retry.
- **Regulators:** **GMP / GLP** in pharma labs, **CLIA** in clinical
  labs, **CE / UL** for electrical safety. For a hobby setup, none of
  these apply yet, but we keep them in mind.
- **Deadline:** no fixed deadline. Aim for a Gazebo simulation first,
  then real hardware later.
- **Scale:** **one cell to start.** Many copies later, if it works.
- **Variations:** mostly 2 mL crimp-cap vials, but **1 mL and screw-cap**
  variants exist and would be nice to handle later.
- **Acceptance test:** a **1,000-vial run** with no breakage and 99+
  percent correct placement.
- **Network exposure:** lab LAN only. No direct internet exposure.

## Common mistakes (to watch for as we design)

These come from
[`../01-finalize-requirements/01-understanding-the-problem.md`](../01-finalize-requirements/01-understanding-the-problem.md)
and apply directly here:

1. **Picking the arm first.** Don't buy hardware until this document is
   finished and agreed on.
2. **Skipping the object analysis.** "We'll figure out the gripper
   later" — but a wet, slippery, 12 mm glass cylinder is genuinely
   tricky to grip. Decide early.
3. **Vague success rules.** "Robot loads the tray" is not enough — we
   need a number (e.g. 99 out of 100, no breakage).
4. **Ignoring humans.** The technician is in the room. Safety must be
   designed in, not added on.
5. **Promising "production-ready" too soon.** A research / hobby setup
   is a great starting point, but GMP-grade production needs a much
   bigger investment.

## What's next

- **Layer 2 — Hardware.** Take this document into
  [`../02-hardware-selection/`](../02-hardware-selection/) and work
  through arm, gripper, sensors, mount, power, control hardware,
  networking, safety, and operator interface.
- **Simulation first.** Build a Gazebo world that models a simple HPLC
  tray and an inbound rack, and run pick-and-place in simulation before
  touching real glass. The existing myCobot pick-and-place demo (see
  [`../../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md`](../../robots/mycobot-280-pi/docs/concepts/04-pick-place-task.md))
  is the natural starting point — swap the YCB cylinder for a vial and
  the empty table for a tray.
- **Later docs in this folder** will add: the simulation world setup,
  the perception choices for vials, the grasp design for slippery
  glass, and the LIMS / barcode integration.
