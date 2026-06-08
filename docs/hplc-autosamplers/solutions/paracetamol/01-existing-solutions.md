# 01 — How labs automate the weighing step today

Before we pick our own hardware, let us look at what real labs already
buy. The wider survey of HPLC-adjacent automation lives in
[`../../research/05-existing-solutions.md`](../../research/05-existing-solutions.md).
This file narrows it down to **weighing only**.

The pattern is the same everywhere: **a dedicated dosing balance does
the milligram-level work, and a robot only handles labware around it.**
No mainstream system tries to dispense powder *with the robot arm
itself*. Once you see why, the rest of this folder makes more sense.

## 1. Mettler Toledo XPR + Quantos — the gold standard

Mettler Toledo sells an analytical balance (the XPR family — readable
to 0.0001 g) together with a clip-on dispenser called **Quantos**.
Quantos comes in three head types:

- **QH** for powders.
- **QL** for liquids.
- **QS** for solid pellets.

You fill the head once with your sample (the head is a small sealed
cartridge with an RFID chip on it). The head sits over the balance pan.
You tell the Quantos a target mass — say "5 mg" — and it slowly opens a
valve while the balance reads the actual mass in real time. It stops
the moment the reading equals the target. Accuracy is ±0.1 mg at the
5 mg target.

Key things to notice:

- The dispensing **is not the arm's job**. The arm's only role is to
  put an empty container on the pan and remove the filled one.
- The dosing head is **swappable** — different chemicals in different
  heads, no cross-contamination, no manual cleaning. The balance reads
  the RFID and logs which head is in use.
- Static (the powder clinging to itself or the pan) is handled by a
  built-in **ionising bar** inside the dispenser.

The full robotic version is the **Mettler CHRONECT XPR Quantos**: a
6-axis arm picks vials and dosing heads from a carousel and feeds the
balance. List price for the Quantos module + balance is around
**$30,000 – $50,000** new (used ones appear around $13k on eBay).
That is the cost floor for "real" automated weighing in pharma today.

- Product page: <https://www.mt.com/us/en/home/library/product-brochures/laboratory-weighing/Quantos_Powder_Dosing.html>
- CHRONECT Bionic arm: <https://www.mt.com/us/en/home/products/Laboratory_Weighing_Solutions/mettler-product-collaboration/axel-semrau.html>

**What we copy from this:** the whole pattern. Our recommendation is
exactly this — Quantos for dispensing, arm for labware. We just swap
their proprietary 6-axis robot for a cheaper standard one.

## 2. Chemspeed SWING / FLEX — gantry-based "kitchen"

Chemspeed builds whole automated chemistry workstations. Their key idea
is different: instead of carrying labware to the balance, the **balance
itself moves** (on a small gantry inside the machine) to whichever
dispenser head is needed. They have over 70 swappable heads — solids,
liquids, viscous fluids, even pastes.

Geometry is a **Cartesian XYZ gantry** with a rotating wrist — not a
6-axis articulated arm. Cartesian means it moves like a 3D printer:
straight along three perpendicular rails. Cheaper to build, very
precise, but limited to right angles.

Worth knowing about because it proves that **paste dispensing on a
balance has been done commercially** — that is relevant for our
ketchup case (see [`../ketchup/`](../ketchup/)).

- Product overview: <https://www.chemspeed.com/technology/>

**What we copy from this:** the principle that gantry / Cartesian
geometry is enough for flat-bench labware shuffling. For our
small-scale project we still pick a SCARA / 6-axis arm (more
beginner-friendly to simulate), but a Cartesian XYZ would also be a
valid pick for a production v2.

## 3. Hamilton STAR / Tecan Fluent / Beckman Biomek — gravimetric *verification*, not dispensing

These three are the giants of automated pipetting (~$50k–$300k). They
all do the same trick:

- They pipette liquids using high-precision syringes.
- They have an **optional on-deck analytical balance**. After the
  pipette dispenses, the balance reads the mass to confirm the volume
  was correct.

This is called **gravimetric verification**: you weigh what you just
pipetted to double-check it. Tecan even sells a stand-alone
**Automated Weighing Station** with up to two balances on it.

But **none of these dispense powder**. The balance is downstream of a
pipette, not a powder doser. So they only solve half of our problem —
the half that does not need solving for paracetamol.

- Tecan AWS: <https://www.tecan.com/customer-news/tecan-announces-a-major-breakthrough-in-sample-management-and-gravimetric-analysis-tecan-s-automated-weighing-stations-2336>

**What we copy from this:** the gravimetric verification idea is useful
for our **dilution** and **transfer-to-vial** steps later. For Step 1
(weighing) it is the wrong tool.

## 4. PAL System (PAL RTC, PAL3) — autosampler with a side balance

PAL is the family of autosamplers that already loads vials into HPLC
machines. The newest PAL3 has an optional **balance module**: a vial
can be placed on a small balance for a tare-and-add reading before the
injector picks it up.

Again, **no powder dispensing**. The PAL is a pickup-and-place machine
with syringes — it does not dose solids.

- PAL RTC product page: <https://www.palsystem.com/en/products/pal-systems/pal-rtc/>

**What we copy from this:** nothing for Step 1. The PAL becomes
relevant later, around Step 8 (placement in the autosampler).

## 5. The lesson — and why the arm we pick does not need to be precise

Every commercial system that **actually dispenses powders to a target
mass** does it with a dedicated dosing module on an analytical balance.
**No commercial system uses a generic robot arm to scoop powder.**
The reason was already in the upstream weighing doc:

> "positioning the container is easy, but dispensing a powder a
> fraction of a milligram at a time is a delicate skill. A general arm
> pinching powder would be clumsy. In practice this step is handled by
> a dedicated dosing balance that the arm simply feeds and unloads."

So our robot arm does **not** need 0.1 mg precision. It needs:

- enough reach to span the bench cell (~40 cm),
- enough payload to lift a 100 mL flask (~250 g full),
- enough repeatability to land the flask on the balance pan (±1 mm
  is fine — the pan is 80 mm wide),
- a way to slide the draft-shield door,
- and a parallel-jaw gripper soft enough not to crush glass.

That is a much easier shopping list than "a robot that can dose
powder", and it lets us choose a small, cheap arm. The next file
([`02-hardware-choice.md`](02-hardware-choice.md)) walks through the
candidates and the pick.
