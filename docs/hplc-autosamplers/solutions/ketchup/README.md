# Ketchup — full 8-step automated cell

> **In one line:** the **same UR5e + Robotiq Hand-E** as the
> paracetamol case, but the Step 1 dispenser is a **Watson-Marlow
> peristaltic pump on a Mettler XPR1203S balance**, and there is one
> extra **centrifuge** station between Steps 3 and 4 to clarify the
> pulpy extract.

This folder is the solution for the **ketchup** case of the eight-step
workflow at
[robotics-research / 03-hplc-workflow](https://github.com/RobinNagpal/robotics-research/tree/main/03-hplc-autosampler/03-hplc-workflow).
Read those eight files first.

## Why this is the "hard" case

Ketchup breaks the paracetamol assumptions:

- **Sticky paste, not free-flowing powder.** Gravity alone will not
  dispense it. We need a peristaltic pump pushing it through tubing.
- **String-and-drip on dispense end.** When the pump stops, a string
  of ketchup hangs from the nozzle and dribbles a few hundred
  milligrams more before it lets go. The pump's slowdown ramp + the
  balance's after-drip reading handle this; the arm is not in the
  loop.
- **Pulp in the extract.** After Step 2 the liquid is cloudy and full
  of solids. A 0.22 µm filter on the syringe would clog instantly —
  so a **centrifuge** sits between extract and filter to clarify the
  liquid first. That is the only new station vs. paracetamol.
- **More vials per run.** Food assays typically use multiple supplier
  batches × 2-3 repeats. The arm's pick-and-place into the autosampler
  tray scales linearly — not a hardware problem, but a worklist
  problem.

That is what makes ketchup the **second** case to bring up — once the
paracetamol cell is reliable, the ketchup cell reuses 90 % of the
same code and most of the same hardware.

## One arm and one gripper for **both** cases

The earlier draft of this folder picked a **Franka Research 3** for
ketchup, on the theory that joint-torque sensing would be needed for
arm-side bead-break detection. We have since moved the pump nozzle
**off the arm** and onto a stationary mount. The bead-break now
happens between the fixed nozzle and the beaker, not between the arm
and anything. With the pump stationary, the joint-torque argument
disappears, and the UR5e + wrist FT picked for paracetamol covers
ketchup just as well.

That convergence is the headline finding of the all-8-steps analysis
in [`02-hardware-choice.md`](02-hardware-choice.md): **the same arm
and the same gripper run both cases.**

## The three files in this folder

1. **[`01-existing-solutions.md`](01-existing-solutions.md)** — short
   summary of how labs do viscous-paste weighing today, and which
   pattern we copy.
2. **[`02-hardware-choice.md`](02-hardware-choice.md)** — the **main
   reasoning** file. Walks all eight (+ a centrifuge) workflow steps
   from the gripper's point of view, confirms the UR5e + Hand-E pick,
   then picks the Step 1 dispenser (Watson-Marlow 323Dud +
   Mettler XPR1203S). Two rejected competitors per pick.
3. **[`03-simulation-workflow.md`](03-simulation-workflow.md)** —
   **(Part 1)** what the arm physically does at every step, in the
   same plain English the upstream workflow uses. **(Part 2)** how
   that maps to ROS 2 + Gazebo + MoveIt 2 calls.

## Headline picks

| | Pick | Why |
|---|---|---|
| **Arm** | Universal Robots UR5e | **Same as paracetamol** — see [`02-hardware-choice.md`](02-hardware-choice.md). |
| **Gripper** | Robotiq Hand-E | **Same as paracetamol** — 50 mm stroke fits beaker, vial, cap. |
| **Step 1 dispenser** | Watson-Marlow 323Dud peristaltic pump + Mettler XPR1203S balance | Standard food-lab pattern. Mass-feedback closed loop. ±1 mg at 5 g. |
| **Step 2 station** | IKA C-MAG hot plate + magnetic stirrer | Heated extraction; thins the paste, brings 5-HMF into the water. |
| **Step 3a (new) station** | Eppendorf 5424 microcentrifuge | Drops the pulp; supernatant pipetted into the dilution flask. |
| **Filter pore size** | 0.22 µm PVDF | Tighter than paracetamol's 0.45 µm. Required for food. |

The arm and gripper are identical to the paracetamol cell. Only the
Step 1 dispenser, the Step 2 mixing station, and the new Step 3a
centrifuge differ.

## What this does **not** cover (and why)

- **Sample homogenisation.** Stirring a sealed ketchup bottle so the
  spoonful is representative — still a manual pre-step.
- **Cleaning between samples.** Sticky residue in the pump tubing is
  real. v2 swaps to a single-use cartridge or a flush cycle.
- **Real hardware bring-up.** Sim-only for now.
- **Other food variations.** v1 is the standard 5-HMF in ketchup
  assay; jams, sauces, mayonnaise, syrups are deferred to v2.
