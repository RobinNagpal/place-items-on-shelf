# 04 — Why Automate **Tray Loading** Specifically?

> **Who this is for:** Anyone asking "okay, but why this step and
> not, say, sample prep?" It is a fair question.

Of the four steps in
[`03-manual-steps-today.md`](03-manual-steps-today.md), we picked
**Step C — tray loading** as the first thing to automate. This doc
explains why.

## The five-line summary

1. Sample prep is too varied for a small arm.
2. Capping needs a specialised end-effector.
3. Tray loading is **the same motion every time, with one object
   shape**.
4. The HPLC itself is already automatic, so loading is the only
   manual step that **gates** the whole night-time run.
5. Tray loading is where **lab errors actually happen** today.

## The longer case

### Reason 1 — Sample prep is too varied

Sample prep needs:

- A balance (weighing).
- A vortex / sonicator (mixing).
- A pipettor (volumes from 1 µL to several mL).
- A syringe filter (0.22 or 0.45 µm).
- Sometimes an SPE manifold (extraction).
- Different glassware for different samples.

Each of these is a separate physical task. A single pick-and-place
arm cannot do them all without a tool changer and several specialised
end-effectors. **It can be done** — that is exactly what a Hamilton
STAR or a Tecan Fluent does — but those systems start at
**~$100,000+** and use specialised liquid-handling heads. They are
not what a small cobot project can attack first.

> **Conclusion:** sample prep is the right *long-term* target, but
> not the right *first* target.

### Reason 2 — Capping needs special tools

- Screw caps are not too bad (a parallel-jaw gripper can twist them
  on with some skill).
- **Crimp caps need a crimper tool** — a separate motor pressing a
  metal seal onto the vial.

Either case adds a tool the arm must carry. Skipping capping in v1
keeps the gripper simple (one design, just for vials).

### Reason 3 — Tray loading is uniform

This is the key. **Every vial is the same shape and weight.** Every
slot is the same size in the same grid. The only things that change
between cycles are:

- Which slot the vial goes in.
- Which barcode is on the vial.

A pick-and-place arm is *perfect* for this. The motion is the same
every time. The grip is the same every time. The lookup is software,
not hardware.

### Reason 4 — The HPLC run is already automatic, so loading is the bottleneck

The HPLC instrument runs **all night** by itself once a tray is
loaded. If a robot can load the next tray when the previous run
finishes, the instrument **never sits idle**. The loading step is
the only manual gate between one autonomous run and the next.

In contrast, if you automated sample prep but not loading, you would
still need a human to hand off vials. The gain is smaller.

> **Conclusion:** automating loading unlocks **24-hour HPLC use** in
> a way no other single step does.

### Reason 5 — Loading is where the errors happen

A well-trained technician rarely messes up sample prep — they have a
written procedure and they pay attention. But after preparing 96
samples, **the loading step is where tired-tech mistakes happen**:

- "Did I put sample 47 in slot 47 or slot 48?"
- "I think I crossed two vials when I was reaching."
- "The barcode label peeled off in transit."

In a regulated lab, even one mis-slotted vial can mean:

- Re-running the entire HPLC batch (hours).
- A deviation report to file.
- In a GMP setting, potentially rejecting the whole product batch.

A robot with a barcode reader in its loading loop **physically
cannot make this mistake**: it reads the barcode of the vial in its
gripper and looks up the slot in software before placing.

> **Conclusion:** the dollar value of the error reduction in this
> step alone justifies the project — even before considering speed
> savings.

## Numbers (rough, public sources)

- A busy QC lab might run **2–5 trays of 96 vials per HPLC per day**
  — i.e. **200–500 vials per HPLC per day**.
- At ~15 seconds of human handling per vial (pick, scan, place,
  log), that is **50 minutes to 2 hours of human time per HPLC per
  day** just on loading.
- A single industrial liquid handler can cost **$100,000+**.
- A small cobot (myCobot 280 Pi) costs **about $700**.
  - Payload: **250 g**, vials weigh ~5–10 g — comfortable margin.
  - Repeatability: **±0.5 mm**, slot clearance is ~1 mm — feasible
    but tight; see [`requirements/03-success-precision-speed.md`](requirements/03-success-precision-speed.md).
  - Reach: **280 mm**, fits a small bench cell.

So the **cost-to-savings ratio for the loading step alone is
attractive** even at small lab scale. Bigger arms (UR3e, Franka)
hit the same use case with more margin and bigger budgets.

## What we are *not* claiming

To stay honest:

- We are **not** claiming this will replace a Hamilton STAR. It
  won't. Different scope, different budget.
- We are **not** claiming v1 will be GMP-ready. GMP-grade software
  validation (21 CFR Part 11, full audit trail, fault tolerance)
  comes after the v1 demo, not in it.
- We are **not** claiming the arm can handle every brand of
  autosampler without tweaking. Tray geometry varies by vendor —
  some calibration is required per setup.

## Sources

- [HPLC Autosamplers: Perspectives, Principles, and Practices — LCGC](https://www.chromatographyonline.com/view/hplc-autosamplers-perspectives-principles-and-practices)
- [Pick and Place Automation for Vial Bottles — AIL Industrial](https://www.ail-us.com/post/pick-and-place-automation-for-vial-bottles-in-the-medical-and-pharmaceutical-industry)
- [The Rise of Automation in the Chromatography Lab — Element Lab Solutions](https://www.elementlabsolutions.com/uk/chromatography-blog/post/automation-in-the-chromatography-lab)
- [myCobot 280 Pi Specifications — Elephant Robotics](https://www.elephantrobotics.com/en/mycobot-280-pi-2023-specifications/)
- [QVIRO myCobot 280-Pi Specifications](https://qviro.com/product/elephant-robotics/mycobot-280-pi/specifications)

## What's next

→ Next: [`requirements/`](requirements/) — the requirements
themselves, broken out by topic.
