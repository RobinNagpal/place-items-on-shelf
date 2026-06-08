# 03 — Simulation workflow for the ketchup case

We now know what the arm does ([`README.md`](README.md)), how labs
solve the dispensing problem today
([`01-existing-solutions.md`](01-existing-solutions.md)), and which
hardware we picked ([`02-hardware-choice.md`](02-hardware-choice.md)).
This file is the **simulation plan**.

Everything below runs on **Linux + ROS 2 Jazzy + Gazebo Harmonic +
MoveIt 2** in a single laptop. No real hardware. No real ketchup.

## What "simulating ketchup dispensing" actually means

We do **not** simulate ketchup as fluid in Gazebo. Fluid simulation is
hard, slow, and unnecessary — we care about the *control loop*, not
the rheology. We fake the relevant signals instead:

| Real-world component | Sim stand-in | What it does in sim |
|---|---|---|
| **Balance reading** | ROS 2 topic `/balance/mass_grams` at 10 Hz | A small node monotonically increases the reported mass while the pump is "on" |
| **Pump motor** | ROS 2 service `/pump/set_state(on/off, rate_g_per_s)` | Tells the balance node to start / stop incrementing |
| **Sticky bead** | Joint-torque pulse on the FR3 wrist joint when the arm retracts | Models the drag of the string before it breaks |
| **After-drip** | A short post-stop increment of `/balance/mass_grams` after pump-off | Models the few hundred milligrams that fall after the pump stops |

That last row is the **whole reason** the FR3 was picked over the
UR5e — the arm has to learn to retract *before* the after-drip is
measured, by watching for the bead-break torque pulse. If we did not
simulate that, we could use any arm.

## The Gazebo world

```
ketchup_weighing_cell.sdf
├── bench
├── fr3_robot (URDF + collision meshes)
│   └── nozzle_holder (3D-printed bracket, mounted on flange)
│       └── camera_realsense_d405 (wrist RGB-D)
├── balance_xpr1203s (static mesh, 120 mm pan)
├── beaker_50ml (URDF, 35 mm bottom × 70 mm top × 60 mm tall)
├── pump_watson_marlow_323 (static mesh on the bench; no joints)
│   └── tubing (Marprene, modelled as a fixed visual, no physics)
├── source_bottle_ketchup_500ml (static, capped, with a barcode label)
├── overhead_camera (small RGB looking down into the beaker)
└── inbound_rack / outbound_rack (slots for beakers before/after)
```

The ketchup itself is **invisible**. The simulation has nothing
flowing through the tubing. We just trust the balance node.

## The ROS 2 packages we add to the workspace

| Package | Source | Role |
|---|---|---|
| [`franka_description`](https://github.com/frankarobotics/franka_description) | first-party | FR3 URDF |
| [`franka_ros2`](https://github.com/frankarobotics/franka_ros2) | first-party | Drivers + Gazebo + ros2_control wiring |
| [`franka_moveit_config`](https://github.com/frankarobotics/franka_ros2/tree/main/franka_moveit_config) | first-party | MoveIt 2 SRDF + planning config |
| **`ketchup_weighing_world`** | this repo (new) | The Gazebo SDF + balance + pump mocks |
| **`ketchup_weighing_demo`** | this repo (new) | Orchestration node — the bead-break detector lives here |

Two of the five are new code we write. Everything else is upstream.

## The orchestration node

The new package `ketchup_weighing_demo` contains one node,
`weigh_one_ketchup`, with the following responsibilities:

1. Plan and execute MoveIt 2 goals for the FR3.
2. Position the nozzle ~5 mm above the centre of the beaker.
3. Turn the pump on. Subscribe to `/balance/mass_grams`.
4. When the mass passes (target_g − overshoot_estimate), turn the
   pump off.
5. Wait for the after-drip to finish (detected as `mass_grams` going
   flat for 1 s).
6. **Retract the nozzle straight up**, watching the FR3's joint
   torques for the string-break signature.
7. Read the wrist camera for the bottle barcode.
8. Emit a JSONL log line `(barcode, target_g, actual_g, slot)`.

## The bead-break detector — the one new bit

Most of the workflow is recognisable from the paracetamol case. The
bead-break detector is what makes this case interesting. Here is the
idea in plain English:

When the pump stops, a small string of ketchup is hanging from the
nozzle and connecting to the bead inside the beaker. If the arm
retracts immediately, the string pulls extra ketchup out of the beaker
and the measured mass is wrong. So the arm has to wait until the
string **lets go** of either the nozzle or the beaker — whichever
gives first.

In simulation we model the let-go as a **torque pulse on the FR3 wrist
joint** that ends abruptly. The detector subscribes to
`/joint_states.effort` and looks for:

1. A sustained negative wrist torque (the string pulling down) for at
   least 200 ms.
2. A sharp return to zero in less than 50 ms.

When both conditions fire within the same 1 s window, the string has
broken. We log the timestamp and continue the retract. If the
conditions never fire (no string ever formed — viscosity must be
unusually low today), we time out at 5 s and continue anyway.

In Python pseudocode:

```
def on_joint_state(msg):
    wrist_effort = msg.effort[idx_wrist]
    history.append((now, wrist_effort))
    if sustained_negative(history, ms=200) and \
       sharp_return_to_zero(history, ms=50):
        detector_state = "string_broken"
```

That logic is the whole "force-sensing" payoff. Without joint torque
on the wrist, the same detector would have to read a wrist-only FT
sensor; in a 6-DOF arm at the same retract pose, the signature gets
mixed with gripping-hold torque artefacts and the detector is
noticeably less reliable.

## The motion sequence — 13 steps

All Cartesian targets are in the FR3's `panda_link0` frame, nozzle
pointing straight down.

```
 1.  arm  → "home"                                  (named target)
 2.  arm  → "above_inbound_beaker"  (0.50, +0.20, 0.40)
 3.  arm  → "grasp_beaker"           (0.50, +0.20, 0.22)
 4.  grip → close_soft                                  (force-limited)
 5.  arm  → "above_balance_pan"     (0.30, 0.00, 0.40)
 6.  arm  → "place_on_pan"          (0.30, 0.00, 0.20)
 7.  grip → open                                       (beaker on the pan)
 8.  arm  → "nozzle_above_beaker"   (0.30, 0.00, 0.28)
       (nozzle is now ~5 mm above the beaker rim)
 9.  ***  service call: /pump/set_state(on, rate=0.5 g/s)  ***
 10. *** subscribe /balance/mass_grams until target reached ***
       at (target_g - 0.2 g) ──► /pump/set_state(off)
       wait for after-drip ──► mass goes flat for 1 s
 11. arm  → "retract_straight_up"   (0.30, 0.00, 0.50)
       watch joint torques during the retract — break detector
 12. arm  → "above_outbound_slot"   (0.50, -0.20, 0.40)
 13. arm  → "home"
```

The straight-up retract in step 11 is the **whole point of having a
7th joint**. With six joints the wrist would have to rotate to keep
the nozzle pointing down during a pure z-axis pull — that rotation
wags the nozzle slightly and is exactly what we want to avoid.

## How it connects to existing checklist exercises

| Step | Re-uses exercise | Why |
|---|---|---|
| 1, 13 | [18 — joint-space hello MoveIt](../../../exercises/18-joint-space-hello-moveit/) | Named-target motion |
| 2, 3, 5, 6, 8, 12 | [19 — Cartesian pose goal](../../../exercises/19-cartesian-pose-goal/) | `setPoseTarget` + KDL IK |
| 4, 7 | [21 — hardcoded pick-and-place](../../../exercises/21-hardcoded-pick-and-place/) | Named gripper targets |
| 11 | [22 — straight-line Cartesian path](../../../exercises/22-cartesian-path-following/) | `computeCartesianPath` for the straight-up retract |
| Beaker + balance + pump as obstacles | [20 — collision objects](../../../exercises/20-collision-objects/) | `PlanningSceneInterface::applyCollisionObjects` |
| Bottle barcode decode | [14 — barcode reader](../../../exercises/14-barcode-reader/) | `pyzbar` on the wrist camera frame |

Two genuinely new things:

1. The **bead-break detector** (joint-torque pattern matcher).
2. The **balance / pump mock services**.

The detector is closer to checklist item 15 (wrist F/T sensor for
surface contact) but uses joint torque rather than wrist FT — a small
but important difference, motivated entirely by what the FR3 makes
available. If we ever build a UR5e variant we would fall back to the
wrist-only FT version of the same detector.

## How to run it (three terminals)

```bash
# Terminal A — Gazebo + FR3 + ros2_control + RViz
ros2 launch ketchup_weighing_world ketchup_weighing.gazebo.launch.py

# Terminal B — MoveIt 2 (Franka FR3 planner action server)
ros2 launch franka_moveit_config moveit.launch.py

# Terminal C — the demo
ros2 launch ketchup_weighing_demo weigh_one_ketchup.launch.py \
    target_g:=5.0 \
    rack_slot:=1
```

Expected output, one successful run:

```
[home   ] arm     -> 'home'
[pose   ] arm     -> above_inbound_beaker (0.50, 0.20, 0.40)
[pose   ] arm     -> grasp_beaker         (0.50, 0.20, 0.22)
[grip   ] gripper -> 'closed_soft' (force=10 N)
[pose   ] arm     -> above_balance_pan    (0.30, 0.00, 0.40)
[pose   ] arm     -> place_on_pan         (0.30, 0.00, 0.20)
[grip   ] gripper -> 'open'
[pose   ] arm     -> nozzle_above_beaker  (0.30, 0.00, 0.28)
[svc    ] /pump/set_state  on, 0.5 g/s
[mass   ] /balance/mass_grams  rising: 0.0 → 4.8 g (pump cutoff)
[svc    ] /pump/set_state  off
[mass   ] /balance/mass_grams  after-drip: 4.8 → 5.0001 g (settled)
[retract] /joint_states.effort  string_broken at t+0.31 s
[pose   ] arm     -> retract_straight_up  (0.30, 0.00, 0.50)
[pose   ] arm     -> above_outbound_slot  (0.50,-0.20, 0.40)
[home   ] arm     -> 'home'
{"barcode":"KETCHUP_BOT_42_S01","target_g":5.0,"actual_g":5.0001,
 "slot":1,"timestamp":"2026-06-08T16:55:33Z","status":"ok",
 "string_break_t_s":0.31}
```

## What "done when" means here

- The 13-step sequence runs end-to-end without `plan` or `execute`
  failures, ten times in a row.
- The bead-break detector fires on at least 9 of 10 runs (we accept
  one timeout-and-continue as the after-drip will sometimes be small
  enough to not produce a detectable string).
- The actual mass is within ±10 mg of the target on 9 of 10 runs.
  (Tolerance is generous in v1 — the after-drip model is a guess; we
  tighten it when we have real-pump data.)
- The JSONL log line is written for every run.

## What this leaves for the next workflow steps

Step 1 ends with a 50 mL beaker holding a known mass of ketchup, on an
outbound rack slot, logged. Step 2 (dissolution / extraction) would
typically add cold acetonitrile to crash out solids — that is a liquid
dispense the same Watson-Marlow pump can handle. Most of
`ketchup_weighing_demo` ports straight over, just with a different
mock service for "add 50 mL of acetonitrile" instead of "ketchup at
0.5 g/s."

This is the same long-term shape as the paracetamol folder: a stable
arm + sensor + balance stack, with each workflow step swapping the
labware and the mock services.
