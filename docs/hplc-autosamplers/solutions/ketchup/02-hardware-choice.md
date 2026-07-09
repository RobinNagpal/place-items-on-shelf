# 02 — Hardware choice for the ketchup case

Same rule as the paracetamol case: the arm and gripper must handle
**all eight workflow steps**, not just the weighing one. If the choice
breaks at Step 6, the cell is wrong.

This file walks all eight steps from the *gripper's point of view*,
then picks an arm, then picks the case-specific dispenser. The arm
and gripper answers come out the same as for paracetamol; the
dispenser does not.

## What every step asks the gripper to do (ketchup-flavoured)

| # | Step | What the gripper physically does | Specialized station the arm presents labware to |
|---|---|---|---|
| 1 | [Weighing](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md) | Grip a 50 mL beaker (50 mm OD), slide the draft-shield door | Mettler XPR1203S balance + Watson-Marlow 323Dud peristaltic pump (fixed nozzle over pan) |
| 2 | [Extraction](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md) | Grip the same beaker, drop it on a heated stirrer | Heated magnetic stirrer (50 °C, 600 rpm) |
| **3a** | **Centrifuge** (extra step for food) | Grip a centrifuge tube (16 mm OD), load into rotor | Eppendorf 5424 microcentrifuge |
| 3 | [Dilution](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/03-dilution.md) | Pick up an electronic pipette, dilute the clarified extract | Sartorius Picus 1000 µL + holster |
| 4 | [Filtering](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md) | Grip a 10 mL syringe with a **0.22 µm** filter on the tip, push the plunger with controlled force | Syringe-filter clamp |
| 5 | [Transfer to vial](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/05-transfer-to-vial.md) | Hold pipette over the 2 mL vial, dispense | (uses the pipette holster) |
| 6 | [Capping](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/06-capping.md) | Grip a 10 mm screw cap, set it on the vial, rotate wrist to torque limit | Cap dispenser |
| 7 | [Labeling](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/07-labeling.md) | Hold the vial upright, present it to the wrapper | Zebra ZD421 printer + wrapper |
| 8 | [Placement](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/08-placement-in-autosampler.md) | Grip the 12 mm vial, place in numbered slot | Agilent 100-position tray |

Two differences from the paracetamol table:

- **Step 1** uses a peristaltic pump instead of a Quantos powder
  doser. The arm's job (place beaker, walk away, pick up beaker) is
  the same shape.
- **Step 3a** is a new row: a centrifuge step before dilution. The
  upstream Step 4 explains why — ketchup has pulp that would
  instantly clog a 0.22 µm filter, so it is centrifuged first.

Everything else is identical to the paracetamol case from the
gripper's point of view. A 50 mL beaker is wider than a 100 mL flask
neck (50 mm vs 35 mm), but our gripper opens to 50 mm so it fits.

## Can one gripper do all eight + 8a steps? Yes.

Same answer as paracetamol. The gripper needs:

- Range from **10 mm** (cap) to **50 mm** (beaker) wide.
- **Glass-safe** soft pads or low force.
- **Plunger pressing** for Step 4.
- **Cap torquing** for Step 6.

An adaptive parallel-jaw gripper with a 0–50 mm stroke, soft silicone
fingertips, and a force-control mode covers all of them. No tool
changer is needed. Nothing case-specific to ketchup forces a second
gripper.

## Arm pick — Universal Robots UR5e (same as paracetamol)

The all-8-steps reasoning is the same as in the paracetamol case.
Repeated here because most readers will only open one folder.

**UR5e at a glance:**

| Spec | Value | Why it matters here |
|---|---|---|
| Reach | **850 mm** | Spans an ~1.0 m bench cell from a central mount |
| Payload | **5 kg** | Beaker + pipette + gripper ≈ 700 g — well within |
| Joints | 6, including **continuous wrist rotation** | Wrist spin tightens the screw cap in step 6 |
| Repeatability | ±0.03 mm | Plenty for our 1 mm autosampler tolerance |
| Built-in sensor | **6-axis wrist force/torque sensor** | Drives plunger push (step 4) and cap torque (step 6) |
| Approx. price | ~$36,000 new | Mid-range cobot |
| Simulation | First-party [`Universal_Robots_ROS2_Driver`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver), [`Universal_Robots_ROS2_GZ_Simulation`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation), MoveIt 2 config | Best-supported arm in open-source robotics |

### Why not a different arm just for ketchup?

The earlier draft of this file picked a **Franka Research 3** for
ketchup, because joint-torque sensing on every joint would help
detect the **bead-break** when the arm retracts after a paste
dispense. But we have since moved the pump **off the arm** and onto
a stationary mount. The arm now only places an empty beaker on the
pan and picks it up filled — exactly like the paracetamol case. The
bead-break happens between the fixed pump nozzle and the beaker; the
arm is not in the loop at that moment.

With the pump stationary, the joint-torque argument disappears. UR5e
+ wrist FT is just as good for ketchup as it is for paracetamol.

### Competitor 1 (rejected) — Franka Research 3 (FR3)

- 7 joints, joint torque on every joint, ±0.1 mm, 855 mm reach.
- ~$15,000 at the research-academic price.

Rejected for two reasons:

1. **3 kg payload** is tight when carrying a syringe + filter + liquid.
2. **Joint torques are wasted** here — pump is stationary, so the
   force-sensing problem is the same one the UR5e wrist FT already
   handles.

### Competitor 2 (rejected) — Kinova Gen3 (7-DOF)

- 7 joints, joint torques, 4 kg payload, 902 mm reach.
- ~$30,000.

Rejected on **simulation maturity**: the Kinova Gazebo plugin lags
ROS 2 releases by months. Pick UR5e in v1; revisit Kinova at v2 if
its sim story matures.

## Gripper pick — Robotiq Hand-E (same as paracetamol)

| Spec | Value | Why it matters here |
|---|---|---|
| Stroke | **0–50 mm** | Fits the 10 mm cap up to the 50 mm beaker |
| Force | 20–185 N, force-controlled | Soft on glass, firm on syringe plunger |
| Finger pads | Swappable silicone | Grips glass without slipping |
| Mass | 0.9 kg | Within UR5e payload |
| Driver | First-party Robotiq UR Toolio + [PickNik](https://github.com/PickNikRobotics/robotiq) ROS 2 driver | Drops in next to UR5e sim |
| Approx. price | ~$5,000 | The smallest of Robotiq's lineup |

### Why this single gripper covers all 8 (+1) steps

| Step | Hand-E action |
|---|---|
| 1 | Grips the 50 mm beaker body. Slides the draft-shield door. |
| 2 | Same beaker grip; places it on the heated stirrer. |
| 3a | Grips a 16 mm centrifuge tube; loads into the rotor. |
| 3 | Grips the 25 mm pipette handle; dilution dispenses are electronic. |
| 4 | Grips a 16 mm syringe barrel; closes force-controlled on the plunger top. |
| 5 | Pipette again. |
| 6 | Grips a 10 mm cap; wrist rotates to torque limit. |
| 7 | Holds the vial upright; wrapper applies the label. |
| 8 | Grips the 12 mm vial body; drops into tray slot. |

### Gripper competitor 1 (rejected) — Robotiq 2F-85

- 85 mm stroke, same ecosystem.

Rejected because **a larger stroke buys nothing** here, and 2F-85's
fingertip pads grip 12 mm vials slightly less securely than Hand-E's.

### Gripper competitor 2 (rejected) — OnRobot RG2-FT

- Built-in 6-axis FT in each finger; ~$10k.

Rejected because the UR5e wrist FT already does what we need, and
RG2-FT doubles the gripper cost for no gain in our 8 (+1) steps.

## Step 1 dispenser pick — Watson-Marlow 323Dud peristaltic pump + Mettler XPR1203S

The arm and gripper are case-independent. The **Step 1 dispenser** is
not — for ketchup it must extrude a thick paste with mass feedback.

| Spec | Value |
|---|---|
| Balance | Mettler Toledo **XPR1203S** (1.2 kg capacity, 1 mg readability) — bigger pan than the XPR226 to fit a 50 mL beaker |
| Pump | Watson-Marlow **323Dud** with 4 mm Marprene tubing |
| Control | Pump speed set by RS232 / Modbus over serial; balance reads on serial too. Closed-loop in software. |
| Target mass | ~5 g |
| Accuracy at 5 g | ±1 mg with a slowdown ramp and after-drip correction |
| Approx. price | ~$2,500 (pump) + ~$15,000 (balance) |
| What the arm has to do | Place the empty beaker on the pan; close the draft-shield door; trigger the closed-loop dispense over serial; wait; open the door; remove the filled beaker |

The pump sits on a small bench fixture next to the balance. Its
nozzle hangs ~5 mm above the centre of the pan. The arm aligns the
beaker so its centre is under the nozzle. Sub-millimetre precision is
not needed — the nozzle is ~5 mm wide and the beaker is 50 mm wide.

### Dispenser competitor 1 (rejected) — preeflow eco-PEN piston dispenser

- Cleaner shut-off (no after-drip).
- Handles 100,000+ cP — more headroom than Watson-Marlow on cold
  ketchup.

**Rejected for v1** because it needs a cleaning cycle between samples
(disposable cartridge or a flush), and food labs already know
Watson-Marlow pumps. If v2 needs to skip the warming step or push the
mass accuracy below 1 mg, swap to a preeflow — the rest of the cell
stays the same.

### Dispenser competitor 2 (rejected) — Manual scoop + tare-and-add by hand

The current industry default in most food QC labs. Cheap, but it
needs a human standing at the bench for every sample. Not actually
automation; listed only to make clear we are not competing with it on
cost — we are competing on consistency and audit trail.

## The whole shopping list (ketchup cell)

| Item | Pick | Approx. price |
|---|---|---|
| Arm | Universal Robots UR5e | ~$36,000 |
| Gripper | Robotiq Hand-E | ~$5,000 |
| Step 1 — balance | Mettler XPR1203S | ~$15,000 |
| Step 1 — pump | Watson-Marlow 323Dud + Marprene tubing | ~$2,500 |
| Step 2 — heated stirrer | IKA C-MAG HS 7 hot plate | ~$700 |
| Step 3a — centrifuge | Eppendorf 5424 (24 × 1.5 mL tubes) | ~$5,500 |
| Step 3 / 5 — pipette | Sartorius Picus 1000 µL + holster + tips | ~$1,500 |
| Step 4 — syringe-filter clamp + 0.22 µm filters | 3D-printed jig + PVDF filters | ~$300 |
| Step 6 — cap dispenser | Spring-loaded cap turret (custom) | ~$300 |
| Step 7 — label printer + wrapper | Zebra ZD421 + wrapper | ~$2,500 |
| Step 8 — autosampler tray | Agilent 100-position tray | ~$200 |
| Wrist camera | Intel RealSense D405 | ~$400 |
| Misc | — | ~$1,000 |
| **Total** | | **~$70,900** |

About $13k less than the paracetamol cell — the Quantos is the
expensive item; the Watson-Marlow + bigger balance combination is
cheaper. The extra centrifuge is the only added line.

## Cross-case comparison

| | Paracetamol | Ketchup |
|---|---|---|
| **Arm** | UR5e | **UR5e (same)** |
| **Gripper** | Robotiq Hand-E | **Robotiq Hand-E (same)** |
| **Step 1 dispenser** | Mettler Quantos QB1 (powder) | Watson-Marlow 323Dud (paste) |
| **Balance** | Mettler XPR226 (0.1 mg) | Mettler XPR1203S (1 mg) |
| **Mixing station** | Ultrasonic bath | Heated magnetic stirrer + microcentrifuge |
| **Target mass** | ~5 mg | ~5 g |
| **Arm cycle time per sample** | ~3 minutes (no centrifuge) | ~7 minutes (centrifuge adds 4 min) |
| **Total cell cost** | ~$83.6k | ~$70.9k |

The two cases share an arm and a gripper because the all-8-steps
analysis converges. They diverge on **the dispenser** (Step 1) and
on **mixing / clarification stations** (Steps 2 and 4) — exactly
where the chemistry actually differs.

## Next

[`03-simulation-workflow.md`](03-simulation-workflow.md) walks
through **(a)** what the arm physically does at each step and
**(b)** how we implement it in ROS 2 + Gazebo + MoveIt 2.
