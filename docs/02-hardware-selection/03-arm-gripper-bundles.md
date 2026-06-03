# Arm + Gripper Bundles

You picked an arm in [`01-arm.md`](01-arm.md) and read the gripper menu in
[`02-gripper.md`](02-gripper.md). But many arm vendors **also sell or
market a specific gripper** alongside the arm. Buying the bundle is usually
cheaper, faster to wire up, and the driver is supported on day one.

This file lists those bundles. For each arm, three columns matter:

- **Gripper.** What model is sold with this arm.
- **Made by.** Either the **arm vendor itself** (first-party) or a
  **partner brand** the vendor resells / co-markets (third-party).
- **What you actually get.** Mechanical mount, wiring, driver in the
  vendor SDK — yes or no.

## Hobby / education tier

| Arm | Gripper | Made by | What you get |
|-----|---------|---------|--------------|
| **Elephant Robotics myCobot 280 Pi / 320** | Adaptive parallel gripper, suction pump, LEGO-style gripper | First-party (Elephant Robotics) | Bolts to the LEGO-style end. Driven from the same Python / ROS 2 SDK as the arm. |
| **Niryo Ned2** | Standard / Large / Adaptive gripper, vacuum pump | First-party (Niryo) | Tool-changer wrist; all Niryo tools plug-and-play in NiryoStudio. |
| **Annin Robotics AR4 / AR5** | Sake EZGripper, or 3D-printed parallel jaw | Third-party (Sake) or DIY | Mount kit available; wiring/driver is community-maintained. |
| **Dobot Magician / MG400** | Suction cup, parallel jaw, pen holder, soft gripper | First-party (Dobot) | Magnetic quick-change; all included in DobotStudio. |
| **SO-ARM100 / Koch / Moss (LeRobot kits)** | Open-hardware parallel gripper, printed | First-party (TheRobotStudio / community) | 3D-printable; driver is part of `lerobot`. |
| **reBot Arm B601-DM Bundle** | Bundled parallel gripper + camera | First-party (reBot) | Sold *as the bundle* — the gripper is the point of the SKU. |
| **AgileX PiPER** | PiPER parallel gripper | First-party (AgileX) | ROS 2 driver ships with the arm. |
| **Trossen WidowX / ViperX** | Trossen X-Series gripper | First-party (Trossen) | Same Dynamixel chain as the arm; one driver for both. |

## Mid-range cobot tier

| Arm | Gripper | Made by | What you get |
|-----|---------|---------|--------------|
| **Universal Robots UR3e – UR20** | Robotiq 2F-85 / 2F-140, Hand-E, EPick, AirPick | Third-party (Robotiq), sold via **UR+** | UR+ certified: ISO 9409 flange, tool-IO wiring, URCap installs the driver in PolyScope. |
| **Universal Robots UR3e – UR20** | OnRobot RG2 / RG6 / VG10 / 3FG15 | Third-party (OnRobot), sold via **UR+** | Same story — wired through tool I/O, URCap driver. |
| **Franka Robotics FR3** | Franka Hand (parallel jaw) | First-party (Franka) | The default end-effector — ships in most FR3 SKUs. Same `libfranka` controls arm and gripper. |
| **Kinova Gen3 / Gen3 lite** | Robotiq 2F-85 (Gen3) or Kinova-integrated 2-finger (Gen3 lite) | Third-party (Robotiq) on Gen3; **first-party** on Gen3 lite | One Kortex SDK call moves arm + gripper. |
| **Doosan H / M / A series** | Doosan-branded gripper or OnRobot bundle | First-party (Doosan) **or** co-marketed OnRobot | Both options are listed in Doosan's online configurator. |
| **Techman TM5 / TM12 / …** | TM-branded servo gripper, plus an OnRobot partnership | First-party (Techman) **and** third-party (OnRobot) | TMflow vision + gripper macros pre-installed. |
| **Aubo / JAKA / Elite** | Robotiq, OnRobot, or in-house Chinese brand grippers (DH-Robotics, Inspire, …) | Mixed | Each vendor maintains a "compatible grippers" PDF — read it before ordering. |
| **Mecademic Meca500** | SCHUNK EGP-25, or Robotiq Hand-E | Third-party (SCHUNK / Robotiq) | Sold separately; Mecademic publishes wiring + driver examples. |
| **Standard Bots RO1** | RO1 parallel gripper | First-party (Standard Bots) | Single SKU; the "AI operator" UI already knows about it. |

## Industrial tier

| Arm | Gripper | Made by | What you get |
|-----|---------|---------|--------------|
| **ABB YuMi (IRB 14000)** | YuMi servo gripper (parallel, with built-in camera and suction options) | First-party (ABB) | Designed-for-the-arm. RobotStudio drivers built in. |
| **ABB GoFa (CRB 15000)** | ABB-branded gripper, plus OnRobot / Robotiq partnerships | First-party **and** third-party | ABB "Power-On Solutions" bundles include the gripper. |
| **FANUC CRX cobots** | Robotiq, OnRobot, SCHUNK, Soft Robotics — all in the **FANUC EZ-Connect** catalogue | Third-party (FANUC resells the wiring kit + plugin) | Plug-and-play "EZ-Connect" kits per gripper. |
| **FANUC LR Mate / R-2000iC (industrial)** | SCHUNK, SMC, Festo, vacuum specialists | Third-party | Custom integration — no plug-and-play assumption. |
| **KUKA KR series / LBR iiwa** | SCHUNK EGP / WSG, KUKA-branded media flange, Weiss WSG | Third-party — KUKA's typical partner is **SCHUNK** | KUKA Sunrise has SCHUNK driver examples; iiwa Media Flange exposes the right pneumatic + electrical lines. |
| **Yaskawa Motoman GP / HC** | Robotiq, OnRobot, SCHUNK via the **Yaskawa MotoFit** ecosystem | Third-party | MotoFit-listed kits include INFORM driver and wiring. |
| **Kawasaki RS / duAro** | duAro ships with a Kawasaki-branded servo gripper; RS arms use third-party (Robotiq, OnRobot, SCHUNK) | Mixed | duAro is the closest Kawasaki has to a "bundle." |

## AI-included platforms

These platforms care more about the *gripper choice* than usual, because
the bundled grasp policy was trained on a specific hand.

- **Mech-Mind / Photoneo bin-picking stacks** — paired with **SCHUNK** or
  **Robotiq** grippers in their reference configurations. The policy
  expects the listed gripper.
- **Covariant / Dexterity warehouse stacks** — usually sold with a
  **vacuum** gripper (Schmalz or Piab), occasionally a parallel jaw.
- **RightHand Robotics** — *their own* gripper (combined vacuum + finger).
  Not separable from the platform.
- **Figure / Apptronik / 1X humanoids** — first-party multi-finger hands,
  not separable.

## How to read a vendor "bundle" page without being misled

When the arm vendor's website shows a gripper next to the arm, check:

1. **Who actually makes it?** "Sold by UR" can mean "made by Robotiq."
   That's fine — but you call Robotiq for hardware support and UR for
   wiring/driver issues.
2. **Is the driver in the arm's SDK** *out of the box*, or do you install
   it separately? Look for a "certified" or "approved" badge (UR+,
   FANUC EZ-Connect, Yaskawa MotoFit, Doosan Bundle).
3. **Does the gripper count against the arm's payload?** Always. Many
   bundles list payload as "X kg at the wrist" — subtract the gripper
   weight before sizing.
4. **One cable or two?** Tool I/O (UR e-series, Franka FR3) means one
   cable down the arm. Anything else needs a separate cable run — plan
   for [cable management](08-cable-management.md).

## When *not* to take the bundle

- You already standardised on a gripper brand fleet-wide (SCHUNK, Robotiq).
  Stick with it across arms instead of buying the vendor's house gripper.
- The bundled gripper is a generic parallel jaw but your task needs vacuum,
  soft, or multi-finger. Buy the right family, even if the vendor doesn't
  sell it.
- You plan to train your **own** imitation-learning or VLA policy. The
  gripper must match the *training data* embodiment — usually one of the
  LeRobot kit grippers, not the vendor default.

## Output of this file

Add one extra line to your arm shortlist from [`01-arm.md`](01-arm.md):

```
Bundled gripper option:    yes / no
  Gripper model:           ___
  Made by:                 arm vendor (first-party) / partner: ___
  Driver in arm SDK?:      yes / no
  Counted against payload: ___ kg
```

If "Driver in arm SDK = no", expect 1–2 extra days of integration work
versus a certified bundle.
