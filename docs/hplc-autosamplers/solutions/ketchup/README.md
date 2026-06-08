# Ketchup — Step 1 (Weighing) solution

> **In one line:** for the hard case (a sticky, viscous paste), a
> **7-axis force-sensing cobot** holds a positive-displacement syringe
> head over a beaker on a balance, and squeezes ketchup out a little
> at a time while the balance tells it when to stop.

This folder is the solution for the **ketchup** case of
**Step 1 — Weighing** in the eight-step workflow at
[robotics-research / 03-hplc-workflow / 01-weighing.md](https://github.com/RobinNagpal/robotics-research/blob/main/03-hplc-autosampler/03-hplc-workflow/01-weighing.md).
Read that file first. This folder assumes you understand what the step
is supposed to produce.

## What we are automating, in one paragraph

A lab technician needs to weigh about **5 grams** (5 g — roughly one
teaspoon) of ketchup straight into a small glass beaker, with the
answer accurate to **about 1 milligram**. Ketchup is sticky and clingy.
A spoon does not pour cleanly: some of it stays on the spoon, some
slides over the edge of the beaker, and it dribbles after you stop
spooning. Our solution removes the spoon and uses a **syringe-like
dispenser** that the robot holds. The balance closed-loops on the mass,
and the arm uses its built-in force sensors to detect when the bead
breaks off the nozzle.

## Why this case is the "hard" one

Compared to paracetamol, ketchup breaks every assumption:

- **Sticky, not free-flowing.** Gravity alone will not move it. You
  need positive pressure (a syringe piston, a peristaltic pump, or a
  pneumatic cylinder).
- **String-and-drip behaviour.** When the dispenser nozzle lifts away
  from the bead in the beaker, a thin string forms and then breaks.
  Some ketchup falls into the beaker after you "stopped." That extra
  drop can be 50–500 mg — way over our 1 mg target tolerance.
- **No clean off-the-shelf answer.** Mettler Toledo's Quantos handles
  powders and liquids, not pastes. Chemspeed sells a viscous-fluid
  head but it is part of a $300k+ workstation. Most food and beverage
  labs still weigh ketchup by hand for exactly this reason.
- **Larger target (5 g not 5 mg).** Good news: a thousand times less
  sensitive than the powder case. Bad news: a thousand times the
  cleaning effort if you spill it.

That is why we recommend a **fundamentally different arm** for this
case than for paracetamol. The arm itself does the dispensing here,
so it needs **real-time force sensing** at every joint — not just
"is the gripper closed."

## The three files in this folder

Read them in order. Each one is short.

1. **[`01-existing-solutions.md`](01-existing-solutions.md)** — what
   industry uses today for viscous dispensing on a balance (Watson-
   Marlow peristaltic pumps, Chemspeed VR heads, food-lab tricks).
2. **[`02-hardware-choice.md`](02-hardware-choice.md)** — which arm,
   which pump, which beaker, and why we picked them.
3. **[`03-simulation-workflow.md`](03-simulation-workflow.md)** — how
   we simulate the whole thing in ROS 2 + Gazebo + MoveIt 2, including
   the sticky-bead break that the force sensor has to detect.

## The headline picks

| What | We picked | Why |
|---|---|---|
| **Dispensing instrument** | Watson-Marlow **323Dud** peristaltic pump + 4 mm Marprene tubing | Standard food/beverage lab pick for thick fluids. Gravimetric closed-loop via serial. Cheap (~$2,500). |
| **Robot arm** | **Franka Research 3 (FR3)** — 7-DOF, joint torque sensors on every joint, 855 mm reach, ±0.1 mm repeatability | Joint-level force sensing detects the bead-break instantly. Seven joints let the arm pull straight up while keeping the nozzle vertical. First-party `franka_ros2` + URDF + Gazebo. ~$15k at research price. |
| **End-effector** | Custom 3D-printed nozzle holder + a Robotiq FT-300 wrist sensor (redundant with the joint torques but useful for nozzle Z-force) | Holds the pump's silicone outlet tube rigidly above the beaker |
| **Balance** | Mettler Toledo XPR1203S milligram balance (1.2 kg capacity, 1 mg readability) | Larger pan than the XPR226 to fit a 50 mL beaker. We do not need 0.1 mg here. |
| **Beaker** | 50 mL low-form Pyrex beaker | Holds 5 g of ketchup easily, fits XPR1203S pan |
| **Sensors** | Wrist RGB-D camera + a small overhead camera looking down into the beaker | Camera B watches the bead form and break — visual confirmation of what the force sensor already detected. |

Full reasoning, the alternatives, and why we did **not** reuse the
UR3e from the paracetamol case is in
[`02-hardware-choice.md`](02-hardware-choice.md).

## One arm for both cases, or two?

The user explicitly raised this: "it maybe possible that we may use
different robot for paracetamol or different for ketchup."

**Our answer: yes, different arms.** Concretely:

- **Paracetamol** — UR3e (precision and reach are easy, force sensing
  is "nice to have" for the draft-shield door, ROS support is the
  binding constraint).
- **Ketchup** — Franka Research 3 (force sensing is the **binding
  constraint** because the arm is the dispenser; one extra joint helps
  with the straight-up retraction).

You **could** force-fit a UR5e onto both jobs — its wrist 6-axis F/T
sensor is decent. But ketchup's bead-break detection is sensitive
enough that having torque feedback on every joint (FR3) noticeably
improves the catch rate. For a teaching project the right pick is the
one that makes the harder case work cleanly, not the cheaper one that
*almost* works.

If a follow-up project needed to share one arm across both cases, the
FR3 also covers the paracetamol case (with slightly worse precision —
±0.1 mm vs ±0.03 mm — which still hits an 80 mm pan trivially). The
reverse swap (UR3e on ketchup) is the brittle one.

## What this does **not** cover (and why)

- **Sample homogenisation.** Ketchup arrives in a sealed bottle and
  has to be **stirred** before any volume of it represents the whole.
  In a real lab this is a 5-minute manual stir. Out of scope for v1.
- **Cleaning between samples.** Sticky residue inside the pump tubing
  is a real problem and the v2 answer is a swappable disposable
  cartridge. v1 assumes one ketchup sample per simulation run.
- **The next seven workflow steps.** Each gets its own folder when we
  implement it.
- **Real hardware bring-up.** Sim-only for now.
