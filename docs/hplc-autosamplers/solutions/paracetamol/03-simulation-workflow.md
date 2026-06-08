# 03 — Simulation workflow for the paracetamol case

This file has **two halves**:

1. **What we are trying to do** — the physical workflow, exactly as a
   human technician performs it on a real bench. No code. No software.
   Just "pick up the flask, walk to the balance, place it." Read this
   first so you know what the arm is replacing.
2. **How we implement it with the arm in simulation** — the ROS 2 +
   Gazebo + MoveIt 2 plan that drives the arm through the same motions.

This separation is deliberate. The mistake is jumping straight to
"`MoveGroupInterface::setPoseTarget(...)`" without first agreeing on
what real action that pose is supposed to perform.

---

# Part 1 — What we are trying to do (the physical workflow)

A human technician runs the eight-step paracetamol assay. The
simulation reproduces exactly this sequence, only with the
technician's hand replaced by the arm.

## The bench, as the technician sees it

A 1.2 m × 0.6 m bench, left to right:

```
 [ inbound ] [ balance ] [ sonicator ] [ pipette ] [ vol-flask ] [ filter ]
   rack       + Quantos                  holster    rack         clamp
                                                                       
 [ vial rack ] [ cap   ] [ label printer ] [ autosampler ]
                dispenser    + wrapper       tray (100 slot)
```

The technician stands in front of it and works left to right, one
sample at a time.

## The eight physical actions, in plain English

| # | What the technician does at this step | Result at the end |
|---|---|---|
| **1 — Weigh** | Take an empty 100 mL volumetric flask from the inbound rack. Slide the balance's glass door open. Place the flask on the pan. Close the door. Press TARE on the balance. Open the door, swing the Quantos dosing head over the flask, close the door, press START. Wait while the Quantos drips powder until the balance reads 5.0 mg. Open the door, swing the head out, remove the flask. | Flask holds 5.0 mg of pure paracetamol powder. |
| **2 — Dissolve** | Take a 1000 µL pipette from its holster, draw 10 mL of methanol (in ten 1 mL aliquots) and squirt it into the flask. Drop the flask into the ultrasonic bath. Wait 3 min. Pull the flask out. | Flask holds 10 mL of clear paracetamol-in-methanol stock solution. |
| **3 — Dilute** | Pick up an empty 10 mL volumetric flask from the rack. Pipette exactly 1 mL of the stock solution into it. Pipette methanol up to the 10 mL mark. Swirl to mix. Repeat once more (1 mL of *that*) to get a 1:100 dilution. | A 10 mL flask of ~100 µg/mL paracetamol — the comfortable detector range. |
| **4 — Filter** | Suck the diluted solution into a 10 mL syringe. Screw a 0.45 µm filter onto the syringe tip. Set the tip over the next station's destination beaker. Push the plunger slowly, letting the first ~0.5 mL go to waste, then catching the clean stream. | A clean, filtered ~5 mL of paracetamol solution. |
| **5 — Transfer to vial** | Hold the syringe (or the pipette, depending on how step 4 caught the liquid) over an empty 2 mL HPLC vial. Squirt in ~1.5 mL — leave a little headspace. | A 2 mL vial with ~1.5 mL of clean liquid. |
| **6 — Cap** | Take a screw cap from the dispenser. Set it on the vial. Twist clockwise with a light wrist motion until it feels firm — about 1 N·m of torque. Stop. | A sealed, cross-thread-free vial. |
| **7 — Label** | The Zebra printer has already printed a sticker for this vial's Sample ID. Pick up the vial, present it to the rotating label wrapper, the wrapper wraps the sticker around. | A labeled, capped, filled vial. |
| **8 — Place** | Carry the vial to the autosampler tray. Look at the worklist — say it says "slot 3." Set the vial gently into slot 3. | One row of the worklist completed. |

That is the workflow. Whatever the simulation does later in this file
**has to map back to this table** — if a step in code does not
correspond to a row above, it is wrong.

## The two physical actions that need force feedback

Most of the workflow is "move object from A to B." Two actions need
something extra:

- **Step 4 — push the plunger.** Too gentle and nothing flows. Too
  hard and the filter membrane bursts. The technician's thumb learns
  the right pressure. The arm uses the wrist FT sensor on the UR5e.
- **Step 6 — torque the cap.** Too loose and the seal leaks. Too
  tight and the glass cracks. The technician's wrist learns "click."
  The arm watches wrist torque while the wrist rotates.

Everything else is positioning, holding, releasing.

---

# Part 2 — How we implement it with the arm in simulation

We now build the same sequence in software. The simulation runs on
**Linux + ROS 2 Jazzy + Gazebo Harmonic + MoveIt 2**.

## What we simulate and what we fake

| Real world | Sim treatment |
|---|---|
| **UR5e arm + Hand-E gripper** | Full URDF, full physics, full MoveIt — same as on real hardware |
| **Bench, racks, stations** | Static collision meshes in the SDF, no physics |
| **Liquid (methanol, paracetamol solution)** | **Not simulated.** Liquid is "in" a flask if the orchestration node says so. The flask volume is just a number tracked outside Gazebo. |
| **Powder dispensing** | ROS 2 service `/quantos/dispense_powder(target_mg) → actual_mg`. Returns target ± noise. No physics. |
| **Sonicator timing** | ROS 2 service `/sonicator/sonicate(seconds)`. Blocks for `seconds` of sim time, then returns. |
| **Pipette dispensing** | ROS 2 service `/pipette/dispense(volume_uL) → actual_uL`. Returns target ± noise. |
| **Syringe + filter resistance** | A small node publishes a simulated back-pressure on `/syringe/back_pressure_N`; the demo node closes the gripper at force-control mode until the cumulative pushed volume matches the target. |
| **Cap-thread torque profile** | A small node publishes simulated reaction torque on `/cap/reaction_torque_Nm` as a function of cap angle; the arm watches it via the wrist FT and stops at 1 N·m. |
| **Label printer + wrapper** | ROS 2 service `/labeler/wrap(barcode)` that returns when "applied." |
| **Autosampler tray** | A 100-position grid of poses, each one a named target in the SDF. |

Note what we do NOT simulate: any fluid mechanics, any thermodynamics,
any particle physics. The simulation models the **control loops** the
arm uses, nothing else.

## ROS 2 packages we add to the workspace

| Package | Source | Role |
|---|---|---|
| [`ur_description`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description) | first-party | UR5e URDF |
| [`ur_simulation_gz`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation) | first-party | Gazebo + ros2_control wiring |
| [`ur_moveit_config`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver) | first-party | MoveIt 2 SRDF + planning config |
| [`robotiq_hande_description`](https://github.com/PickNikRobotics/robotiq) | community | Hand-E URDF + open / close controllers |
| **`paracetamol_cell_world`** | this repo (new) | SDF for the bench + every station + the mock service nodes |
| **`paracetamol_cell_demo`** | this repo (new) | Orchestration node that drives the 8 steps |

Four of six are upstream. Two we write.

## The orchestration node

`paracetamol_cell_demo` exposes one node: `run_assay`. It owns the
state machine for one sample. The state machine has eight states,
one per workflow step. Each state:

1. Plans and executes the MoveIt 2 motions for its physical action.
2. Calls any required mock services (Quantos, sonicator, pipette,
   labeler).
3. Emits a JSONL log line on success.
4. Transitions to the next state.

The state machine is implemented in plain Python (`rclpy`), not in
BehaviorTree or SMACH — we want the code to read like the table in
Part 1.

## Step-by-step implementation, one row per workflow step

The table below maps each row of the Part-1 physical workflow to the
ROS 2 / MoveIt calls that perform it. `pose_*` names refer to named
targets defined in the URDF SRDF.

| Workflow step | ROS 2 calls performed by `run_assay` |
|---|---|
| **1 — Weigh** | `move_arm("above_inbound_slot")` → `gripper_close(35 mm, 40 N)` → `move_arm("above_balance")` → `compute_cartesian_path("push_door_open")` → `move_arm("above_pan")` → `move_arm("place_on_pan")` → `gripper_open()` → `move_arm("retract")` → `compute_cartesian_path("push_door_closed")` → call `/quantos/dispense_powder(5.0)` and **wait** → `compute_cartesian_path("push_door_open")` → `move_arm("above_pan")` → `gripper_close(35 mm, 40 N)` → `move_arm("retract_with_flask")` → `compute_cartesian_path("push_door_closed")` |
| **2 — Dissolve** | `move_arm("above_pipette_holster")` → `gripper_close(25 mm, 30 N)` (pick up pipette) → `move_arm("above_solvent_bottle")` → call `/pipette/aspirate(1000)` → `move_arm("above_flask_in_outbound")` → call `/pipette/dispense(1000)` → repeat the aspirate / dispense loop **10 times** to deliver 10 mL → `move_arm("pipette_holster")` → `gripper_open()` (return pipette) → `move_arm("grasp_flask")` → `gripper_close(35 mm)` → `move_arm("above_sonicator")` → `move_arm("inside_sonicator")` → `gripper_open()` → call `/sonicator/sonicate(180)` → `gripper_close(35 mm)` → `move_arm("above_sonicator")` |
| **3 — Dilute** | `move_arm("above_volflask_rack")` → `gripper_open()` → grab fresh 10 mL flask → repeat the pipette pickup → aspirate / dispense → release pipette pattern. The orchestration node knows the source-flask volume and the target-flask volume and converts each dispense into an actual fluid update. |
| **4 — Filter** | `move_arm("above_syringe_rack")` → `gripper_close(16 mm)` → `move_arm("above_filter_clamp")` → `gripper_open()` (set syringe in clamp; clamp holds it) → `move_arm("above_plunger")` → `gripper_close_with_force(target_force_N=4)` → **closed-loop force control**: while `/syringe/back_pressure_N` < threshold and pushed volume < target, decrement gripper width. |
| **5 — Transfer to vial** | Pipette pattern (same as steps 2 / 3) targeting an empty 2 mL vial on the vial rack. Aspirate 1500 µL, move over vial, dispense. |
| **6 — Cap** | `move_arm("above_cap_dispenser")` → `gripper_close(10 mm, force=15 N)` → `move_arm("above_vial")` → `move_arm("seat_cap")` → run a `RotateWristToTorque` action: rotate `wrist_3_joint` clockwise at 0.05 rad/s while watching `/wrench` Z-torque; stop when Z-torque ≥ 1.0 N·m. |
| **7 — Label** | `move_arm("above_vial_holder")` → `gripper_close(12 mm)` → `move_arm("above_label_wrapper")` → call `/labeler/wrap(barcode)` → wait for response → `move_arm("retract")`. |
| **8 — Place** | `move_arm("above_tray_slot_N")` (N from the worklist) → `move_arm("inside_tray_slot_N")` → `gripper_open()` → `move_arm("retract")` → `move_arm("home")`. |

Each line of the right column is a real `rclpy` call. There is no
hidden cleverness — exactly the operations the human did in Part 1.

## The closed-loop force controller for Step 4

The plunger push is the most interesting line in the table. Pseudocode:

```python
def push_plunger_until_volume(target_uL):
    target_force = 4.0  # newtons
    while pushed_uL < target_uL:
        gripper.close_step(delta_mm=0.1, force_limit_N=target_force)
        wait(0.02)                     # 50 Hz loop
        back_pressure = read("/syringe/back_pressure_N")
        if back_pressure > target_force * 1.2:
            raise RuntimeError("Filter blocked")
        pushed_uL = lookup_pushed_volume()
```

The loop closes on **back-pressure**, not on plunger position — that
way a partially clogged filter slows the push instead of bursting it.
In the real world the same loop closes on the UR5e wrist FT reading
directly; in sim we publish a simulated back-pressure that grows
linearly with pushed volume.

## The wrist-torque controller for Step 6

```python
def screw_cap_to_torque(target_Nm=1.0):
    rate = 0.05            # rad/s, slow
    arm.start_wrist_rotation(rate)
    while True:
        wrist_torque_z = read("/wrench").torque.z
        if abs(wrist_torque_z) >= target_Nm:
            arm.stop_wrist_rotation()
            return
        if abs(wrist_torque_z) < 0.01 and elapsed > 5:
            raise RuntimeError("Cap not engaging thread")
```

Again the loop reads wrist torque (UR5e's wrist FT) and stops on a
threshold. The sim mock publishes a torque that grows as the cap
turns, plus noise.

## How to run it (three terminals — same shape as exercise 21)

```bash
# Terminal A — Gazebo + UR5e + ros2_control + RViz
ros2 launch paracetamol_cell_world paracetamol_cell.gazebo.launch.py

# Terminal B — MoveIt 2 (UR5e planner action server)
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e

# Terminal C — the demo
ros2 launch paracetamol_cell_demo run_assay.launch.py \
    sample_id:=PARA_BATCH_47_S01 \
    target_mg:=5.0 \
    tray_slot:=3
```

Expected console output on a successful run — read this together with
the Part-1 table; every line maps to one row there.

```
[ 1 ] [weigh    ] flask grasped, draft-shield open, on pan
[ 1 ] [weigh    ] quantos dispensed 5.0001 mg in 12.4 s
[ 1 ] [weigh    ] draft-shield closed, flask retrieved
[ 2 ] [dissolve ] pipette delivered 10000 µL of methanol in 10 cycles
[ 2 ] [dissolve ] sonicator ran 180 s; flask retrieved
[ 3 ] [dilute   ] 1 mL of stock into 10 mL flask, swirled
[ 3 ] [dilute   ] 1 mL of dilution into 10 mL flask, 1:100 reached
[ 4 ] [filter   ] plunger push: 5000 µL pushed at 3.8 N back-pressure
[ 5 ] [transfer ] 1500 µL into vial 12-mm OD
[ 6 ] [cap      ] wrist torque reached 1.0 N·m at 124°
[ 7 ] [label    ] barcode PARA_BATCH_47_S01 wrapped
[ 8 ] [place    ] vial seated in tray slot 3
{"sample_id":"PARA_BATCH_47_S01","target_mg":5.0,"actual_mg":5.0001,
 "tray_slot":3,"timestamp":"2026-06-08T16:42:11Z","status":"ok"}
```

## "Done when" criteria

- The eight-step state machine completes without `plan` or `execute`
  failures, ten times in a row.
- The flask is on the balance pan in step 1 (verified by the wrist
  camera seeing the balance's ArUco tag inside a 5 cm × 5 cm window).
- The Quantos service returns a non-error response and the reported
  actual mass is within ±0.2 mg of the target.
- The Step-4 force loop completes the target volume without the
  back-pressure exceeding the threshold (no burst filter).
- The Step-6 torque loop reaches 1.0 N·m at a wrist angle between 90°
  and 270° (a sensible cap engagement range).
- The vial ends up in the correct tray slot (verified by the wrist
  camera reading the slot's ArUco tag during retract).
- The JSONL log line is written.

End-effector accuracy is *not* a success criterion — the Quantos sets
the mass, and the autosampler-slot tolerance (±1 mm) is way larger
than the arm's repeatability.

## How this reuses existing exercises

| Step | Reuses exercise | What it borrows |
|---|---|---|
| Every step | [20 — collision objects](../../../exercises/20-collision-objects/) | Bench / stations as static obstacles in the planning scene |
| 1, 2, 7, 8 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) | The pick / transit / place primitive |
| 1, 4, 6 | [22 — straight-line Cartesian path](../../../exercises/22-cartesian-path-following/) | Pushing the draft-shield door, the plunger, and seating the cap |
| 7 | [14 — barcode reader](../../../exercises/14-barcode-reader/) | Verifying the printed label on retract |
| 8 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) | Final slot drop |

Nothing fundamentally new is added beyond the two closed-loop force
controllers (plunger push and cap torque), which are small extensions
of exercise 22's contact-style motion.

## What this leaves for next time

Step 1 ends in a known-mass flask. Step 8 ends in a vial in a known
slot. Both ends are observable from the wrist camera and the orchestration
node. The same code with a different SDF and different mock services
handles the **ketchup case** — see
[`../ketchup/03-simulation-workflow.md`](../ketchup/03-simulation-workflow.md).
