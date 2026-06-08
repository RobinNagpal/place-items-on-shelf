# 03 — Dilution (ketchup case)

A Gazebo world that mirrors HPLC workflow **Step 3 — Dilution**, for
the **ketchup** example only. The workflow doc describes this as the
"messy + uncertain" dilution:

> The ketchup extract is much less predictable — you do not know in
> advance exactly how much 5-HMF is in it. So you often dilute it a
> lot, for example **1:10 or 1:100**. Sometimes you have to guess, run
> it, and adjust.
> — [robotics-research / 03-hplc-autosampler / 03-hplc-workflow / 03-dilution.md](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/03-dilution.md)

The bench has both a **10 mL** and a **100 mL** volumetric flask on it
on purpose — the operator picks one based on how strong the Step 2
extract turned out. The action is: aspirate a measured volume of the
cloudy extract with the P1000 micropipette, dispense it into the
chosen flask, top up to the graduation ring with deionised water from
the solvent bottle, cap the flask, invert to mix, write the dilution
factor on the label with the Sharpie.

This world contains **only the bench and the objects**. There is no
arm. A yellow disc at the back of the bench marks where the arm base
will go later (same position as the Step 2 world, so the cell layout
stays consistent across steps).

## Run it

```bash
# Gazebo Classic
gazebo gazebo_worlds/03-dilution/ketchup_dilution.sdf

# Gazebo Sim (Garden / Harmonic / Ionic)
gz sim gazebo_worlds/03-dilution/ketchup_dilution.sdf
```

The world is **self-contained** — the sun (as a `<light>`) and the
ground plane are defined inline rather than via
`<include>model://sun</include>`, so no `GZ_SIM_RESOURCE_PATH` or
Gazebo Fuel setup is required.

### Run it on WSL (Ubuntu under Windows)

If you cloned this repo into `~/ros2_ws/src/place-items-on-shelf` (the
standard ROS 2 workspace layout):

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim gazebo_worlds/03-dilution/ketchup_dilution.sdf
```

If `gz: command not found`, install Gazebo Harmonic (matches ROS 2
Jazzy) — see the
[Step 2 README](../02-dissolution-and-extraction/README.md#run-it-on-wsl-ubuntu-under-windows)
for the full apt setup. You do not need to `source /opt/ros/<distro>/setup.bash`
just to run `gz sim` on an SDF — Gazebo is its own binary.

On Windows 11 + WSL2 the GUI window pops up via WSLg automatically.
On Windows 10 + WSL2 you need an X server running on the Windows side
(VcXsrv, X410, MobaXterm) and:

```bash
export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0
```

before running `gz sim`.

You should see a brown lab bench with: a small clear beaker holding a
dark-red translucent column of ketchup extract (left), the two
volumetric flasks side by side in the centre (10 mL near, 100 mL far),
a pale-blue water bottle (far left), a 250 mL waste beaker (far
right), a tall white pipette stand near the back with the blue-handled
P1000 hanging from its arm, a light-blue tip rack with four white tip
tops poking up, a black Sharpie lying flat at the back, and the yellow
arm-base disc behind everything.

## What is on the bench

All dimensions come from real off-the-shelf lab products. Frame
convention: **+X = forward**, **+Y = left**, **+Z = up**. Bench top is
at **z = 0.900 m**.

| # | Object | Purpose in workflow | Real product reference | Size (mm) | Pose (X, Y) on bench | Mass |
|---|---|---|---|---|---|---|
| 1 | **Bench** | Work surface | Laminated lab bench section | 1000 × 600 × 50 | centred at (0, 0) | static |
| 2 | **Arm marker** | Future arm base location | n/a — visual flag only | Ø100 × 2 yellow disc | (-0.22, 0.00) | static |
| 3 | **Source beaker** (with cloudy extract) | The Step 2 output — the cloudy ketchup extract you aspirate FROM | Corning Pyrex 1000 low-form, 100 mL (P/N 1000-100) | Ø50 × 70 | (0.00, +0.20) | 150 g |
| 4 | **10 mL volumetric flask** | First-attempt dilution vessel for a 1:10 dilution (1 mL extract + diluent to mark) | Corning Pyrex 5641 Class A 10 mL (P/N 5641-10) | Foot Ø30 × 3, bulb Ø30 sphere, neck Ø8 × 70, total 103 mm | (0.10, +0.07) | 35 g |
| 5 | **100 mL volumetric flask** | Backup dilution vessel for a 1:100 dilution when the 1:10 reads "still too strong" | Corning Pyrex 5640 Class A 100 mL (P/N 5640-100) | Foot Ø50 × 5, bulb Ø60 sphere, neck Ø12 × 140, total 205 mm | (0.10, -0.07) | 150 g |
| 6 | **Solvent bottle (water)** | Diluent — the doc names water (or mild acid) for the ketchup case | Schott Duran 500 mL wide-mouth reagent bottle GL45 (P/N 218017552) | Body Ø85 × 150, cap Ø50 × 25 | (0.05, +0.30) | 700 g |
| 7 | **Pipette charging stand** | Holds the micropipette upright when not in use | Eppendorf Single Stand for Research Plus / Reference (P/N 022499951) | Foot Ø100 × 10, pole Ø10 × 240, arm 50 × 10 × 10 | (-0.10, -0.15) | static |
| 8 | **Eppendorf Research Plus P1000 micropipette** | The "precise volume" tool — the workflow doc explicitly identifies this as the make-or-break instrument for dilution accuracy | Eppendorf Research Plus single-channel, 100 - 1000 µL (P/N 3123000063) | Total length 240 (thumb wheel Ø12.5 × 80 + body Ø7.5 × 100 + tip shaft Ø4 × 60) | hangs on the stand at (-0.055, -0.15) | 100 g |
| 9 | **Pipette tip rack (96 tips)** | Source of fresh, sterile tips. One tip per dilution step — no cross-contamination | Eppendorf epT.I.P.S. Box 2.0 for 100 - 1000 µL (P/N 0030073460) | 130 × 85 × 60 box, 96 tips Ø6 × 60 in 8 × 12 grid | (0.00, -0.15) | static |
| 10 | **Waste beaker (used tips)** | Tip-disposal pot — the operator ejects each used tip into here so the bench stays clean | Corning Pyrex 1000 low-form, 250 mL (P/N 1000-250) | Ø70 × 100 | (0.05, -0.30) | 300 g |
| 11 | **Sharpie permanent marker** | Records the dilution factor on the flask label area — the doc warns "forgetting to record the dilution factor → result is useless" | Sharpie Fine Point permanent marker, black (P/N 30001) | Body Ø12 × 110, cap Ø13 × 30, total 140 | (-0.10, +0.20) lying flat along Y | 12 g |

### Why these objects in particular

The Step 3 doc lists the dilution routine as: aspirate a small exact
volume → transfer to a clean larger container → top up with solvent
to a known total volume → mix → **record the dilution factor**. Every
object on the bench maps to exactly one of those sub-steps:

| Doc sub-step | Object responsible |
|---|---|
| "aspirate a small, exact amount" | P1000 micropipette + tip rack |
| "put it into a clean, larger container" | 10 mL / 100 mL volumetric flask |
| "add solvent up to a known total volume" | 500 mL water bottle + the etched ring on the flask neck |
| "mix well" | flask cap + manual inversion (the operator does this) |
| "write down the dilution factor" | Sharpie marker |
| "dilute the dilution" | second volumetric flask (use the 100 mL after the 10 mL) |
| (tip hygiene between aspirations) | waste beaker (eject + replace tip every transfer) |

### What was deliberately left out

- **Pasteur / serological pipettes + pipette bulb.** A glass volumetric
  pipette is more accurate than a micropipette for high volumes, but
  ketchup extract is pulpy and **clogs narrow glass capillaries** — the
  doc explicitly calls out the food sample as messier. A P1000 with a
  wide-bore tip handles pulp better, so that is what the bench shows.
- **Magnetic stirrer / hot plate.** The doc says "mix well" but for
  small dilutions in a volumetric flask the standard practice is
  manual **inversion** (cap and tip up-down 10 times), not magnetic
  stirring. So no hot plate in this world.
- **Analytical balance.** No gravimetric dilution is described in the
  ketchup paragraph — only volumetric. The balance lives in Step 1.
- **Filtration tools.** Pulp removal is [Step 4 — Filtering](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md);
  it does not belong here.
- **HPLC vials.** Vialling is [Step 5](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/README.md).

## Arm placeholder

The yellow Ø100 mm disc at **(-0.22, 0.00)** is the future arm-base
mounting spot. Same position as Step 2 so the same arm install works
for both worlds. To drop an arm in:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

The bench items at the perimeter — the solvent bottle at (0.05, +0.30)
and the waste beaker at (0.05, -0.30) — are **outside** the myCobot
280's ~280 mm reach envelope. For a myCobot, shrink the cell by
moving those two items to (0.05, ±0.20). The bench is sized generously
so a longer-reach arm (UR3 / Franka FR3) does not have to relayout.

## Coordinate sanity check

Bench top is at **z = 0.900 m**. Tall items and their tops:

| Object | Bottom z | Top z |
|---|---|---|
| Source beaker | 0.900 | 0.970 |
| 10 mL flask | 0.900 | 1.003 |
| 100 mL flask | 0.900 | 1.105 |
| Solvent bottle (incl. cap) | 0.900 | 1.075 |
| Pipette stand pole | 0.900 | 1.150 |
| Pipette (hanging) tip | 0.890 | 1.130 |
| Waste beaker | 0.900 | 1.000 |
| Tip box | 0.900 | 0.960 |
| Sharpie | 0.900 | 0.912 |

The tallest item (the 100 mL flask) is 205 mm above the bench. Leave
arm pre-grasp standoff ≥ 250 mm if you mount a vertically-approaching
gripper.

## Is one Gazebo world enough for Step 3?

**Yes**, one is enough for the ketchup case. Step 3 happens at one
bench station; the only branching is "pick the 10 mL or the 100 mL
flask," and both flasks are already on the bench. A 1:1000 cascade
(rare for ketchup) would just reuse the 10 mL flask twice in
sequence — still one world.

You would want a **second** world only for:

- the **paracetamol** Step 3 (a different layout — no waste beaker
  because clean drug solutions do not need pulp-tolerant tips, no
  100 mL backup flask because the target strength is predictable).
  A `paracetamol_dilution.sdf` sibling in this same folder would be
  the natural home.
- A **liquid handler / robot pipettor** version where the dilution
  happens off-bench in a dedicated automated station. That would
  belong in its own subfolder once it is on the roadmap.

For now, the single `ketchup_dilution.sdf` here covers the entire
ketchup Step 3 routine end-to-end.

## File list

```
03-dilution/
├── README.md                  (this file)
└── ketchup_dilution.sdf       (the Gazebo world)
```
