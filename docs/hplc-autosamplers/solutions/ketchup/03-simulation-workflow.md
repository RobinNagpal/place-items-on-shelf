# 03 — Simulation workflow for the ketchup case

This file has **two halves**:

1. **What we are trying to do** — the physical workflow, exactly as
   a human technician performs it on a real bench. No code. No
   software. Just "pick up the beaker, walk to the balance, place
   it." Read this first so you know what the arm is replacing.
2. **How we implement it with the arm in simulation** — the ROS 2 +
   Gazebo + MoveIt 2 plan that drives the arm through the same
   motions.

The structure mirrors
[`../paracetamol/03-simulation-workflow.md`](../paracetamol/03-simulation-workflow.md).
Differences are confined to **Step 1** (peristaltic pump vs Quantos)
and a **new Step 3a — centrifuge** before dilution.

---

# Part 1 — What we are trying to do (the physical workflow)

A human technician runs the eight-step ketchup 5-HMF assay. The
simulation reproduces this sequence, only with the technician's hand
replaced by the arm.

## The bench, as the technician sees it

A 1.2 m × 0.6 m bench, left to right:

```
 [ inbound ] [ balance + pump ] [ stirrer ] [ centrifuge ] [ pipette ]
   rack       (Watson-Marlow                                holster
               nozzle fixed
               above pan)
                                                                       
 [ vol-flask ] [ filter ] [ vial rack ] [ cap   ] [ label printer ]
   rack         clamp                    dispenser   + wrapper
                                                                       
 [ autosampler tray (100 slot) ]
```

The technician stands in front of it and works left to right, one
ketchup sample at a time.

## The eight (+1) physical actions, in plain English

| # | What the technician does at this step | Result at the end |
|---|---|---|
| **1 — Weigh** | Take an empty 50 mL Pyrex beaker from the inbound rack. Slide the balance's glass door open. Place the beaker on the pan so its centre is under the Watson-Marlow pump nozzle. Close the door. Press TARE — the reading goes to 0.0000. Press START on the pump's controller (programmed for "deliver 5.0 g into the next vessel"). The pump runs slowly; the balance reads the rising mass. The pump's software slows the pump as it nears target, then stops at 5.0 g. Open the door, remove the beaker. | Beaker holds 5.0 g of ketchup. |
| **2 — Extract** | Pipette ~25 mL of water (or mild acid) into the beaker. Drop the beaker on the heated magnetic stirrer, stirring at 600 rpm for 10 min at 50 °C. Pull the beaker off. | A cloudy, pulpy mixture: 5-HMF is in the liquid, but tomato pulp is too. |
| **3a — Centrifuge** | Transfer the cloudy mix into a 1.5 mL centrifuge tube (~1 mL). Load the tube into the centrifuge rotor. Close the lid, spin at 14,000 g for 5 min. Open the lid, take the tube out. Pipette ~0.5 mL of the clearer supernatant into a 10 mL volumetric flask, **avoiding the pellet at the bottom**. | A clearer extract in a 10 mL flask, with the pulp pellet left behind in the centrifuge tube. |
| **3 — Dilute** | Top the 10 mL flask up to the mark with water. Swirl. If the strength is unknown, repeat once more (take 1 mL of *that* into another 10 mL flask) for a 1:100 total dilution. | A 10 mL flask of ~µg/mL-range 5-HMF in water — within the detector's comfortable range. |
| **4 — Filter** | Suck the diluted solution into a 10 mL syringe. Screw a **0.22 µm PVDF** filter onto the tip (tighter than paracetamol's 0.45 µm because food solutions carry finer particles). Set the tip over the destination vial. Push slowly, first ~0.5 mL to waste, then catch the clean stream. | A clean, filtered ~5 mL of ketchup extract. |
| **5 — Transfer to vial** | Hold the syringe (or pipette) over an empty 2 mL HPLC vial. Squirt in ~1.5 mL. | A 2 mL vial with ~1.5 mL of clean liquid. |
| **6 — Cap** | Take a screw cap from the dispenser. Set it on the vial. Twist clockwise until it feels firm — about 1 N·m. | A sealed vial. |
| **7 — Label** | The Zebra printer has already printed a sticker for this vial's Sample ID. Present the vial to the wrapper. The wrapper wraps the sticker around. | A labeled vial. |
| **8 — Place** | Carry the vial to the autosampler tray. Look at the worklist — say "slot 5." Set the vial gently into slot 5. | One row of the worklist completed. |

That is the workflow. Whatever the simulation does later has to map
back to this table.

## The differences from the paracetamol workflow

Only three rows differ from
[`../paracetamol/03-simulation-workflow.md`](../paracetamol/03-simulation-workflow.md):

- **Step 1** — pump instead of Quantos. Same physical motion
  (place / wait / pick up), different dispenser under the hood.
- **Step 2** — heated stirrer instead of ultrasonic bath, and the
  result is **cloudy** instead of clear.
- **Step 3a (new)** — centrifuge. No paracetamol equivalent.

Everything else (dilution, filter, vial, cap, label, place) is
identical to paracetamol. The arm and gripper do the same things.

## The two physical actions that need force feedback

Same as paracetamol:

- **Step 4 — push the plunger.** Same wrist-FT push, with a tighter
  back-pressure threshold (the 0.22 µm filter clogs faster than the
  0.45 µm one used for paracetamol).
- **Step 6 — torque the cap.** Same wrist-FT torque-limit motion.

Step 1 does **not** need arm-side force feedback in this design —
the bead-break happens between the fixed pump nozzle and the beaker,
not between the arm and anything. Mass feedback closes the loop on
the pump, not the arm.

---

# Part 2 — How we implement it with the arm in simulation

We now build the same sequence in software. The stack is the same as
the paracetamol case: **Linux + ROS 2 Jazzy + Gazebo Harmonic +
MoveIt 2**.

## What we simulate and what we fake

| Real world | Sim treatment |
|---|---|
| **UR5e arm + Hand-E gripper** | Full URDF, MoveIt, ros2_control — same as paracetamol |
| **Bench, racks, stations** | Static collision meshes in the SDF |
| **Liquid (ketchup, water, extract)** | Not simulated. The orchestration node tracks "what is in which vessel" as state. |
| **Pump (Watson-Marlow)** | ROS 2 service `/pump/dispense(target_g) → actual_g`. Internally simulates the slowdown ramp and the after-drip, returns `actual_g` after the simulated "rest" period. |
| **Balance reading** | ROS 2 topic `/balance/mass_grams` at 10 Hz. Driven by the pump service. |
| **Heated stirrer** | ROS 2 service `/stirrer/stir(seconds, rpm, deg_c)`. Blocks for `seconds` of sim time. |
| **Centrifuge** | ROS 2 service `/centrifuge/spin(seconds, g_force)`. Blocks for `seconds` of sim time, returns "supernatant ready." |
| **Pipette dispensing** | `/pipette/aspirate` and `/pipette/dispense` services. |
| **Syringe back-pressure** | `/syringe/back_pressure_N` topic; pushed-volume tracker like in paracetamol. |
| **Cap-thread torque** | `/cap/reaction_torque_Nm` topic like in paracetamol. |
| **Label wrapper / autosampler tray** | Same services and named poses as paracetamol. |

The list overlaps with the paracetamol list by 90 % — most of the
mock services are reusable. Only the **pump**, the **stirrer**, and
the **centrifuge** are ketchup-specific.

## ROS 2 packages we add to the workspace

| Package | Source | Role |
|---|---|---|
| [`ur_description`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Description) | first-party | UR5e URDF |
| [`ur_simulation_gz`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation) | first-party | Gazebo + ros2_control wiring |
| [`ur_moveit_config`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver) | first-party | MoveIt 2 SRDF + planning config |
| [`robotiq_hande_description`](https://github.com/PickNikRobotics/robotiq) | community | Hand-E URDF + controllers |
| **`ketchup_cell_world`** | this repo (new) | SDF for the bench + every station + the mock service nodes |
| **`ketchup_cell_demo`** | this repo (new) | Orchestration node — the 8 (+1) step state machine |

Of the two new packages, **most code is reusable** from the
paracetamol packages. The differences are confined to the pump mock
(`ketchup_cell_world`) and three states of the demo node
(`ketchup_cell_demo`).

## The orchestration node

`ketchup_cell_demo` exposes one node: `run_assay`. Same shape as
paracetamol: a plain-Python state machine with one state per workflow
row, including the new Step 3a centrifuge state.

## Step-by-step implementation, one row per workflow step

| Workflow step | ROS 2 calls performed by `run_assay` |
|---|---|
| **1 — Weigh** | `move_arm("above_inbound_slot")` → `gripper_close(50 mm, 30 N)` → `move_arm("above_balance")` → `compute_cartesian_path("push_door_open")` → `move_arm("above_pan")` → `move_arm("place_on_pan")` → `gripper_open()` → `move_arm("retract")` → `compute_cartesian_path("push_door_closed")` → call `/pump/dispense(5.0)` and **wait** (10–20 s of sim time) → `compute_cartesian_path("push_door_open")` → `move_arm("above_pan")` → `gripper_close(50 mm, 30 N)` → `move_arm("retract_with_beaker")` → `compute_cartesian_path("push_door_closed")` |
| **2 — Extract** | Pipette pattern: `pipette_pickup` → `aspirate(25000)` → `move_arm("above_beaker_with_ketchup")` → `dispense(25000)` (over 25 cycles of 1 mL) → `pipette_release` → `move_arm("grasp_beaker")` → `move_arm("above_stirrer")` → `place_on_stirrer` → call `/stirrer/stir(600, 600, 50)` (600 s, 600 rpm, 50 °C) → `pick_up_beaker` |
| **3a — Centrifuge** | `pipette_pickup` → `aspirate(1000)` from the extract beaker → `move_arm("above_centrifuge_tube_rack")` → `dispense(1000)` into a 1.5 mL tube → `pipette_release` → `move_arm("grasp_tube")` → `move_arm("above_centrifuge")` → `load_tube_in_rotor` → `gripper_open()` → `move_arm("above_centrifuge_lid")` → `compute_cartesian_path("close_lid")` → call `/centrifuge/spin(300, 14000)` (5 min @ 14k g) → `compute_cartesian_path("open_lid")` → `grasp_tube` → `move_arm("above_volflask_rack")` → `pipette_pickup` → `aspirate(500)` **from above the pellet, not into it** (a known fixed pipetting depth) → `dispense(500)` into the 10 mL volumetric flask |
| **3 — Dilute** | Same pipette pattern as paracetamol. Top the flask to 10 mL with water, swirl. Optionally repeat once for 1:100. |
| **4 — Filter** | Same pattern as paracetamol but with a **0.22 µm** filter and a **lower** back-pressure threshold (3 N instead of 4 N) — the 0.22 µm filter clogs sooner. |
| **5 — Transfer to vial** | Identical to paracetamol. |
| **6 — Cap** | Identical to paracetamol. |
| **7 — Label** | Identical to paracetamol. |
| **8 — Place** | Identical to paracetamol. |

The diff vs. paracetamol is short: **steps 1, 2, 3a, and 4**.
Everything else is shared code. That is the payoff for picking the
same arm and gripper for both cases.

## The pump-control sub-controller for Step 1

```python
def dispense_via_pump(target_g, max_time_s=30):
    start_mass = read("/balance/mass_grams")
    pump.start(rate_g_per_s=0.5)
    while True:
        current = read("/balance/mass_grams")
        delivered = current - start_mass
        if delivered > (target_g - 0.5):
            pump.set_rate(0.05)             # slow-down ramp
        if delivered >= target_g - 0.05:
            pump.stop()
            break
        if elapsed > max_time_s:
            pump.stop()
            raise RuntimeError("Pump timeout")
    wait(1.0)                                # wait for after-drip
    actual_g = read("/balance/mass_grams") - start_mass
    return actual_g
```

In v1 the after-drip is **modelled inside the pump service** — it
adds a brief mass increment after `pump.stop()`. The orchestration
node trusts the final balance reading, not the pump's request. That
is how real Watson-Marlow + Mettler installations work: the balance
is the truth, the pump is only a throttle.

## The closed-loop force controller for Step 4 (slightly tightened)

Same shape as paracetamol's, but `target_force` is **3 N** instead of
4 N — the 0.22 µm membrane has half the open area of the 0.45 µm one
and clogs sooner.

```python
def push_plunger_until_volume(target_uL):
    target_force = 3.0
    ...
```

## The wrist-torque controller for Step 6

Identical to paracetamol.

## How to run it (three terminals)

```bash
# Terminal A — Gazebo + UR5e + ros2_control + RViz
ros2 launch ketchup_cell_world ketchup_cell.gazebo.launch.py

# Terminal B — MoveIt 2 (UR5e planner action server)
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur5e

# Terminal C — the demo
ros2 launch ketchup_cell_demo run_assay.launch.py \
    sample_id:=KETCHUP_BOT_42_S01 \
    target_g:=5.0 \
    tray_slot:=5
```

Expected console output on a successful run — read this together
with the Part-1 table.

```
[ 1  ] [weigh    ] beaker grasped, draft-shield open, on pan
[ 1  ] [weigh    ] pump delivered 5.0010 g in 11.2 s (after-drip 0.0010 g)
[ 1  ] [weigh    ] draft-shield closed, beaker retrieved
[ 2  ] [extract  ] pipette delivered 25000 µL of water in 25 cycles
[ 2  ] [extract  ] stirrer ran 600 s @ 600 rpm @ 50 °C; beaker retrieved
[ 3a ] [spin     ] 1.0 mL transferred to centrifuge tube
[ 3a ] [spin     ] centrifuge ran 300 s @ 14000 g
[ 3a ] [spin     ] 500 µL supernatant transferred to 10 mL flask
[ 3  ] [dilute   ] flask topped to 10 mL with water
[ 4  ] [filter   ] plunger push: 5000 µL pushed at 2.7 N back-pressure
[ 5  ] [transfer ] 1500 µL into vial 12-mm OD
[ 6  ] [cap      ] wrist torque reached 1.0 N·m at 118°
[ 7  ] [label    ] barcode KETCHUP_BOT_42_S01 wrapped
[ 8  ] [place    ] vial seated in tray slot 5
{"sample_id":"KETCHUP_BOT_42_S01","target_g":5.0,"actual_g":5.0010,
 "tray_slot":5,"timestamp":"2026-06-08T16:55:33Z","status":"ok"}
```

## "Done when" criteria

- The 8 (+1) step state machine completes without `plan` or
  `execute` failures, ten times in a row.
- The pump service returns `actual_g` within ±10 mg of the target on
  9 of 10 runs (looser than paracetamol because the after-drip model
  is a v1 guess).
- The centrifuge service blocks for the full simulated duration and
  the supernatant-pipetting depth never reaches into the pellet
  region (a fixed safety offset).
- The Step-4 force loop completes the target volume without
  back-pressure exceeding the threshold.
- The Step-6 torque loop reaches 1.0 N·m at a wrist angle between
  90° and 270°.
- The vial ends up in the correct tray slot.
- The JSONL log line is written.

## How this reuses existing exercises

| Step | Reuses exercise |
|---|---|
| Every step | [20 — collision objects](../../../exercises/20-collision-objects/) |
| 1, 2, 3a, 7, 8 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) |
| 1, 4, 6, 3a (lid open/close) | [22 — straight-line Cartesian path](../../../exercises/22-cartesian-path-following/) |
| 7 | [14 — barcode reader](../../../exercises/14-barcode-reader/) |
| 8 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) |

Same exercises as the paracetamol cell. The centrifuge lid-open /
lid-close is just two more `computeCartesianPath` calls — no new
primitive.

## What this leaves for next time

Step 1 ends in a known-mass beaker. Step 8 ends in a vial in a known
slot. The orchestration node JSONL log line is enough for a v1
audit trail. Future work, in rough order:

1. **Replace the pump after-drip model** with a real measurement
   from the bench-bringup phase.
2. **Replace the "fixed pipetting depth above pellet"** safety
   offset with a depth-camera-based pellet detector — useful when
   sample volumes vary.
3. **Replace the heated stirrer mock** with a real PID-controlled
   heater + magnetic stirrer driver.
4. **Bring up on real UR5e + real Hand-E** once the sim is reliable
   for 100 consecutive runs.
