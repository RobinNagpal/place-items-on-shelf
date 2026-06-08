# 02 — Hardware choice for the ketchup case

Unlike the paracetamol case, **the arm itself is the dispenser** here.
That changes the shopping list. The previous file
([`01-existing-solutions.md`](01-existing-solutions.md)) already
narrowed the dispensing mechanism (peristaltic pump or positive-
displacement piston, gated by a balance). This file picks the arm.

## The shopping list

| Requirement | Number | Why |
|---|---|---|
| **Reach** | ≥ 60 cm | The arm has to span an inbound rack, the balance, and an outbound rack. Bigger workspace than paracetamol because the beaker + pump + tubing are bulkier. |
| **Repeatability** | ≤ 0.5 mm | A 50 mL beaker has a 4 cm opening — millimetre-level is fine. |
| **Payload** | ≥ 3 kg | A preeflow dispenser (~0.5 kg) + a glass beaker holder + safety pads. |
| **Force / torque sensing** | **on every joint** | Non-negotiable. We need to detect the string-break the moment it happens, in any direction. A wrist-only sensor catches z-axis but is blind to drag. |
| **Joint count** | ≥ 7 | A 7th joint lets the arm pull the nozzle straight up while keeping it vertical. With 6 joints, lifting straight up forces a wrist rotation. |
| **Open-source ROS 2 + Gazebo + MoveIt 2 support** | first-party | Same as paracetamol — sim-first project. |
| **Force-limited (safe near humans)** | yes | Same as paracetamol — bench-side technician. |

The "joint torque sensing on every joint" and the "≥ 7 joints" lines
together rule out the entire UR family and the entire Doosan family.
Both are 6-DOF with **wrist-only** force sensing.

## The shortlist

### Option A — Franka Research 3 (FR3) — the pick

- **Reach:** 855 mm
- **Joints:** 7
- **Payload:** 3 kg
- **Repeatability:** ±0.1 mm
- **Sensing:** joint torque sensor on **every** joint (7 of them)
- **Approx. price:** ~$15,000 at the research-academic price (commercial
  closer to $25k)
- **ROS 2 support:** first-party — [`franka_ros2`](https://github.com/frankarobotics/franka_ros2),
  [`franka_description`](https://github.com/frankarobotics/franka_description),
  Gazebo plugin maintained by Franka Robotics
- **Vendor page:** <https://franka.de/franka-research-3>

Why this is right:

- **String-break detection.** The string of ketchup hanging from the
  nozzle as the arm lifts away exerts a tiny downward drag — maybe
  20–80 mN. A joint-torque sensor on the elbow + shoulder + wrist
  picks that up cleanly. A wrist-only FT sensor (UR) detects only the
  z-component; if the bead tugs sideways (which it does on partial
  retractions), the wrist FT misses it.
- **7 joints = straight-up retraction with a vertical nozzle.** Crucial
  for not dragging extra paste out of the beaker on retract.
- **First-party simulation maturity.** TARMAC (the closest research
  paper) uses the FR3 in exactly this configuration. The sim path is
  well trodden.
- **Modest price for what it does.** $15k research price is comparable
  to a UR3e and dramatically less than a Mettler Quantos rig.

### Option B — Universal Robots UR5e (rejected)

- **Reach:** 850 mm
- **Joints:** 6
- **Repeatability:** ±0.03 mm
- **Sensing:** **wrist-only** 6-axis FT (built-in)
- **ROS 2 support:** first-party (best in class)
- **Approx. price:** ~$36,000

The UR5e is the obvious cheaper alternative. We reject it for two
reasons:

1. **Wrist-only FT is the wrong sensor placement for string detection.**
   The bead drags in arbitrary directions; wrist-only FT measures
   force on a single rigid body (the wrist + tool). With 6 axes the
   contribution of a sideways tug at the very tip is hard to separate
   from gripping torque artefacts. With joint torque on every link,
   the signature of a string tug is unmistakable.
2. **6 joints + straight-up retract = wrist rotation.** A 6-axis arm
   trying to lift the nozzle straight up while keeping it
   vertically aligned uses an awkward shoulder + wrist combination
   that often hits joint limits inside a draft-shield-style
   enclosure. The 7th joint of the FR3 makes this trivial.

If budget became a hard constraint at v2 and the bench is open (no
enclosure), UR5e is a defensible fallback. It is **not** the right v1
choice for a teaching project where we want the bead-break detection
to actually work first time.

### Option C — Kinova Gen3 (rejected)

- **Reach:** 902 mm
- **Joints:** 7
- **Repeatability:** ±0.5 mm
- **Sensing:** joint torque on all 7 joints
- **ROS 2 support:** first-party (`ros2_kortex`)
- **Approx. price:** ~$30,000

Specs are close to the FR3 on paper — even better reach. We reject it
on **simulation maturity** alone. The Kinova Gazebo plugin lags ROS 2
releases by months; the description package has been through breaking
changes recently. The TARMAC-style sim story is rougher. If Kinova's
sim story matures we revisit, but for now FR3 is the safer pick.

### Option D — Industrial 6-axis (Fanuc CRX-10iA, ABB GoFa, KUKA LBR iiwa)

The KUKA **LBR iiwa 7 R800** is interesting: 7 joints, joint torque on
every joint, ~800 mm reach. It is essentially the German industrial
sibling of the FR3. We reject it on price (~$80,000) and ROS 2 support
(community-maintained drivers only). For a future production v2 cell,
LBR iiwa is the natural upgrade.

## The decision

We pick **Option A — Franka Research 3 (FR3)** with no fallback for
v1. The decision rests on **joint torque sensing on every joint** plus
**7 joints**, both of which the cheaper alternatives lack.

## Dispenser sub-decision

Two candidates from
[`01-existing-solutions.md`](01-existing-solutions.md):

| Candidate | Pros | Cons | Pick |
|---|---|---|---|
| **Watson-Marlow 323Dud peristaltic** | Cheap (~$2,500), food-lab standard, no valves to clean | After-drip overshoot; struggles above ~10,000 cP | First pick — start here |
| **preeflow eco-PEN piston** | Cleaner shut-off, handles 100,000+ cP | Costlier (~$3,000), needs cleaning cycle between samples | Fallback if Watson-Marlow can't hit 1 mg tolerance |

We start with the Watson-Marlow because food-lab people will recognise
it and it has a serial-control protocol that is well-documented for
ROS 2. If the after-drip turns out to be larger than 5 mg in
simulation, we swap to the preeflow.

## Other hardware in the cell

| Item | Pick | Why |
|---|---|---|
| **Arm** | Franka Research 3 | See above |
| **Pump (primary)** | Watson-Marlow 323Dud + 4 mm Marprene tubing | Discussed above |
| **Pump (fallback)** | preeflow eco-PEN piston dispenser | Higher viscosity headroom |
| **End-effector** | Custom 3D-printed nozzle holder + Robotiq FT-300 wrist sensor | The FT-300 is redundant with joint torques but useful as a second source for direct Z-force when the nozzle approaches the surface |
| **Balance** | Mettler Toledo XPR1203S (milligram readability) | Larger pan than the XPR226 used in paracetamol; 1 mg is fine for a 5 g target |
| **Beaker** | 50 mL low-form Pyrex beaker | Right size for 5 g of ketchup, stable footprint on the pan |
| **Cameras** | Intel RealSense D405 on wrist + a small overhead RGB looking into the beaker | Wrist camera reads ketchup-bottle barcode; overhead watches the bead form / break |
| **Heat plate (v2)** | Small 30 °C plate under the source bottle | Thins ketchup viscosity; deferred to v2 to keep v1 simple |

## Cross-case comparison

How the two cases line up:

| | Paracetamol | Ketchup |
|---|---|---|
| **Arm role** | Carry labware to / from a dosing balance | Hold the dispenser nozzle and drive the dispense |
| **Arm** | UR3e (6-DOF, wrist FT) | Franka Research 3 (7-DOF, joint torque on every joint) |
| **Dispenser** | Mettler Quantos QB1 (powder, ±0.1 mg) | Watson-Marlow 323Dud peristaltic (paste, ±1 mg) |
| **Balance** | Mettler XPR226 (0.1 mg readability) | Mettler XPR1203S (1 mg readability) |
| **Target mass** | ~5 mg | ~5 g (1000× more) |
| **Hardest skill** | Sliding the draft-shield door without breaking glass | Detecting the string-break on retract |
| **Approx. arm + dispenser hardware cost** | $28k (UR3e) + ~$35k (Mettler XPR + Quantos) | $15k (FR3) + ~$2.5k (Watson-Marlow) + ~$15k (Mettler XPR1203S) |

The two cases need different hardware for honest engineering reasons —
the **binding constraint differs**: precision-of-dispense for
paracetamol, force-feedback-on-retract for ketchup. The two arms are
*both* easy to simulate in ROS 2, so the project can build the two
cells in parallel without compatibility headaches.

## Next

[`03-simulation-workflow.md`](03-simulation-workflow.md) — the Gazebo
world, the ROS 2 packages, the motion sequence, and the bead-break
detector.
