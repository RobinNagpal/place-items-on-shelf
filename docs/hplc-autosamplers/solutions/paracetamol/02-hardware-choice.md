# 02 — Hardware choice for the paracetamol case

We do **not** choose the arm and gripper from the weighing step alone.
The same robot must also do the seven other workflow steps
(dissolution → dilution → filter → vial transfer → cap → label →
autosampler placement). If the choice works for Step 1 but breaks at
Step 6, we have built the wrong cell.

This file walks all eight steps from the *gripper's point of view*,
then picks an arm, then picks the dispenser.

## What every step asks the gripper to do

Read this table top to bottom. Each row is one upstream workflow file,
linked. The "Specialized station" column lists any non-arm hardware
the cell needs.

| # | Step | What the gripper physically does | Specialized station the arm presents labware to |
|---|---|---|---|
| 1 | [Weighing](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md) | Grip a 100 mL volumetric flask (35 mm neck), slide the draft-shield door | Mettler XPR analytical balance + Quantos QB1 powder doser |
| 2 | [Dissolution](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/02-dissolution-and-extraction.md) | Grip the same flask, drop it into a fixed ultrasonic bath | Branson 1800 ultrasonic bath |
| 3 | [Dilution](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/03-dilution.md) | Pick up an electronic pipette (25 mm handle), aim it into a 10 mL volumetric flask | Sartorius Picus pipette in a charging holster + tip rack |
| 4 | [Filtering](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/04-filtering.md) | Grip a 10 mL syringe with a 0.45 µm filter on the tip, **press the plunger with controlled force** | Syringe-filter clamp on the bench |
| 5 | [Transfer to vial](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/05-transfer-to-vial.md) | Hold the pipette over a 2 mL vial (12 mm OD), dispense | (uses the same pipette holster as step 3) |
| 6 | [Capping](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/06-capping.md) | Grip a 10 mm screw cap, set it on the vial, **rotate the wrist to torque limit** | Cap dispenser (spring-loaded) |
| 7 | [Labeling](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/07-labeling.md) | Hold the vial upright, present it to a label applicator | Zebra ZD421 printer + benchtop label wrapper |
| 8 | [Placement](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/08-placement-in-autosampler.md) | Grip the 12 mm capped, labeled vial, place it into a numbered tray slot | Agilent 100-position autosampler tray |

Reading down the **last column**: every messy specialized motion
(dosing powder, sonicating, applying labels) sits in a **stationary
station**. The arm only ever shuttles labware between them. That is
how we get away with one gripper.

Reading down the **third column**: only two steps need anything beyond
"grip and move." Step 4 needs **closing force** to push a plunger.
Step 6 needs **wrist rotation with torque feedback** to screw on a
cap. Both are standard cobot features.

## Can one gripper do all eight steps? Yes.

Concretely, the gripper has to handle:

- Objects from **10 mm** (cap) to **50 mm** (flask body) wide.
- **Glass**, so soft pads or low closing force.
- **Plunger pressing** for Step 4 — gripper closes onto a plunger
  cap and pushes down.
- **Cap torquing** for Step 6 — the gripper holds the cap rigidly
  while the arm's wrist rotates.

A single adaptive parallel-jaw gripper with a 0–50 mm stroke, soft
silicone fingertips, and a force-control mode covers all four. No
tool changer is needed. Nothing case-specific to paracetamol forces a
second gripper.

## Arm pick — Universal Robots UR5e

This is the arm we recommend for both cases (paracetamol and ketchup).
The reasoning below is the same in
[`../ketchup/02-hardware-choice.md`](../ketchup/02-hardware-choice.md);
read it once.

**UR5e at a glance:**

| Spec | Value | Why it matters here |
|---|---|---|
| Reach | **850 mm** | Spans an ~1.0 m bench cell from a central mount |
| Payload | **5 kg** | Flask + cap + gripper ≈ 700 g — well within |
| Joints | 6, including **continuous wrist rotation** | Wrist spin is what tightens the screw cap in step 6 |
| Repeatability | ±0.03 mm | An order of magnitude tighter than any opening we aim at |
| Built-in sensor | **6-axis wrist force/torque sensor** | Drives plunger push (step 4) and cap torque (step 6) |
| Approx. price | ~$36,000 new | Mid-range cobot |
| Simulation | First-party [`Universal_Robots_ROS2_Driver`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver), [`Universal_Robots_ROS2_GZ_Simulation`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation), MoveIt 2 config | Best-supported arm in open-source robotics |

The UR5e's wrist FT sensor is the single feature that lets us avoid
buying a more expensive joint-torque arm. It is good enough for the
two force-sensitive steps in our list (push the plunger, twist the
cap), and the Quantos doser handles the only step where milligram
precision actually matters.

### Competitor 1 (rejected) — Franka Research 3 (FR3)

- 7 joints, **joint torque on every joint**, ±0.1 mm, 855 mm reach.
- Approx. ~$15,000 at the research-academic price.
- First-party `franka_ros2` + `franka_description`.

Strong in theory. We rejected it for two reasons:

1. **Payload is 3 kg.** Once we add the Robotiq Hand-E (~0.9 kg) plus
   a syringe filled with solvent and connected to a filter (~0.6 kg),
   we are at 1.5 kg with no headroom for the dynamic forces of a
   pushing motion. UR5e gives us 5 kg.
2. **Joint torques are wasted here.** They shine when the arm is the
   dispenser (e.g. holding a peristaltic-pump nozzle). In our cell the
   pump is on a *stationary* mount — bead-break detection moves out of
   the arm and onto the balance's mass-vs-time signal. The UR5e wrist
   FT sensor covers everything we actually do.

If at v2 we put the pump on the arm, the FR3 becomes worth a
revisit. For v1 the UR5e is plain better.

### Competitor 2 (rejected) — Kinova Gen3 (7-DOF)

- 7 joints, joint torques on every joint, 4 kg payload, **902 mm
  reach** (best on paper).
- Approx. ~$30,000.
- Official `ros2_kortex` driver.

We rejected it on **simulation maturity**. The Kinova Gazebo plugin
lags ROS 2 releases by months, and the description URDF has been
through breaking changes recently. The teaching value of "follow the
upstream UR docs and have a sim running in an afternoon" is
significant for this project. If Kinova's sim story stabilises at v2
we revisit.

## Gripper pick — Robotiq Hand-E

Same gripper for both cases.

| Spec | Value | Why it matters here |
|---|---|---|
| Stroke | **0–50 mm** | Spans the 10 mm cap to the 50 mm flask body |
| Force | 20–185 N, **force-controlled** | Soft enough not to crack glass, strong enough to push a syringe plunger |
| Finger pads | **Swappable silicone** | Grips glass without slipping |
| Mass | 0.9 kg | Within UR5e payload |
| Driver | First-party Robotiq UR Toolio + ROS 2 driver from [PickNik](https://github.com/PickNikRobotics/robotiq) | Drops in next to the UR5e simulation |
| Approx. price | ~$5,000 | The smallest of Robotiq's lineup |

### Why this single gripper covers all 8 steps

| Step | Hand-E action |
|---|---|
| 1 | Grips the 35 mm flask neck at ~40 N. Slides the draft-shield door with the closed-fingertip contour. |
| 2 | Same flask grip; carries it into the sonicator basket. |
| 3 | Grips the 25 mm pipette handle at ~30 N. Pipette is electronic, so the dispense itself is a USB / Bluetooth command — no plunger to press. |
| 4 | Grips the 16 mm syringe barrel, then **closes onto the plunger top with force-controlled motion** to push fluid through the filter. The wrist FT reads back-pressure. |
| 5 | Pipette again. |
| 6 | Grips a 10 mm cap from a spring-loaded cap dispenser. Wrist rotates with torque feedback to "firm but not jammed." |
| 7 | Holds the vial upright; the label wrapper does the actual wrap. |
| 8 | Grips the 12 mm vial body. Drops it into the tray slot. |

### Gripper competitor 1 (rejected) — Robotiq 2F-85

- 85 mm stroke (handles larger labware than we need).
- Same ecosystem and driver as Hand-E.

Rejected because **the larger stroke buys us nothing** here, and the
2F-85's fingertip surfaces are coarser than Hand-E's, slightly less
secure on small (12 mm) vials. Hand-E is the cleaner pick.

### Gripper competitor 2 (rejected) — OnRobot RG2-FT

- Built-in 6-axis force/torque sensor *in each finger* — exquisite
  contact sensing.
- Cost ~$10,000.

Rejected because the **UR5e wrist FT already handles** our two
force-sensitive steps, and RG2-FT is double the price of Hand-E with
no other gain we can use.

## Step 1 dispenser pick — Mettler Toledo XPR226 + Quantos QB1

The arm and gripper are case-independent. The **Step 1 dispenser** is
not — for paracetamol it must dose a dry powder to ±0.1 mg.

| Spec | Value |
|---|---|
| Balance | Mettler Toledo **XPR226** (220 g capacity, 0.1 mg readability) |
| Doser | Mettler **Quantos QB1** powder-dosing module with QH-series heads |
| Head technology | RFID-tagged sealed cartridge; ionising bar inside; closed-loop on balance reading |
| Target mass | 1 mg – 5 g (we use ~5 mg) |
| Accuracy at 5 mg | ±0.1 mg |
| Approx. price | ~$35,000 new |
| What the arm has to do | Open the draft-shield door; place the flask; close the door; trigger the Quantos via a serial command; wait; open the door; remove the flask |

### Dispenser competitor 1 (rejected) — Sartorius Cubis II + Q-App auto-dispensing

Strong product line, competitive accuracy. We **rejected** it because
its automation hooks (Q-App) are less openly documented than Quantos's
RFID + RS232 protocol, and the ROS-friendly community examples almost
all target Mettler. We do not lose accuracy by picking Mettler.

### Dispenser competitor 2 (rejected) — Vibri vibrating-chute doser (manual + balance)

A small vibrating chute that dispenses powder onto a manual balance.
Used in some teaching labs because it is cheap (~$2,000). **Rejected**
because it has no machine-readable protocol — the arm cannot tell it
"dispense 5 mg now," and you would still need a person to read the
balance. Fine for a benchtop demo, useless for a 50-vial run.

## The whole shopping list (paracetamol cell)

| Item | Pick | Approx. price |
|---|---|---|
| Arm | Universal Robots UR5e | ~$36,000 |
| Gripper | Robotiq Hand-E | ~$5,000 |
| Step 1 — dosing balance | Mettler XPR226 + Quantos QB1 | ~$35,000 |
| Step 2 — sonicator | Branson 1800 ultrasonic bath | ~$1,500 |
| Step 3 / 5 — pipette | Sartorius Picus 1000 µL + holster + tip rack | ~$1,500 |
| Step 4 — syringe-filter clamp | Custom 3D-printed jig + 10 mL Luer syringes + 0.45 µm filters | ~$200 |
| Step 6 — cap dispenser | Spring-loaded cap turret (custom) | ~$300 |
| Step 7 — label printer + wrapper | Zebra ZD421 + tabletop wrapper | ~$2,500 |
| Step 8 — autosampler tray | Agilent 100-position tray | ~$200 |
| Wrist camera | Intel RealSense D405 | ~$400 |
| Misc (mount, fiducials, cables) | — | ~$1,000 |
| **Total** | | **~$83,600** |

The Mettler Quantos is the single biggest line item. Drop it for v0
(use the Vibri chute and accept manual mass logging) and the cell
falls under $50k.

## Next

[`03-simulation-workflow.md`](03-simulation-workflow.md) walks through
**(a)** what the arm physically does at each step and **(b)** how we
implement that in ROS 2 + Gazebo + MoveIt 2.
