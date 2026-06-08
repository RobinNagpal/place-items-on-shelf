# 02 — Hardware choice for the paracetamol case

The previous file ([`01-existing-solutions.md`](01-existing-solutions.md))
showed that the **dosing balance does the milligram-level work**. Our
robot arm only carries labware around it. So the arm shopping list is
the easier one:

- **Reach** ≥ 40 cm — enough to span an in-rack vial, the balance pan,
  and an outgoing vial slot on the same bench.
- **Repeatability** ≤ 0.1 mm — the balance pan is 80 mm wide; ±1 mm
  would already be fine; we ask for an order of magnitude tighter as
  margin.
- **Payload** ≥ 1 kg — a 100 mL volumetric flask weighs ~200 g empty,
  ~280 g full. A 2 mL HPLC vial weighs ~10 g.
- **Bench-friendly footprint** — must sit on the same 60 × 90 cm
  benchtop as the balance.
- **Open-source ROS 2 + Gazebo + MoveIt 2 support** — non-negotiable
  for our sim-first workflow.
- **Soft / force-limited motion** — the arm reaches inside a
  glass-walled draft shield with the doors open. A bumped door breaks
  glass and resets the day.

## The four candidate families

Robot arms split into four geometry families. Each has a typical "what
it is good at":

| Family | Geometry | Strength | Weakness |
|---|---|---|---|
| **Industrial 6-axis** | 6 rotating joints, big base | Best repeatability, highest payload | Heavy, expensive, needs safety cage |
| **Cobot** (collaborative 6-axis) | 6 rotating joints, force-limited | Safe near humans, easy to teach, good ROS support | Lower repeatability than industrial |
| **SCARA** | 4 axes — two horizontal arms + one vertical + one wrist rotation | Very fast and precise in flat pick-and-place | Cannot tilt its tool, limited shape |
| **Cartesian / gantry** | XYZ rails plus a rotating wrist | Cheap to build, very precise | Big footprint, restricted to right angles |

For loading a balance pan on a flat bench, **SCARA and Cartesian
gantries are technically the best fit** — the motion is "lift, move
horizontally, lower." But neither has a strong open-source ROS 2
simulation story for beginners.

**Industrial 6-axis** is overkill. We do not need 0.02 mm repeatability
and we do not want a safety cage in a teaching project.

**Cobot** trades a tiny bit of precision for huge ROS / simulation
support — and the precision we lose does not matter because the
Quantos sets the mass.

So the real choice is **SCARA (production answer) vs. cobot
(beginner / simulation answer).** Below is the comparison.

## The shortlist

### Option A — Epson G6-553S SCARA (the production answer)

- **Reach:** 550 mm
- **Payload:** 6 kg
- **Repeatability:** ±0.015 mm in XY, ±0.010 mm in Z
- **Tool:** any standard mechanical end-effector mounted on the
  rotating Z-axis
- **Approx. price (new):** ~$15,000
- **ROS 2 support:** community xacro / URDF only — **no official
  driver, no first-party Gazebo SDF**
- **Vendor page:** <https://epson.com/For-Work/Robots/SCARA/Epson-G6-SCARA-Robots---550mm/p/RG6-553ST13>

In a real lab this is the right pick. The SCARA geometry matches the
"lift, slide, drop" motion of balance loading exactly. Repeatability
is over an order of magnitude tighter than any cobot. It is also
faster — cycle times under one second for a typical pick-and-place.

The catch: in our **sim-first** workflow this arm is hard to teach.
Epson's official driver runs on Windows under their own RC+ language;
there is no first-party `epson_description` URDF, no `epson_ros2`
driver, and no Gazebo plugin from Epson. Community packages exist but
they are not beginner-friendly and they drift behind the supported
ROS distribution.

### Option B — Universal Robots UR3e (the project answer)

- **Reach:** 500 mm
- **Payload:** 3 kg
- **Repeatability:** ±0.03 mm
- **Built-in 6-axis force/torque sensor** in the wrist (useful for
  draft-shield-door touch detection and "soft" approaches near
  glass)
- **Approx. price (new):** ~$28,000
- **ROS 2 support:** **first-party** —
  [`Universal_Robots_ROS2_Description`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver)
  for URDF,
  [`Universal_Robots_ROS2_GZ_Simulation`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation)
  for Gazebo, official MoveIt 2 config, and active community
- **Vendor specs:** <https://www.universal-robots.com/media/1807464/ur3e_e-series_datasheets_web.pdf>

A UR3e is twice the price of the Epson, and ten times less repeatable.
For this task, neither difference matters. The flask just needs to
land on an 80 mm pan; ±0.03 mm is laughably tight for that. And the
Quantos still does the dispensing, so flask-position accuracy never
turns into mass-measurement accuracy.

What we gain is huge:

- First-party Gazebo SDF and MoveIt config — anyone who follows the
  upstream [Universal Robots ROS 2 docs](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver)
  can replicate the simulation in an afternoon.
- A wrist-mounted 6-axis force/torque sensor — handy for "stop the
  moment the gripper touches the door."
- Active community examples for exactly the kind of motion we need
  (open a door, place an object, close a door).

### Option C (rejected) — Mitsubishi RV-2FRL industrial 6-axis

Specs are excellent (±0.02 mm, 2 kg payload, 504 mm reach, ~$13k
used). But it is built for caged industrial cells, not a benchtop
shared with a human technician. The safety-rated stop modes are weak
without a contactor cabinet, and the ROS 2 driver
([`mitsubishi_melfa_ros_driver`](https://github.com/Mitsubishi-Electric-Automation/mitsubishi_melfa_ros_driver))
only recently came online. Skip for v1.

### Option D (rejected) — myCobot 280 Pi

Used elsewhere in this repo for the **tray loading** task (Step 8 of
the workflow). For Step 1, the 280 mm reach is too short to span
"in-rack vial + balance pan + scan station" without moving the
balance — which we explicitly do not want, because every move of the
balance forces a recalibration. The 280's repeatability (±0.5 mm) is
borderline OK for an 80 mm pan but tight against the draft-shield
opening. Skip it.

## The decision

We pick **Option B — Universal Robots UR3e**.

The trade-off is explicit: **we trade ~$13k of price and 2× of
nominal precision for a first-party ROS 2 / Gazebo / MoveIt 2 stack
and a built-in force sensor.** In a beginner-friendly, sim-first
project this is the right call, because:

- the precision difference never reaches the measured mass,
- the simulation tooling difference shows up on day one,
- the force sensor gives us "do not break the glass door" out of the
  box.

If the project moves to real hardware at v2 and the budget is the
binding constraint, switch to **Option A — Epson G6-553S SCARA**. The
MoveIt-level workflow code we write against the UR3e ports to the
SCARA with only the URDF changing — the planning, gripper, and
balance-control logic stay the same.

## Other hardware in the cell

The arm is only one of six items. The complete shopping list:

| Item | Pick | Why |
|---|---|---|
| **Analytical balance** | Mettler Toledo XPR226 (220 g capacity, 0.1 mg readability) | Industry standard, drives Quantos directly |
| **Powder doser** | Mettler Quantos QB1 + QH-series powder dosing head | The actual fine-precision dispenser. ±0.1 mg at 5 mg. |
| **Robot arm** | Universal Robots UR3e | See the discussion above |
| **Gripper** | Robotiq 2F-85 with soft silicone pads | Holds glass without cracking, 85 mm opening fits flasks |
| **Wrist camera** | Intel RealSense D405 (close-range RGB-D) | Reads the vial barcode and verifies labware seating |
| **Bench fiducial** | One ArUco tag on the balance base, one on the rack | Lets the arm re-zero its world frame after a bump |

The arm is not strictly necessary for a 5-tablet study — a human can
load the Quantos in 60 seconds. The arm pays off when the workflow
chains together: weigh → dissolve → dilute → filter → vial → cap →
label → tray. With one arm running the whole eight-step chain
unattended, the hourly throughput jumps from a few samples per hour to
a few samples per minute.

## Next

[`03-simulation-workflow.md`](03-simulation-workflow.md) shows how we
actually drive the UR3e through the weighing step inside Gazebo.
