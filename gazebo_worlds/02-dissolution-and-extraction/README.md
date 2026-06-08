# 02 — Dissolution / extraction (ketchup case)

A Gazebo world that mirrors HPLC workflow **Step 2 — Dissolution /
extraction**, for the **ketchup** example only. It is the messy case
from the workflow doc:

> Take the ~5 g of ketchup you weighed into the beaker. Add a solvent —
> often water or a mild acid solution — that coaxes the 5-HMF (and some
> sugars) out of the thick paste and into the liquid. Stir, and possibly
> warm gently, to help the target leave the pulp and move into the
> liquid.
> — [robotics-research / 03-hplc-autosampler / 03-hplc-workflow / 02-dissolution-and-extraction.md](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md)

This world contains **only the bench and the objects**. There is no
arm. A small yellow disc marks where a future arm base will be bolted
down (see [Arm placeholder](#arm-placeholder)).

## Run it

```bash
# Gazebo Classic
gazebo gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf

# Gazebo Sim (Garden / Harmonic / Ionic)
gz sim gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

The world is **self-contained** — it defines the sun (as a `<light>`)
and the ground plane inline rather than via `<include>model://sun</include>`,
so no `GZ_SIM_RESOURCE_PATH` / Gazebo Fuel setup is required.

### Run it on WSL (Ubuntu under Windows)

If you cloned this repo into `~/ros2_ws/src/place-items-on-shelf` (the
standard ROS 2 workspace layout):

```bash
cd ~/ros2_ws/src/place-items-on-shelf
gz sim gazebo_worlds/02-dissolution-and-extraction/ketchup_extraction.sdf
```

If `gz: command not found`, install Gazebo Harmonic (matches ROS 2
Jazzy):

```bash
sudo apt update
sudo apt install -y curl lsb-release gnupg
sudo curl https://packages.osrfoundation.org/gazebo.gpg --output /usr/share/keyrings/pkgs-osrf-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/pkgs-osrf-archive-keyring.gpg] http://packages.osrfoundation.org/gazebo/ubuntu-stable $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/gazebo-stable.list > /dev/null
sudo apt update
sudo apt install -y gz-harmonic
```

(If you are on ROS 2 Humble, install Gazebo Classic 11 instead:
`sudo apt install -y gazebo libgazebo-dev` and use the `gazebo`
command, not `gz sim`.)

You do **not** need to `source /opt/ros/<distro>/setup.bash` just to
run `gz sim` on an SDF — that source command is for ROS 2 commands
(`ros2 ...`), not Gazebo itself. Gazebo is its own binary.

On Windows 11 + WSL2 the GUI window pops up via WSLg automatically.
On Windows 10 + WSL2 you need an X server running on the Windows side
(VcXsrv, X410, MobaXterm) and `export DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0`
in WSL before running `gz sim`.

You should see a brown lab bench with seven items on it: a red ketchup
bottle on the left, a pale-blue solvent bottle on the right, a hot
plate in the centre with a small clear beaker on its ceramic top, a
white weigh boat carrying a tiny red blob of pre-weighed sample, a
silver spatula, and a yellow disc at the back where the arm goes.

## What is on the bench

All dimensions are real off-the-shelf lab parts. Frame convention:
**+X = forward**, **+Y = left**, **+Z = up**. Bench top sits at
**z = 0.900 m** (standard lab bench height).

| # | Object | Real reference | Size (mm) | Pose (X, Y) on bench | Mass | Why it is on the bench |
|---|---|---|---|---|---|---|
| 1 | **Bench** | Laminated lab bench section | 1000 × 600 × 50 | centred at (0, 0) | static | The work surface everything sits on. |
| 2 | **Arm marker** | n/a (visual flag) | Ø100 × 2 disc | (-0.22, 0.00) | static | Marks where the arm base will be bolted down later. Yellow so it is impossible to miss. |
| 3 | **Hot plate** | IKA C-MAG HS 7 magnetic stirrer + hot plate | 220 × 220 × 120 (180 × 180 ceramic top) | (0.05, 0.00) | static | The doc says *stir, and possibly warm gently*. A combo hot-plate stirrer does both. |
| 4 | **Beaker (100 mL)** | Pyrex 1000 low-form, 100 mL | Ø50 × 70 | on the hot plate ceramic top | 75 g | The extraction vessel. Ketchup + solvent end up here. |
| 5 | **Stir bar** | PTFE-coated octagonal magnet | Ø25 × 8 (white) | inside the beaker | 5 g | Driven by the magnet under the hot-plate top, this is *how* the beaker gets stirred. |
| 6 | **Ketchup bottle** | Heinz 14 oz glass bottle | Ø55 body × 180, Ø30 cap × 25 | (0.10, +0.25) | 500 g | The source of the ~5 g sample. Glass body is painted red to read as "ketchup-visible-through-glass". |
| 7 | **Solvent bottle (water / mild acid)** | 500 mL wide-mouth glass reagent bottle | Ø85 body × 150, Ø50 cap × 25 | (0.10, -0.25) | 700 g | Holds the solvent the doc lists for ketchup: water, or a mild acid solution. Pale-blue label stands in for the text. |
| 8 | **Weigh boat + sample** | 60 mm white PS antistatic weigh boat | 60 × 60 × 15 | (-0.05, +0.18) | 10 g | Carries the pre-weighed ~5 g ketchup blob from Step 1. The doc opens with *"Take the ~5 g you weighed"* — this is that. |
| 9 | **Spatula** | 150 mm stainless lab scoop | 100 mm handle + 50 × 12 × 2 blade | (0.10, -0.05) | 15 g | Used to lift the ketchup blob from the weigh boat into the beaker. |

### Why these are the only items

Looking again at the ketchup paragraph of Step 2, the *required* actions
are: **transfer the pre-weighed sample → add solvent → stir → optionally
warm**. The items above are the smallest set that supports all four
actions with realistic real-world dimensions.

Items I considered and **deliberately left out**:

- **Ultrasonic bath (sonicator).** The doc's general routine mentions
  sonication, but the ketchup paragraph specifically says *stir, and
  possibly warm gently* — no sonication. Adding one would just clutter
  the cell.
- **Analytical balance + tare button.** Weighing happens in
  [Step 1](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md),
  not here. The pre-weighed sample on the weigh boat captures the
  hand-off cleanly.
- **Stock solution dilution flask, volumetric pipette, vials.** These
  belong to [Step 3 — Dilution](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/03-dilution.md)
  and later. Putting them here would imply a workflow the world is
  not modelling.
- **Pulp / centrifuge tube.** Pulp removal happens in
  [Step 4 — Filtering](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md),
  not Step 2.

## Arm placeholder

The yellow Ø100 mm disc at **(-0.22, 0.00)** on the bench top is the
arm base location. It sits 2 mm above the bench so it shows up clearly
in the GUI. When you are ready to add the arm:

1. Pick the arm you want (e.g. the upstream `mycobot_280` model).
2. Replace the `arm_base_marker` model with an `<include>`:

```xml
<include>
  <name>arm</name>
  <uri>model://mycobot_280</uri>
  <pose>-0.22 0.00 0.900 0 0 0</pose>
</include>
```

3. Check reach — the rough cell radius from the arm marker to the
   farthest object (the ketchup bottle at (0.10, +0.25)) is ~407 mm,
   which is outside the myCobot 280's ~280 mm reach. For a myCobot, the
   ketchup and solvent bottles should be moved closer to **(0.05, ±0.15)**.
   The bench is sized generously on purpose so a longer-reach arm
   (e.g. UR3 / Franka FR3) does not have to relayout the cell.

## Coordinate sanity check

Bench top is at **z = 0.900 m**. For any object on the bench, the
SDF pose's z is **0.900 + height/2** (boxes / cylinders are centred
on their geometry). The beaker is the only object not sitting
directly on the bench — it sits on the hot plate ceramic top at
**z = 1.020**, so its centre is at **z = 1.055**.

## Is one world enough for Step 2?

**Yes, one world is enough for the ketchup case.** Step 2 is a single
extraction at a single station, so a single bench layout covers
everything the doc asks for.

You would want a **second** world only if you were also modelling:

- the **paracetamol** case (clean dissolution into methanol). The
  objects overlap a lot — same beaker, same stir plate — but the
  source container is a blister-pack tablet, the solvent is methanol
  not water, and there is no weigh-boat-pulp aesthetic. A
  `paracetamol_dissolution.sdf` sibling under this same folder would
  be a natural next addition.
- **other steps** (dilution, filtering, vialling). Each step has its
  own bench layout and gets its own folder under `gazebo_worlds/`.

For now, the single `ketchup_extraction.sdf` here covers the entire
ketchup workflow for Step 2 end-to-end.

## File list

```
02-dissolution-and-extraction/
├── README.md                  (this file)
└── ketchup_extraction.sdf     (the Gazebo world)
```
