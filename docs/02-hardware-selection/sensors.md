# Sensors

Sensors are how the robot **sees, feels, and measures** its world. Without
them, the arm can move precisely to coordinates you give it, but it has no
idea what's around it.

This file covers everyday sensors that mount on or near an arm. **Safety
sensors** (laser scanners, light curtains) live in their own file:
[`safety-equipment.md`](safety-equipment.md).

## First: do you even need a sensor?

The honest answer is: **as few as possible.** Every sensor adds a wire to
break, a calibration to keep up to date, and a piece of software to debug.

Run these binary checks against your Layer-1 spec first:

| Question | If yes, you need... |
|----------|---------------------|
| Are object positions **known in advance** (fixed jig, taught pose)? | Probably no perception sensor at all. |
| Do object positions **change**? | A 2D or 3D camera. |
| Is depth important (stacked items, picking from a bin)? | A depth (RGBD) camera, not a flat RGB one. |
| Does the gripper need to **feel** the object (fragile, variable weight)? | A force/torque sensor or a tactile sensor. |
| Are humans nearby and the area isn't fenced off? | A safety sensor (in [safety-equipment.md](safety-equipment.md)). |
| Does the task involve weighing? | A load cell or scale, separate from the arm. |

If most answers are "no," you probably need fewer sensors than you think.

## The sensor families

The catalogue is large; the families that matter for arm work are:

1. **2D RGB cameras** — flat colour images. Cheap and well-supported.
2. **3D / RGBD cameras** — colour plus a distance for every pixel. The
   workhorse for most "see and grasp" demos.
3. **Force / torque (F/T) sensors** — measure push, pull, and twist at the
   wrist. Used for fragile insertion, contact detection, polishing.
4. **Tactile sensors** — pressure at the fingertip. Newer than F/T.
5. **Proximity sensors** — say "something is near" without saying what or
   how far. Cheap, fast.
6. **Joint encoders and IMUs** — built into the arm already in almost all
   cases. Don't budget for them separately.
7. **Environmental** — temperature, humidity, scales. Niche.

## Where the sensor mounts

The same camera does different jobs depending on where it sits.

- **Eye-in-hand** — on the wrist or gripper. Moves with the arm. Good for
  close-up alignment, in-bin picking. **Penalty:** weight on the wrist
  eats payload; the sensor is blind during the grasp itself.
- **Eye-to-hand** — on a tripod or overhead frame, looking at the work
  area. Stable view of the whole scene. **Penalty:** the arm itself can
  block the view mid-motion.
- **Gripper-integrated** — F/T or tactile baked into the gripper. No
  separate wiring. **Penalty:** locked into that gripper.
- **Workspace-mounted** — load cells, scales, safety mats. Don't move.
  Don't need calibration. Don't "see" the object directly.

You pick a sensor and a mounting strategy together. Both have to fit your
Layer-1 workspace and payload.

## Popular sensors by family

### 2D RGB cameras

For barcodes, simple classification, AprilTag detection.

- **Basler ace / dart / boost** — industrial USB / GigE colour cameras.
  Very common in inspection cells.
- **IDS uEye / NXT** — German industrial vision. The NXT family has an
  on-camera AI chip.
- **FLIR / Teledyne Blackfly S** — research-grade GigE / USB cameras.
- **Allied Vision Mako / Alvium** — similar tier to Blackfly.
- **Raspberry Pi HQ Camera, Logitech C920, Arducam** — hobby tier. Fine
  for a myCobot 280 demo. Not for production.

**Best for what:**

- Basler / FLIR / IDS — production inspection, where image quality
  matters.
- Pi Camera / Logitech — learning, demos, low-volume hobby projects.

### 3D / RGBD depth cameras

The most consequential sensor pick for manipulation. Different
technologies have different strengths.

- **Intel RealSense D435 / D435i / D405 / D455 / D456** — the de facto
  ROS depth camera since 2018. ~$300, great driver support. ⚠️ Intel has
  wound down new RealSense product development; existing cameras and
  the SDK are still supported, but new long-horizon projects should look
  at **Orbbec** as a future-proof alternative.
- **Orbbec Gemini 2 / Gemini 2 L / Femto Bolt / Femto Mega** — credible
  RealSense replacement. Femto Bolt / Mega use the same time-of-flight
  sensor as the discontinued Microsoft Azure Kinect DK.
- **StereoLabs ZED 2 / ZED 2i / ZED X / ZED Mini** — passive stereo (no
  IR projector). Works outdoors and at long range. Needs an NVIDIA GPU.
- **Photoneo PhoXi (S / M / L) and MotionCam-3D** — very high precision
  (<200 µm). The bin-picking industry standard. Heavy, expensive
  (~$10–20k). Usually eye-to-hand.
- **Zivid 2 / 2+ / Zivid One Plus** — sub-100 µm structured-light. Often
  paired with bin-picking AI stacks. Heavy (~1.5–2 kg) — check your
  payload before wrist-mounting.
- **Mech-Mind Pro / Nano** — sold bundled with Mech-Mind's bin-picking AI.
- **Roboception rc_visard / rc_reason** — passive stereo + on-camera
  grasp detection. Popular in EU manufacturing.

**Best for what:**

- RealSense / Orbbec — close-range manipulation, research, hobby. Cheap
  and well-documented.
- ZED — outdoor robotics or long-range stereo.
- Photoneo / Zivid — high-precision industrial bin picking.
- Mech-Mind — AI-included bin-picking projects.

### Force / torque sensors

For insertion, polishing, fragile contact, variable-weight tasks.

- **ATI Industrial Automation Mini40 / Mini45 / Axia80 / Axia90 / Gamma /
  Delta** — long-standing research and industrial standard.
- **Robotiq FT 300-S** — plug-and-play with UR e-series cobots.
- **OnRobot HEX-E v3 / HEX-H v3** — cobot-friendly F/T sensor.
- **Bota Systems SensONE / Medusa** — newer, low-noise, popular in
  research.

**Built into the arm (no separate purchase):**

- Universal Robots e-series — wrist-equivalent F/T from joint torques.
- Franka Robotics FR3 — torque sensors on every joint.
- KUKA LBR iiwa — same.
- Kinova Gen3 — same.

If your arm is one of those, skip the separate F/T sensor unless you
need extra precision.

**Best for what:**

- ATI — research-grade signal quality.
- Robotiq FT 300-S — UR users who want plug-and-play.
- OnRobot HEX — multi-vendor cobot users.

### Tactile sensors

Newer category. Most are still research-grade.

- **Contactile** — commercial fingertip force sensors.
- **GelSight** — optical tactile, very high resolution. Heavy use in
  research.
- **Tacterion** — flexible capacitive films, lower-resolution but easy to
  retrofit.
- **ReSkin (Meta)** — open-source magnetic-skin tactile design.

**Best for what:** research into delicate manipulation. If Layer 1 doesn't
explicitly say "must not crush this", skip the whole family.

### Proximity / presence sensors

Cheap, fast binary sensors. Used to detect "object is there" or "gripper
closed on something."

- **SICK** — photoelectric and capacitive.
- **Keyence (FS, FU fiber-optic; CapaciTec)** — premium, small.
- **Banner Engineering / Pepperl+Fuchs / IFM Efector** — broad industrial
  ranges.

**Best for what:** sensing that a part has arrived at a feeder, or
confirming the gripper closed on an object.

## Practical things to check before buying

| Check | Why it matters |
|-------|---------------|
| **Weight + cable weight** vs. arm's *remaining* payload | A heavy sensor wrist-mounted can silently break your payload budget. |
| **Field of view** | Eye-to-hand with too narrow a FOV won't see the whole table. |
| **Working range** (min to max depth) | RealSense D405 works at 7–50 cm; D435 at 30 cm – 3 m. Mismatch means no useful data. |
| **Resolution** | Drives how small an object the sensor can resolve. Over-spec wastes bandwidth. |
| **Frame rate** | Below 10 Hz feels laggy. ≥30 Hz needed for moving objects. |
| **Interface** (USB3 / GigE / Ethernet) | Some controllers can't host USB3. GigE often needs PoE or a switch. |
| **Power** | Bus-powered (USB3) is simpler. External supply is more reliable. |
| **ROS 2 driver** | A sensor without a driver is a software project. Always check first. |
| **Calibration tool** | Every camera needs hand-eye calibration. Budget the time. |
| **Mounting kit for your arm** | "We'll print one" turns into a week of CAD. |

## Output of this file — your sensor shortlist

Extend the comparison table from arm.md and gripper.md:

```
Sensor model:        ___
Family:              RGB / RGBD / F/T / tactile / proximity
Mount mode:          eye-in-hand / eye-to-hand / gripper / workspace
Working range:       ___ m
FOV / resolution:    ___
Frame rate:          ___ Hz
Interface:           ___
Weight (g):          ___
ROS 2 driver?:       yes / no
Price:               ___
```

Together with the arm and gripper shortlists, this is the **moving and
sensing hardware**. The next files cover the static and supporting
hardware: mount, power, control, network, cables, safety, operator
interface.

## Common mistakes

1. **Buying a sensor without checking wrist payload.** Zivid 2+ weighs
   ~2 kg — more than the entire payload of a myCobot 280.
2. **Over-spending on precision.** A Photoneo is brilliant; for "pick a
   coke can off a table," a $300 RealSense is fine.
3. **Picking without a ROS 2 driver.** Writing one is a real project.
4. **Forgetting hand-eye calibration.** Every camera-on-arm setup needs
   it. Even with `easy_handeye`, it's a day of work the first time.
5. **Two IR cameras pointed at the same object.** Their IR projectors
   blind each other. Switch one off or stagger captures.

## What's next

You have arm, gripper, and sensors. The next decision is what they all
**sit on** — the mounting structure.

→ Next: [mounting-and-mechanical-structure.md](mounting-and-mechanical-structure.md)
