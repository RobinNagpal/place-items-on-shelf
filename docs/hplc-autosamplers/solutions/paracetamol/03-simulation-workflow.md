# 03 — Simulation workflow for the paracetamol case

We now know **what** the arm does (carry labware to a Quantos-equipped
balance, [`README.md`](README.md)), **why** off-the-shelf systems work
that way ([`01-existing-solutions.md`](01-existing-solutions.md)), and
**which** arm we picked ([`02-hardware-choice.md`](02-hardware-choice.md)).
This file ties it all together as a **simulation plan** the project can
actually build.

Everything below runs on **Linux + ROS 2 Jazzy + Gazebo Harmonic +
MoveIt 2** in a single laptop. No real hardware. No wet lab.

## What "simulating a balance" actually means

The balance and the Quantos do not move and do not need real physics —
they are **passive** in our simulation. We fake them with three small
ROS 2 services / topics:

| Real-world component | Sim stand-in | What it does in sim |
|---|---|---|
| **Balance pan** | A small static box in the Gazebo world, tagged with an ArUco fiducial | Provides a fixed pose the arm can target |
| **Draft-shield door** | A sliding link in the URDF, opened by a tiny prismatic joint | The arm pushes a known XYZ point to open it |
| **Quantos dispenser** | A ROS 2 service `dispense_powder(target_mg) -> actual_mg` | Returns the target mass plus simulated noise. No mesh, no physics — the powder never appears as a particle. |

Crucially, the **mass dispensed is not simulated by physics** — it is
just a ROS 2 service that returns a number. That is enough for the
arm's job (open door → place flask → call service → wait → close door
→ remove flask), which is the only thing the simulation needs to
verify.

## The Gazebo world

```
autosampler_cell_weighing.sdf
├── bench (flat plane, 60 × 90 cm)
├── ur3e_robot (URDF + collision meshes)
│   └── robotiq_2f85_gripper
│       └── camera_realsense_d405 (mounted on the wrist)
├── balance_xpr226 (static mesh — base + glass draft shield + 80 mm pan)
│   ├── door_left  (prismatic joint, 0–150 mm travel)
│   ├── door_right (prismatic joint, 0–150 mm travel)
│   └── aruco_tag_balance (ArUco marker on the base)
├── quantos_qb1 (static mesh, attached to the balance top, no joints)
├── flask_100ml_volumetric  (URDF, 80 mm wide × 220 mm tall)
└── inbound_rack (8-slot rack with 5 ready flasks + 3 empty slots)
```

Optional: a coarse model of the lab room — wall, floor, ceiling
light — for shadow realism. Skippable for v1.

## The ROS 2 packages we add to the workspace

| Package | Source | Role |
|---|---|---|
| [`Universal_Robots_ROS2_Description`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/main/ur_description) | first-party | UR3e URDF |
| [`Universal_Robots_ROS2_GZ_Simulation`](https://github.com/UniversalRobots/Universal_Robots_ROS2_GZ_Simulation) | first-party | Gazebo + ros2_control wiring |
| [`Universal_Robots_ROS2_MoveIt_Config`](https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver/tree/main/ur_moveit_config) | first-party | MoveIt 2 SRDF + planning config |
| [`robotiq_2f_gripper_ros2`](https://github.com/PickNikRobotics/robotiq) | community | gripper URDF + open/close controllers |
| **`weighing_cell_world`** | this repo (new) | the Gazebo SDF above + balance / Quantos mock |
| **`weighing_cell_demo`** | this repo (new) | the orchestration node that drives the steps |

Two of the six are new code we write. Everything else is upstream.

## The orchestration node

The new package `weighing_cell_demo` contains one node,
`weigh_one_sample`, with the following responsibilities:

1. Plan and execute a sequence of MoveIt 2 goals.
2. Open / close the gripper at the right moments.
3. Drive the draft-shield door open and closed.
4. Call the simulated `dispense_powder` service.
5. Read the wrist camera and decode the flask's QR / barcode for the
   per-vial log.
6. Emit a JSONL log line of `(barcode, target_mg, actual_mg, slot)`.

That is it. Nothing else.

## The motion sequence — 14 steps

All Cartesian targets are in the arm's `base_link` frame, gripper
pointing straight down (roll = π). Numbers below are illustrative; the
real ones come from the launched SDF.

```
 1. arm  → "home"                                  (named target)
 2. grip → "open"                                  (named target)
 3. arm  → "above_rack_slot_1"   (0.40, +0.10, 0.30)
 4. arm  → "grasp_flask"         (0.40, +0.10, 0.20)
 5. grip → "closed_soft"         (force-limited)
 6. arm  → "lift_flask"          (0.40, +0.10, 0.30)
 7. arm  → "above_balance_door"  (0.30, -0.05, 0.30)
 8. arm  → "open_door_left"      (push the prismatic joint)
 9. arm  → "above_pan"           (0.30, -0.05, 0.25)
10. arm  → "place_on_pan"        (0.30, -0.05, 0.18)
11. grip → "open"                ───► flask released, arm retracts 5 cm
12. *** service call: /quantos/dispense_powder(target_mg=5.0) ***
       blocks until response (actual_mg returned, ~5.0 ± 0.0001 g)
13. arm  → "close_door_left"     (push the prismatic joint back)
14. arm  → "home"
```

Step 12 is what makes this a *weighing* workflow rather than a generic
pick-and-place — and it is the **one step the arm does not perform**.
The Quantos does it. The arm just waits.

A second pass (steps 7–14 again) pulls the *now-filled* flask off the
pan and onto an outbound rack slot for downstream steps to consume.

## How it connects to existing checklist exercises

A lot of this is already implemented under
[`../../../exercises/`](../../../exercises/). Re-use, do not
rebuild:

| Step | Re-uses exercise | Why |
|---|---|---|
| 1, 14 | [18 — joint-space hello MoveIt](../../../exercises/18-joint-space-hello-moveit/) | Named-target motion |
| 3, 4, 6, 7, 9, 10, 13 | [19 — Cartesian pose goal](../../../exercises/19-cartesian-pose-goal/) | `setPoseTarget` + KDL IK |
| 8, 13 | [22 — straight-line Cartesian path](../../../exercises/22-cartesian-path-following/) | `computeCartesianPath` for the linear door push |
| 5, 11 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) | `setNamedTarget` on the gripper move group |
| QR decode in `dispense_powder` log | [14 — barcode reader](../../../exercises/14-barcode-reader/) | `pyzbar` on the wrist camera frame |
| Bench + balance + draft shield as obstacles | [20 — collision objects](../../../exercises/20-collision-objects/) | `PlanningSceneInterface::applyCollisionObjects` |

Only two genuinely new things stand alongside the exercises:

1. The **draft-shield door** as a prismatic-joint obstacle that the arm
   has to *push* rather than route around. This is item 22 with a
   specific twist: end-effector contact, not free motion.
2. The **balance / Quantos mock services**.

## How to run it (three terminals — same shape as exercise 21)

```bash
# Terminal A — Gazebo + UR3e + ros2_control + RViz
ros2 launch weighing_cell_world weighing_cell.gazebo.launch.py

# Terminal B — MoveIt 2 (UR3e planner action server)
ros2 launch ur_moveit_config ur_moveit.launch.py ur_type:=ur3e

# Terminal C — the demo
ros2 launch weighing_cell_demo weigh_one_sample.launch.py \
    target_mg:=5.0 \
    rack_slot:=1
```

Expected output in terminal C, for one successful run:

```
[home   ] arm     -> 'home'
[open   ] gripper -> 'open'
[pose   ] arm     -> above_rack_slot_1   (0.40, 0.10, 0.30)
[pose   ] arm     -> grasp_flask         (0.40, 0.10, 0.20)
[grip   ] gripper -> 'closed_soft' (force=15 N)
[pose   ] arm     -> lift_flask          (0.40, 0.10, 0.30)
[pose   ] arm     -> above_balance_door  (0.30,-0.05, 0.30)
[push   ] door_left opened (147.8 mm)
[pose   ] arm     -> place_on_pan        (0.30,-0.05, 0.18)
[grip   ] gripper -> 'open'
[svc    ] /quantos/dispense_powder       target=5.0 mg
[svc    ] /quantos/dispense_powder       actual=5.0001 mg in 12.4 s
[push   ] door_left closed
[home   ] arm     -> 'home'
{"barcode":"PARA_BATCH_47_S01","target_mg":5.0,"actual_mg":5.0001,
 "slot":1,"timestamp":"2026-06-08T16:42:11Z","status":"ok"}
```

## What "done when" means here

We borrow the format from
[`../../../learning-checklist.md`](../../../learning-checklist.md):

- The 14-step sequence runs end-to-end without `plan` or `execute`
  failures, ten times in a row.
- The flask is on the pan in step 11 (verified by the wrist camera
  seeing the balance ArUco within a 5 cm × 5 cm window).
- The Quantos service call returns a non-error response.
- The JSONL log line is written.

End-effector accuracy is **not** part of the success criterion — the
Quantos handles that. This is the inverse of every other exercise we
have shipped (which all measure end-effector accuracy directly).

## What this leaves for the next workflow steps

Step 1 (weighing) ends with a 100 mL volumetric flask containing a
known mass of paracetamol powder, sitting in an outbound rack slot,
logged. Step 2 (dissolution) picks it up from there. The arm motion
for Step 2 is structurally the same as Step 1 — pick the flask, drive
to a sonicator instead of a balance, drop it in, wait for a fixed
time, retrieve it. So most of `weighing_cell_demo` is re-usable as a
shared utility once Step 2 lands.

That is the long-term shape of this folder: each step has its own
small simulation, but they all reuse the same UR3e + Robotiq +
RealSense + MoveIt 2 stack. The **only** thing that changes per step
is the static labware in the Gazebo world and which mock service the
demo node calls.
